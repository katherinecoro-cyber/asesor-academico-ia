import streamlit as st
import os

# Intentar importar la librería oficial de IA de Google
try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

st.set_page_config(
    page_title="Asesor Académico IA", 
    page_icon="🤖", 
    layout="centered"
)

st.title("🤖 Asesor Académico y Consultor de Proyectos")
st.write("Ingresa la propuesta de un nuevo diplomado o curso para recibir un análisis de mercado, nombres comerciales alternativos y estructura modular recomendada.")
st.markdown("---")

# Obtener la API Key desde los secretos de Streamlit
api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

# Formulario de entrada
nuevo_titulo = st.text_input("Escribe el nombre de la propuesta a evaluar:")
publico_objetivo = st.text_input("Público objetivo o área (Opcional, ej: Profesionales en Salud, Contadores, etc.):")

if st.button("Generar Asesoría Estratégica", type="primary") and nuevo_titulo:
    if not api_key:
        st.error("🔑 Falta configurar la `GEMINI_API_KEY` en los Secrets de Streamlit. Revisa la guía de configuración.")
    elif not HAS_GENAI:
        st.warning("⏳ La librería de IA se está instalando en el servidor. Espera un minuto y vuelve a intentar.")
    else:
        with st.spinner("🤖 El Consultor IA está analizando la propuesta académica y tendencias del mercado..."):
            try:
                # Inicializar el cliente de Gemini
                client = genai.Client(api_key=api_key)
                
                contexto_publico = f"dirigido a: {publico_objetivo}" if publico_objetivo else "para el mercado profesional general."
                
                prompt = f"""
                Actúa como un Vicerrector Académico Senior y Consultor de Marketing Universitario.
                
                EVALÚA LA SIGUIENTE PROPUESTA DE PROGRAMA:
                Título propuesto: "{nuevo_titulo}" {contexto_publico}
                
                Por favor, genera un informe estratégico en formato Markdown con las siguientes secciones bien estructuradas:
                
                ### 🎯 Diagnóstico Comercial y Pedagógico
                - Analiza la demanda actual en el mercado laboral para este tema.
                - Evalúa si el título suena atractivo o si es demasiado genérico/tradicional.
                
                ### 💡 3 Propuestas de Títulos Alternativos (Más Comerciales)
                - Da 3 opciones de nombres más modernos, incluyendo tendencias actuales (ej. herramientas digitales, automatización, IA, gestión estratégica o enfoque práctico).
                
                ### 📚 Módulos Sugeridos (Estructura del Programa)
                - Propón entre 4 y 5 módulos indispensables que debe tener este diplomado para ser competitivo y atractivo.
                
                ### 🚀 Factor Diferenciador
                - Una sugerencia breve de qué valor agregado o proyecto práctico final se le puede ofrecer al estudiante para destacar frente a la competencia.
                """
                
                # Generar contenido usando el modelo optimizado
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=prompt
                )
                
                st.success("✨ ¡Análisis generado con éxito!")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Ocurrió un detalle al conectar con el Asesor IA: {e}")
