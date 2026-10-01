# Taller virtual de empleabilidad – Nuevas Generaciones

App en Streamlit: registro → diapositivas (se cuentan solas) → evaluación (5 preguntas, 60 %, intentos sin límite) → constancia de participación en PDF.
Los intentos quedan en Google Sheets (conexión por Apps Script: `apps_script/Codigo.gs`).

- Parámetros: `config.py`
- Preguntas: `preguntas.json`
- Diapositivas: `slides/slide_XX.png`
- Publicación y mantenimiento: **[GUIA_DESPLIEGUE.md](GUIA_DESPLIEGUE.md)**

Para correrla en tu computador: `pip install -r requirements.txt` y luego `streamlit run app.py`.
Copia `.streamlit/secrets.toml.example` como `.streamlit/secrets.toml` y llénalo con tus datos.
