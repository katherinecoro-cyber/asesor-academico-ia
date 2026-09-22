import os
import re

import streamlit as st

try:
    from google import genai
    from google.genai import types
except ImportError:  # La app sigue funcionando en modo sin conexión.
    genai = None
    types = None

st.set_page_config(
    page_title="Asesor Académico IA",
    page_icon="🎓",
    layout="centered",
)

# Se prueban en orden; si uno no está disponible se pasa al siguiente.
MODELOS_GEMINI = ["gemini-3.6-flash", "gemini-flash-latest", "gemini-2.5-flash"]

NIVELES = {
    "Diplomado": (
        "Programa corto de actualización o especialización práctica (normalmente 100-250 horas). "
        "El proyecto suele ser un trabajo integrador o aplicado a un caso real de la organización del participante. "
        "Los títulos deben ser concretos, orientados a competencias y a resultados medibles."
    ),
    "Maestría": (
        "Programa de posgrado de 1-2 años. Puede ser profesionalizante (proyecto aplicado, plan de mejora, "
        "plan de negocio, consultoría) o de investigación (tesis con metodología formal). "
        "Los títulos deben delimitar variables, contexto, población y periodo cuando aplique."
    ),
    "Doctorado": (
        "Máximo grado académico. El proyecto es una tesis doctoral que exige un aporte original al conocimiento: "
        "nuevo modelo, teoría, instrumento o evidencia empírica inédita. "
        "Los títulos deben reflejar el vacío de investigación, el enfoque teórico-metodológico y la contribución."
    ),
}

TIPOS_PROYECTO = {
    "Propuesta de nuevo programa académico": (
        "El usuario diseña la OFERTA académica de una escuela de negocios: quiere nombres de programas "
        "(diplomados, maestrías o doctorados) atractivos, pertinentes y vendibles, con justificación de mercado."
    ),
    "Trabajo de grado / tesis": (
        "El usuario necesita títulos para un PROYECTO DE GRADO o TESIS dentro de un programa: "
        "títulos académicamente sólidos, investigables y factibles, con pregunta y objetivo general."
    ),
}
ES_PROGRAMA = "Propuesta de nuevo programa académico"

SYSTEM_PROMPT = """
Eres "Asesor Académico IA", un Vicerrector Académico Senior, director de posgrados y consultor de
marketing universitario con amplia experiencia en escuelas de negocios de Latinoamérica.

Tu misión es ayudar al usuario a idear, evaluar y perfeccionar TÍTULOS DE PROYECTOS para
diplomados, maestrías y doctorados. Responde siempre en español, en Markdown, con tono profesional
y cercano.

Contexto actual del usuario:
- Tipo de proyecto: {tipo}. {tipo_desc}
- Nivel académico: {nivel}. {nivel_desc}
- Área o disciplina: {area}
- Público objetivo / contexto: {publico}
- Modalidad: {modalidad}

Criterios que SIEMPRE aplicas al proponer o evaluar un título:
1. Claridad y precisión (qué, en quién/dónde, para qué). Evita títulos genéricos.
2. Pertinencia y tendencias actuales (IA, transformación digital, sostenibilidad/ESG, analítica de datos,
   liderazgo, innovación, normativa vigente) solo cuando aporten valor real.
3. Coherencia con el nivel: un diplomado es aplicado; una maestría delimita y aplica/investiga;
   un doctorado aporta conocimiento original.
4. Factibilidad (acceso a datos, tiempo, recursos) y, si es una oferta académica, atractivo comercial.
5. Extensión razonable: idealmente 12-20 palabras para tesis, 4-10 palabras para nombres de programas.

Cuando propongas títulos, presenta cada uno con:
- **Título**
- Enfoque o línea (una frase)
- Por qué funciona / qué lo diferencia
- Para tesis: pregunta de investigación y objetivo general sugeridos. Para programas: perfil de egreso breve.

Cuando evalúes un título: da una calificación de 1 a 10, fortalezas, debilidades, y al menos 3 versiones mejoradas.

Si falta información clave, haz como máximo 2 preguntas breves al final, pero entrega igualmente una
propuesta útil. No inventes estadísticas ni cifras exactas del mercado; si mencionas demanda, hazlo de forma
cualitativa y sugiere cómo validarla.
"""

# ---------------------------------------------------------------------------
# Plantillas del modo sin conexión (se usan si Gemini no está disponible)
# ---------------------------------------------------------------------------
PLANTILLAS_PROGRAMA = {
    "Diplomado": [
        ("Diplomado en {Tema} Aplicado a {Area}", "Enfoque práctico con casos reales del sector."),
        ("Diplomado en {Tema}: Herramientas Digitales e IA", "Actualización con herramientas digitales y automatización."),
        ("Diplomado en Gestión Estratégica de {Tema}", "Orientado a mandos medios que toman decisiones."),
        ("Diplomado en Liderazgo e Innovación en {Tema}", "Combina habilidades directivas con innovación."),
        ("Diplomado en Analítica de Datos para {Tema}", "Decisiones basadas en datos e indicadores."),
        ("Diplomado Ejecutivo en {Tema} y Transformación Digital", "Formato ejecutivo para profesionales con experiencia."),
        ("Diplomado en {Tema} Sostenible y Criterios ESG", "Integra sostenibilidad y responsabilidad corporativa."),
        ("Diplomado en {Tema} Ágil: Métodos y Proyectos", "Metodologías ágiles aplicadas a proyectos concretos."),
        ("Diplomado en Normativa y Buenas Prácticas de {Tema}", "Cumplimiento normativo y estándares vigentes."),
        ("Diplomado en {Tema} para la Toma de Decisiones", "Enfocado en resultados de negocio medibles."),
    ],
    "Maestría": [
        ("Maestría en {Tema} y Transformación Digital", "Formación integral con foco en tecnología."),
        ("Maestría en Dirección Estratégica de {Tema}", "Prepara para cargos directivos."),
        ("Maestría en {Tema} e Inteligencia de Negocios", "Une gestión con analítica avanzada."),
        ("Maestría en {Tema} con Mención en Innovación", "Diferenciación mediante innovación y emprendimiento."),
        ("Maestría en {Tema} Sostenible", "Alineada con ESG y Objetivos de Desarrollo Sostenible."),
        ("Maestría Ejecutiva en {Tema} (Executive)", "Para profesionales con trayectoria que buscan ascender."),
        ("Maestría en Gestión de {Tema} Basada en Datos", "Analítica, indicadores y toma de decisiones."),
        ("Maestría en {Tema} y Liderazgo Organizacional", "Desarrollo de equipos y cambio organizacional."),
        ("Maestría en {Tema} Internacional", "Perspectiva global y negocios internacionales."),
        ("Maestría en {Tema} e Inteligencia Artificial Aplicada", "Uso responsable de IA en la gestión."),
    ],
    "Doctorado": [
        ("Doctorado en {Tema} y Gestión de Organizaciones", "Investigación de alto nivel sobre organizaciones."),
        ("Doctorado en Ciencias de la Gestión con Línea en {Tema}", "Formación de investigadores en gestión."),
        ("Doctorado en {Tema}, Innovación y Sostenibilidad", "Líneas de investigación emergentes."),
        ("Doctorado en {Tema} y Transformación Digital", "Estudio del impacto tecnológico en organizaciones."),
        ("Doctorado en Administración con Énfasis en {Tema}", "Clásico y reconocido, con énfasis diferenciador."),
        ("Doctorado en Estudios Avanzados de {Tema}", "Generación de teoría y modelos originales."),
        ("Doctorado en {Tema} y Políticas Públicas", "Vinculación con Estado y sociedad."),
        ("Doctorado en {Tema} y Ciencia de Datos", "Métodos cuantitativos avanzados."),
        ("Doctorado en {Tema} y Desarrollo Sostenible", "Aporte a los desafíos regionales."),
        ("Doctorado Internacional en {Tema}", "Redes y cotutelas internacionales."),
    ],
}

PLANTILLAS_TESIS = {
    "Diplomado": [
        "Propuesta de mejora de {tema} en {publico}",
        "Plan de implementación de {tema} para {publico}",
        "Diagnóstico y plan de acción de {tema} en {publico}",
        "Diseño de un modelo práctico de {tema} para {publico}",
        "Aplicación de herramientas digitales para optimizar {tema} en {publico}",
        "Propuesta de indicadores de gestión de {tema} para {publico}",
        "Rediseño de procesos de {tema} en {publico}",
        "Estrategia de {tema} basada en datos para {publico}",
        "Guía metodológica de {tema} aplicada a {publico}",
        "Proyecto integrador: {tema} como palanca de competitividad en {publico}",
    ],
    "Maestría": [
        "Influencia de {tema} en el desempeño organizacional de {publico}, {periodo}",
        "{Tema} y su relación con la productividad en {publico}, {periodo}",
        "Modelo de gestión de {tema} para mejorar la competitividad de {publico}",
        "Factores críticos de éxito en {tema}: estudio en {publico}, {periodo}",
        "Impacto de la inteligencia artificial en {tema}: caso {publico}",
        "Propuesta de un plan estratégico de {tema} para {publico}, {periodo}",
        "Percepción de los colaboradores sobre {tema} en {publico}, {periodo}",
        "Efecto de {tema} en la satisfacción del cliente de {publico}, {periodo}",
        "{Tema} y sostenibilidad: análisis en {publico}, {periodo}",
        "Evaluación de la madurez de {tema} en {publico} y propuesta de mejora",
    ],
    "Doctorado": [
        "Hacia un modelo teórico de {tema} en {publico}: aportes desde la evidencia latinoamericana",
        "{Tema} como capacidad dinámica: construcción y validación de un modelo en {publico}",
        "Determinantes de {tema} en {publico}: un enfoque de ecuaciones estructurales",
        "Diseño y validación de un instrumento para medir {tema} en {publico}",
        "{Tema} e inteligencia artificial: un marco conceptual para {publico}",
        "Mecanismos explicativos de {tema} en {publico}: un estudio de métodos mixtos",
        "{Tema} y sostenibilidad organizacional: propuesta de un modelo integrador para {publico}",
        "Repensar {tema} en {publico}: una aproximación desde la teoría de recursos y capacidades",
        "Efectos de largo plazo de {tema} en {publico}: evidencia longitudinal, {periodo}",
        "Modelo predictivo de {tema} en {publico} basado en analítica avanzada",
    ],
}

PALABRAS_GENERICAS = {"aspectos", "generales", "general", "introducción", "estudio", "análisis", "algunos", "diversos", "temas", "conceptos"}
PALABRAS_TENDENCIA = {"ia", "inteligencia", "digital", "datos", "sostenible", "sostenibilidad", "esg", "innovación", "ágil", "analítica", "automatización", "liderazgo", "estratégica", "estratégico"}


def _capitalizar(texto):
    return texto[:1].upper() + texto[1:] if texto else texto


def _contexto(perfil, tema=None):
    tema = (tema or perfil["area"] or "gestión empresarial").strip().rstrip(".")
    return {
        "tema": tema if tema[:2].isupper() else tema[:1].lower() + tema[1:],
        "Tema": _capitalizar(tema),
        "Area": _capitalizar(perfil["area"].strip()) if perfil["area"].strip() else "las Organizaciones",
        "publico": perfil["publico"].strip() or "empresas de la región",
        "periodo": "2025-2026",
    }


def generar_sin_conexion(perfil, tema, cantidad):
    ctx = _contexto(perfil, tema)
    nivel = perfil["nivel"]
    lineas = [f"### 💡 {cantidad} propuestas de títulos ({nivel})\n"]
    if perfil["tipo"] == ES_PROGRAMA:
        for i, (plantilla, enfoque) in enumerate(PLANTILLAS_PROGRAMA[nivel][:cantidad], 1):
            titulo = plantilla.format(**ctx)
            lineas.append(
                f"**{i}. {titulo}**\n"
                f"- *Enfoque:* {enfoque}\n"
                f"- *Perfil de egreso:* profesional capaz de liderar iniciativas de {ctx['tema']} "
                f"en {ctx['publico']} ({perfil['modalidad'].lower()}).\n"
            )
    else:
        for i, plantilla in enumerate(PLANTILLAS_TESIS[nivel][:cantidad], 1):
            titulo = _capitalizar(plantilla.format(**ctx))
            lineas.append(
                f"**{i}. {titulo}**\n"
                f"- *Pregunta:* ¿De qué manera {ctx['tema']} contribuye a mejorar los resultados de {ctx['publico']}?\n"
                f"- *Objetivo general:* Analizar/proponer {ctx['tema']} para {ctx['publico']}.\n"
            )
    lineas.append(
        "**Recomendación:** empieza por la opción 1 y ajústala con datos concretos "
        "(organización, país, periodo) para hacerla más específica."
    )
    return "\n".join(lineas)


def evaluar_sin_conexion(perfil, titulo):
    palabras = re.findall(r"\w+", titulo.lower())
    n = len(palabras)
    es_programa = perfil["tipo"] == ES_PROGRAMA
    minimo, maximo = (4, 10) if es_programa else (12, 20)
    puntaje = 6
    fortalezas, debilidades = [], []

    if minimo <= n <= maximo:
        puntaje += 2
        fortalezas.append(f"Extensión adecuada ({n} palabras).")
    elif n < minimo:
        puntaje -= 1
        debilidades.append(f"Es corto ({n} palabras); conviene precisar contexto o enfoque (ideal {minimo}-{maximo}).")
    else:
        puntaje -= 1
        debilidades.append(f"Es largo ({n} palabras); intenta resumirlo (ideal {minimo}-{maximo}).")

    genericas = PALABRAS_GENERICAS.intersection(palabras)
    if genericas:
        puntaje -= 1
        debilidades.append("Usa palabras genéricas: " + ", ".join(sorted(genericas)) + ".")
    else:
        fortalezas.append("Evita palabras genéricas.")

    if PALABRAS_TENDENCIA.intersection(palabras):
        puntaje += 1
        fortalezas.append("Incorpora un enfoque actual o diferenciador.")
    else:
        debilidades.append("Podría incluir un enfoque actual (digital, datos, IA, sostenibilidad, innovación).")

    if not es_programa:
        if re.search(r"\b(19|20)\d{2}\b", titulo):
            puntaje += 1
            fortalezas.append("Delimita el periodo de estudio.")
        else:
            debilidades.append("No delimita periodo (ej. 2025-2026).")
        if " en " not in f" {titulo.lower()} ":
            debilidades.append("No delimita el lugar, organización o población.")

    puntaje = max(1, min(10, puntaje))
    tema = re.sub(r"^(diplomado|maestr[ií]a|doctorado)( ejecutiva?)? (en|de) ", "", titulo.strip(), flags=re.I)
    mejoras = generar_sin_conexion(perfil, tema, 3).split("\n", 1)[1].rsplit("**Recomendación", 1)[0]

    return (
        f"### 🔍 Evaluación de: *{titulo}*\n\n"
        f"**Calificación estimada: {puntaje}/10**\n\n"
        "**Fortalezas**\n" + "\n".join(f"- {f}" for f in fortalezas or ["Tema identificable."]) + "\n\n"
        "**Aspectos a mejorar**\n" + "\n".join(f"- {d}" for d in debilidades or ["Sin observaciones importantes."]) + "\n\n"
        "**Versiones mejoradas**\n" + mejoras
    )


def responder_sin_conexion(perfil, peticion):
    if peticion["accion"] == "evaluar":
        return evaluar_sin_conexion(perfil, peticion["titulo"])
    if peticion["accion"] == "generar":
        return generar_sin_conexion(perfil, peticion["tema"], peticion["cantidad"])
    return generar_sin_conexion(perfil, peticion["texto"], 5)


# ---------------------------------------------------------------------------
# Gemini (opcional)
# ---------------------------------------------------------------------------
def obtener_secreto(nombre):
    try:
        valor = st.secrets.get(nombre)
    except Exception:
        valor = None
    return valor or os.getenv(nombre)


def construir_system_prompt(perfil):
    return SYSTEM_PROMPT.format(
        tipo=perfil["tipo"],
        tipo_desc=TIPOS_PROYECTO[perfil["tipo"]],
        nivel=perfil["nivel"],
        nivel_desc=NIVELES[perfil["nivel"]],
        area=perfil["area"] or "no especificada",
        publico=perfil["publico"] or "no especificado",
        modalidad=perfil["modalidad"],
    )


def responder_con_gemini(client, perfil, mensajes):
    """Prueba cada modelo en orden y devuelve la respuesta en streaming.

    Si un modelo falla antes de enviar texto, se intenta con el siguiente.
    Si todos fallan, se lanza la última excepción.
    """
    contenido = [
        types.Content(
            role="user" if m["role"] == "user" else "model",
            parts=[types.Part(text=m["content"])],
        )
        for m in mensajes
    ]
    config = types.GenerateContentConfig(
        system_instruction=construir_system_prompt(perfil),
        temperature=0.8,
    )
    modelo_elegido = obtener_secreto("GEMINI_MODEL")
    modelos = [modelo_elegido] + MODELOS_GEMINI if modelo_elegido else MODELOS_GEMINI
    ultimo_error = None
    for modelo in modelos:
        envio_texto = False
        try:
            for fragmento in client.models.generate_content_stream(
                model=modelo, contents=contenido, config=config
            ):
                if fragmento.text:
                    envio_texto = True
                    yield fragmento.text
            if envio_texto:
                return
        except Exception as e:
            if envio_texto:
                return
            ultimo_error = e
    raise ultimo_error or RuntimeError("Gemini no devolvió respuesta.")


# ---------------------------------------------------------------------------
# Barra lateral: perfil del proyecto
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Tu proyecto")
    perfil = {
        "tipo": st.radio("¿Qué necesitas?", list(TIPOS_PROYECTO)),
        "nivel": st.selectbox("Nivel académico", list(NIVELES)),
        "area": st.text_input("Área o disciplina", placeholder="Ej: Finanzas, Marketing, Salud, Educación"),
        "publico": st.text_input(
            "Público objetivo o contexto",
            placeholder="Ej: Gerentes de PYMES en Perú, docentes universitarios",
        ),
        "modalidad": st.selectbox("Modalidad", ["Virtual", "Presencial", "Híbrida", "No aplica"]),
    }
    st.markdown("---")
    if st.button("🗑️ Nueva conversación", use_container_width=True):
        st.session_state.mensajes = []
        st.rerun()

st.title("🎓 Asesor de Títulos para Diplomados, Maestrías y Doctorados")
st.write(
    "Configura tu proyecto en la barra lateral, usa una acción rápida o conversa libremente "
    "con el asesor para idear, evaluar y pulir tus títulos."
)

api_key = obtener_secreto("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if (api_key and genai) else None
if client is None:
    st.info("ℹ️ Modo sin conexión: las propuestas se generan con plantillas del asesor (sin IA).")

if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

# ---------------------------------------------------------------------------
# Acciones rápidas
# ---------------------------------------------------------------------------
tab_ideas, tab_evaluar = st.tabs(["💡 Generar títulos", "🔍 Evaluar mi título"])
peticion = None

with tab_ideas:
    tema = st.text_input("Tema o idea general (opcional)", placeholder="Ej: inteligencia artificial en recursos humanos")
    cantidad = st.slider("¿Cuántas propuestas?", 3, 10, 5)
    if st.button("Generar propuestas", type="primary"):
        peticion = {
            "accion": "generar",
            "tema": tema,
            "cantidad": cantidad,
            "texto": (
                f"Propón {cantidad} títulos para un {perfil['nivel'].lower()} "
                f"({perfil['tipo'].lower()})"
                + (f" sobre el tema: {tema}." if tema else " en mi área.")
                + " Ordénalos del más recomendado al menos recomendado y cierra con tu recomendación final."
            ),
        }

with tab_evaluar:
    titulo = st.text_input("Escribe el título que quieres evaluar")
    if st.button("Evaluar título", type="primary") and titulo:
        peticion = {
            "accion": "evaluar",
            "titulo": titulo,
            "texto": f'Evalúa este título para un {perfil["nivel"].lower()}: "{titulo}"',
        }

st.markdown("---")

# ---------------------------------------------------------------------------
# Conversación
# ---------------------------------------------------------------------------
for m in st.session_state.mensajes:
    with st.chat_message(m["role"], avatar="🧑‍🎓" if m["role"] == "user" else "🎓"):
        st.markdown(m["content"])

entrada = st.chat_input("Pregunta, pide ajustes o comparte tu idea…")
if entrada:
    peticion = {"accion": "chat", "texto": entrada}

if peticion:
    st.session_state.mensajes.append({"role": "user", "content": peticion["texto"]})
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(peticion["texto"])

    with st.chat_message("assistant", avatar="🎓"):
        respuesta = None
        if client is not None:
            try:
                respuesta = st.write_stream(responder_con_gemini(client, perfil, st.session_state.mensajes))
            except Exception:
                st.caption("⚠️ La IA no respondió en este momento; te muestro una propuesta del modo sin conexión.")
        if not respuesta:
            respuesta = responder_sin_conexion(perfil, peticion)
            st.markdown(respuesta)
        st.session_state.mensajes.append({"role": "assistant", "content": respuesta})
