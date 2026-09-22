import os

import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="Asesor Académico IA",
    page_icon="🎓",
    layout="centered",
)

MODELO_POR_DEFECTO = "gemini-2.5-flash"

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


def obtener_api_key():
    try:
        clave = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        clave = None
    return clave or os.getenv("GEMINI_API_KEY")


def obtener_modelo():
    try:
        modelo = st.secrets.get("GEMINI_MODEL")
    except Exception:
        modelo = None
    return modelo or os.getenv("GEMINI_MODEL", MODELO_POR_DEFECTO)


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


def responder(client, perfil, mensajes):
    """Envía el historial completo al modelo y devuelve la respuesta en streaming."""
    contenido = [
        types.Content(
            role="user" if m["role"] == "user" else "model",
            parts=[types.Part(text=m["content"])],
        )
        for m in mensajes
    ]
    stream = client.models.generate_content_stream(
        model=obtener_modelo(),
        contents=contenido,
        config=types.GenerateContentConfig(
            system_instruction=construir_system_prompt(perfil),
            temperature=0.8,
        ),
    )
    for fragmento in stream:
        if fragmento.text:
            yield fragmento.text


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

api_key = obtener_api_key()
if not api_key:
    st.error("🔑 Falta configurar la `GEMINI_API_KEY` en los Secrets de Streamlit o como variable de entorno.")
    st.stop()

client = genai.Client(api_key=api_key)

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
        peticion = (
            f"Propón {cantidad} títulos para un {perfil['nivel'].lower()} "
            f"({perfil['tipo'].lower()})"
            + (f" sobre el tema: {tema}." if tema else " en mi área.")
            + " Ordénalos del más recomendado al menos recomendado y cierra con tu recomendación final."
        )

with tab_evaluar:
    titulo = st.text_input("Escribe el título que quieres evaluar")
    if st.button("Evaluar título", type="primary") and titulo:
        peticion = f'Evalúa este título para un {perfil["nivel"].lower()}: "{titulo}"'

st.markdown("---")

# ---------------------------------------------------------------------------
# Conversación
# ---------------------------------------------------------------------------
for m in st.session_state.mensajes:
    with st.chat_message(m["role"], avatar="🧑‍🎓" if m["role"] == "user" else "🎓"):
        st.markdown(m["content"])

entrada = st.chat_input("Pregunta, pide ajustes o comparte tu idea…")
peticion = entrada or peticion

if peticion:
    st.session_state.mensajes.append({"role": "user", "content": peticion})
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.markdown(peticion)

    with st.chat_message("assistant", avatar="🎓"):
        try:
            respuesta = st.write_stream(responder(client, perfil, st.session_state.mensajes))
            st.session_state.mensajes.append({"role": "assistant", "content": respuesta})
        except Exception as e:
            st.session_state.mensajes.pop()
            st.error(f"Ocurrió un problema al conectar con el Asesor IA: {e}")
