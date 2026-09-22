# Asesor Académico IA 🎓

Agente conversacional (Streamlit + Gemini) que asesora sobre **títulos de proyectos** para
**diplomados, maestrías y doctorados**.

## Qué hace

- **Dos tipos de proyecto**: propuesta de un nuevo programa académico (oferta de la escuela) o
  trabajo de grado / tesis.
- **Adaptado al nivel**: diplomado (aplicado), maestría (delimitado, profesionalizante o de
  investigación) y doctorado (aporte original).
- **Generar títulos**: propone de 3 a 10 títulos ordenados, con enfoque, justificación y
  pregunta/objetivo (tesis) o perfil de egreso (programas).
- **Evaluar mi título**: calificación de 1 a 10, fortalezas, debilidades y versiones mejoradas.
- **Chat con memoria**: sigue conversando para ajustar, combinar o comparar títulos.

## Ejecutar

```bash
pip install -r requirements.txt
export GEMINI_API_KEY="tu-clave"
streamlit run app.py
```

En Streamlit Cloud, agrega `GEMINI_API_KEY` en *Secrets*. Opcionalmente define `GEMINI_MODEL`
para forzar un modelo concreto.

## Sin errores: respaldo automático

- La app prueba varios modelos de Gemini en orden (`gemini-3.6-flash`, `gemini-flash-latest`,
  `gemini-2.5-flash`) y usa el primero que responda.
- Si no hay clave o Gemini no responde, entra en **modo sin conexión**: genera y evalúa títulos
  con plantillas propias del asesor, sin mostrar errores.
