"""
Capacitación virtual con evaluación y constancia de participación.
Flujo: (clave) → registro → contenido → evaluación → constancia.
Los parámetros se cambian en config.py y las preguntas en preguntas.json.
"""

import json
import re
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st

import config
from utils import sheets
from utils.pdf_certificado import generar_certificado

RAIZ = Path(__file__).resolve().parent
st.set_page_config(page_title=config.NOMBRE_CURSO, page_icon="🎓", layout="centered")


# ------------------------------------------------------------------
# Estilo
# ------------------------------------------------------------------
def aplicar_estilo():
    c = config.COLOR_PRINCIPAL
    suave = config.COLOR_SUAVE
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');
        html, body, .stApp, .stApp *:not([data-testid="stIconMaterial"]):not(.material-symbols-rounded) {{
            font-family: 'Montserrat', sans-serif;
        }}
        .stApp {{ background: #FFFFFF; }}
        .block-container {{ padding-top: 2rem; max-width: 900px; }}
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background: #FFFFFF; border-radius: 14px !important;
            border-color: #D6E6F5 !important;
            box-shadow: 0 2px 12px rgba(0,112,192,.06);
        }}
        .encabezado {{
            background: {c}; color: #fff; border-radius: 14px;
            padding: 1.1rem 1.4rem; margin-bottom: 1rem;
        }}
        .encabezado .etiqueta {{ font-size: .72rem; letter-spacing: .12em; opacity: .85; text-transform: uppercase; }}
        .encabezado h1 {{ color: #fff; font-size: 1.35rem; margin: .2rem 0 0; padding: 0; font-weight: 700; }}
        .pasos {{ display: flex; gap: .4rem; margin: 0 0 1.1rem; flex-wrap: wrap; }}
        .paso {{ flex: 1; min-width: 110px; text-align: center; font-size: .75rem; font-weight: 600;
                 padding: .45rem .3rem; border-radius: 999px; background: #F1F4F8; color: #7A8699; }}
        .paso.activo {{ background: {c}; color: #fff; }}
        .paso.hecho {{ background: {suave}; color: {c}; }}
        .puntaje {{ font-size: 2.6rem; font-weight: 700; color: {c}; line-height: 1.1; }}
        .stProgress > div > div > div > div {{ background-color: {c}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


PASOS = ["Registro", "Contenido", "Evaluación", "Constancia"]
PANTALLA_A_PASO = {"registro": 0, "contenido": 1, "examen": 2, "resultado": 2, "certificado": 3}


def encabezado():
    st.markdown(
        f"""<div class="encabezado"><div class="etiqueta">{config.ORGANIZACION} · Capacitación virtual</div>
        <h1>{config.NOMBRE_CURSO}</h1></div>""",
        unsafe_allow_html=True,
    )
    actual = PANTALLA_A_PASO.get(st.session_state.pantalla)
    if actual is None:
        return
    html = "".join(
        f'<div class="paso {"activo" if i == actual else "hecho" if i < actual else ""}">{i + 1}. {p}</div>'
        for i, p in enumerate(PASOS)
    )
    st.markdown(f'<div class="pasos">{html}</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------
# Datos
# ------------------------------------------------------------------
@st.cache_data
def cargar_preguntas():
    with open(RAIZ / config.ARCHIVO_PREGUNTAS, encoding="utf-8") as f:
        return json.load(f)


EXTENSIONES = {".png", ".jpg", ".jpeg", ".webp"}


def _orden_natural(ruta: Path):
    """Ordena 'slide_2' antes que 'slide_10' (y 'Diapositiva2' antes que 'Diapositiva10')."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", ruta.name)]


@st.cache_data
def cargar_diapositivas():
    """Toma todas las imágenes de la carpeta, sin importar mayúsculas en la extensión."""
    carpeta = RAIZ / config.CARPETA_DIAPOSITIVAS
    imagenes = [p for p in carpeta.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONES]
    return [str(p) for p in sorted(imagenes, key=_orden_natural)]


def sin_limite() -> bool:
    return not config.MAX_INTENTOS or config.MAX_INTENTOS <= 0


def ahora():
    return datetime.now(ZoneInfo(config.ZONA_HORARIA))


def iniciar_estado():
    valores = {
        "pantalla": "clave" if config.USAR_CLAVE_ACCESO else "registro",
        "nombre": "",
        "cedula": "",
        "slide": 0,
        "vio_todo": False,
        "intentos": 0,
        "puntaje": None,
        "aprobado": False,
        "certificado": "",
        "fecha_cert": None,
        "sheets_ok": True,
    }
    for k, v in valores.items():
        st.session_state.setdefault(k, v)


def ir(pantalla):
    st.session_state.pantalla = pantalla
    st.rerun()


# ------------------------------------------------------------------
# Pantallas
# ------------------------------------------------------------------
def pantalla_clave():
    with st.container(border=True):
        st.subheader("Acceso")
        with st.form("form_clave"):
            clave = st.text_input("Clave de acceso", type="password")
            if st.form_submit_button("Ingresar", type="primary"):
                try:
                    clave_real = st.secrets.get("clave_acceso", "")
                except Exception:
                    clave_real = ""
                if clave and clave == clave_real:
                    ir("registro")
                else:
                    st.error("La clave no es correcta.")


def pantalla_registro():
    with st.container(border=True):
        st.subheader("Registro")
        st.write("Ingresa tus datos tal como quieres que aparezcan en la constancia.")
        with st.form("form_registro"):
            nombre = st.text_input("Nombre completo *", max_chars=80)
            cedula = st.text_input("Número de cédula *", max_chars=10, help="Solo números, sin puntos ni espacios.")
            acepta = st.checkbox(config.TEXTO_AUTORIZACION)
            enviar = st.form_submit_button("Comenzar la capacitación", type="primary")

    if not enviar:
        return

    nombre = re.sub(r"\s+", " ", nombre).strip()
    cedula = cedula.strip()
    errores = []
    if len(nombre.split()) < 2 or not re.fullmatch(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' .-]+", nombre):
        errores.append("Escribe tu nombre y apellido, solo con letras.")
    if not re.fullmatch(r"\d{5,10}", cedula):
        errores.append("La cédula debe tener solo números (entre 5 y 10 dígitos).")
    if not acepta:
        errores.append("Debes aceptar la autorización de tratamiento de datos para continuar.")
    if errores:
        for e in errores:
            st.error(e)
        return

    st.session_state.nombre = nombre
    st.session_state.cedula = cedula

    # Historial en Google Sheets: intentos previos y constancia ya emitida
    try:
        with st.spinner("Verificando tu registro..."):
            hist = sheets.historial_cedula(cedula)
        st.session_state.sheets_ok = True
    except Exception:
        hist = {"intentos": 0, "aprobado": None}
        st.session_state.sheets_ok = False

    if hist["aprobado"]:
        r = hist["aprobado"]
        st.session_state.nombre = r["nombre"]
        st.session_state.certificado = r["certificado"]
        st.session_state.fecha_cert = _leer_fecha(r["fecha"])
        st.session_state.puntaje = r["puntaje"]
        st.session_state.aprobado = True
        st.session_state.ya_aprobado = True
        ir("certificado")

    st.session_state.intentos = hist["intentos"]
    if not sin_limite() and hist["intentos"] >= config.MAX_INTENTOS:
        st.session_state.intentos = config.MAX_INTENTOS
        ir("resultado")
    ir("contenido")


def _leer_fecha(valor) -> date:
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(valor), fmt).date()
        except ValueError:
            continue
    return ahora().date()


def pantalla_contenido():
    slides = cargar_diapositivas()
    if not slides:
        st.error(f"No se encontraron imágenes en la carpeta '{config.CARPETA_DIAPOSITIVAS}'.")
        return
    total = len(slides)
    i = min(st.session_state.slide, total - 1)
    if i == total - 1:
        st.session_state.vio_todo = True

    with st.container(border=True):
        st.progress((i + 1) / total, text=f"Diapositiva {i + 1} de {total}")
        st.image(slides[i], width="stretch")
        c1, c2, c3 = st.columns([1, 1, 1])
        if c1.button("← Anterior", disabled=i == 0, width="stretch"):
            st.session_state.slide = i - 1
            st.rerun()
        if c3.button("Siguiente →", disabled=i == total - 1, type="primary", width="stretch"):
            st.session_state.slide = i + 1
            st.rerun()

    if st.session_state.vio_todo:
        st.success("Terminaste el contenido. Cuando estés listo, presenta la evaluación.")
        if st.button("Ir a la evaluación", type="primary", width="stretch"):
            ir("examen")
    else:
        st.caption("Recorre todas las diapositivas para habilitar la evaluación.")


def pantalla_examen():
    if not st.session_state.vio_todo:
        ir("contenido")
    preguntas = cargar_preguntas()
    intento = st.session_state.intentos + 1

    with st.container(border=True):
        st.subheader("Evaluación final")
        minimo = -(-config.PUNTAJE_MINIMO * len(preguntas) // 100)  # preguntas buenas necesarias
        texto = (f"Son {len(preguntas)} preguntas cortas. Elige una respuesta en cada una. "
                 f"Necesitas **{minimo} buenas** para recibir tu constancia.")
        if not sin_limite():
            texto += f" Intento **{intento} de {config.MAX_INTENTOS}**."
        st.write(texto)
        with st.form(f"form_examen_{intento}"):
            respuestas = []
            for n, p in enumerate(preguntas, start=1):
                r = st.radio(f"**{n}. {p['pregunta']}**", p["opciones"], index=None, key=f"p{n}_{intento}")
                respuestas.append(r)
            enviar = st.form_submit_button("Enviar respuestas", type="primary")

    if not enviar:
        return
    if any(r is None for r in respuestas):
        st.error("Responde todas las preguntas antes de enviar.")
        return

    correctas = sum(r == p["opciones"][p["correcta"] - 1] for r, p in zip(respuestas, preguntas))
    puntaje = round(correctas / len(preguntas) * 100, 1)
    aprobado = puntaje >= config.PUNTAJE_MINIMO
    momento = ahora()

    try:
        numero = sheets.registrar_intento(
            momento.strftime("%Y-%m-%d %H:%M:%S"),
            st.session_state.nombre,
            st.session_state.cedula,
            puntaje,
            aprobado,
        )
    except Exception:
        st.session_state.sheets_ok = False
        numero = f"{config.PREFIJO_CERTIFICADO}-{momento:%Y%m%d%H%M%S}-{st.session_state.cedula[-4:]}" if aprobado else ""

    st.session_state.intentos = intento
    st.session_state.puntaje = puntaje
    st.session_state.aprobado = aprobado
    st.session_state.correctas = correctas
    if aprobado:
        st.session_state.certificado = numero
        st.session_state.fecha_cert = momento.date()
        ir("certificado")
    ir("resultado")


def pantalla_resultado():
    restantes = 1 if sin_limite() else config.MAX_INTENTOS - st.session_state.intentos
    with st.container(border=True):
        if st.session_state.puntaje is not None:
            st.markdown(f'<div class="puntaje">{st.session_state.puntaje:g} %</div>', unsafe_allow_html=True)
            st.write("¡Casi lo logras! Esta vez no alcanzaste el puntaje mínimo.")
        if restantes > 0:
            if sin_limite():
                st.info("Puedes repasar las diapositivas o intentarlo de nuevo cuando quieras.")
            else:
                st.info(f"Te {'queda' if restantes == 1 else 'quedan'} {restantes} "
                        f"{'intento' if restantes == 1 else 'intentos'}. Repasa el contenido y vuelve a intentarlo.")
            c1, c2 = st.columns(2)
            if c1.button("Repasar el contenido", width="stretch"):
                st.session_state.slide = 0
                ir("contenido")
            if c2.button("Intentar de nuevo", type="primary", width="stretch"):
                ir("examen")
        else:
            st.error("Usaste todos los intentos permitidos para esta cédula. "
                     "Comunícate con el equipo organizador si necesitas ayuda.")


def pantalla_certificado():
    with st.container(border=True):
        if st.session_state.get("ya_aprobado"):
            st.success(f"{st.session_state.nombre}, ya habías completado esta capacitación. Puedes descargar tu constancia de nuevo.")
        else:
            st.balloons()
            st.markdown(f'<div class="puntaje">{st.session_state.puntaje:g} %</div>', unsafe_allow_html=True)
            st.success(f"¡Felicitaciones, {st.session_state.nombre.split()[0]}! Aprobaste la evaluación.")
        pdf = generar_certificado(
            st.session_state.nombre,
            st.session_state.cedula,
            st.session_state.certificado,
            st.session_state.fecha_cert or ahora().date(),
        )
        st.download_button(
            "Descargar constancia (PDF)",
            data=pdf,
            file_name=f"Constancia_{st.session_state.cedula}.pdf",
            mime="application/pdf",
            type="primary",
            width="stretch",
            on_click="ignore",
        )
        st.caption(f"Constancia No. {st.session_state.certificado}")


# ------------------------------------------------------------------
# Principal
# ------------------------------------------------------------------
def main():
    iniciar_estado()
    aplicar_estilo()
    encabezado()
    if not st.session_state.sheets_ok:
        st.warning("No fue posible conectar con el registro en línea. Puedes continuar, "
                   "pero avisa al equipo organizador para que tu participación quede registrada.")
    {
        "clave": pantalla_clave,
        "registro": pantalla_registro,
        "contenido": pantalla_contenido,
        "examen": pantalla_examen,
        "resultado": pantalla_resultado,
        "certificado": pantalla_certificado,
    }[st.session_state.pantalla]()


main()
