"""
Registro de intentos en Google Sheets.

Dos formas de conexión; la app elige sola según lo que haya en los Secrets:
  1. Apps Script (recomendada): secrets "apps_script_url" y "apps_script_token".
     No necesita cuenta de servicio ni llaves JSON.
  2. Cuenta de servicio (alternativa): sección [gcp_service_account] + SHEET_ID en config.py.
"""

import requests
import streamlit as st

import config

ENCABEZADOS = ["Fecha y hora", "Nombre", "Cédula", "Puntaje", "Estado", "Número de certificado"]


def _usa_apps_script() -> bool:
    try:
        return "apps_script_url" in st.secrets
    except Exception:
        return False


# ------------------------------------------------------------------
# Opción 1: Apps Script
# ------------------------------------------------------------------
def _apps_script(payload: dict) -> dict:
    datos = {**payload, "token": st.secrets["apps_script_token"]}
    r = requests.post(st.secrets["apps_script_url"], json=datos, timeout=40)
    r.raise_for_status()
    respuesta = r.json()
    if not respuesta.get("ok"):
        raise RuntimeError(respuesta.get("error", "error en el registro"))
    return respuesta


# ------------------------------------------------------------------
# Opción 2: cuenta de servicio (gspread)
# ------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _hoja():
    import gspread
    from google.oauth2.service_account import Credentials

    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    libro = gspread.authorize(creds).open_by_key(config.SHEET_ID)
    try:
        hoja = libro.worksheet(config.NOMBRE_HOJA)
    except gspread.WorksheetNotFound:
        hoja = libro.add_worksheet(title=config.NOMBRE_HOJA, rows=1000, cols=len(ENCABEZADOS))
    if hoja.row_values(1) != ENCABEZADOS:
        hoja.update(range_name="A1", values=[ENCABEZADOS])
    return hoja


def _filas_gspread() -> list[dict]:
    return _hoja().get_all_records(expected_headers=ENCABEZADOS)


# ------------------------------------------------------------------
# Funciones que usa la app
# ------------------------------------------------------------------
def historial_cedula(cedula: str) -> dict:
    """{"intentos": n, "aprobado": None | {nombre, fecha, puntaje, certificado}}"""
    if _usa_apps_script():
        r = _apps_script({"accion": "historial", "cedula": cedula})
        return {"intentos": r["intentos"], "aprobado": r["aprobado"]}

    filas = [f for f in _filas_gspread() if str(f["Cédula"]).strip() == cedula]
    ap = next((f for f in filas if f["Estado"] == "Aprobado"), None)
    return {
        "intentos": len(filas),
        "aprobado": None if not ap else {
            "nombre": ap["Nombre"], "fecha": str(ap["Fecha y hora"]),
            "puntaje": ap["Puntaje"], "certificado": ap["Número de certificado"],
        },
    }


def registrar_intento(fecha_hora: str, nombre: str, cedula: str, puntaje: float, aprobado: bool) -> str:
    """Guarda el intento y devuelve el número de certificado ("" si no aprobó)."""
    if _usa_apps_script():
        r = _apps_script({
            "accion": "registrar", "fecha": fecha_hora, "nombre": nombre,
            "cedula": cedula, "puntaje": puntaje, "aprobado": aprobado,
        })
        return r["certificado"]

    numero = ""
    if aprobado:
        prefijo = f"{config.PREFIJO_CERTIFICADO}-{fecha_hora[:4]}-"
        usados = [
            int(str(f["Número de certificado"])[len(prefijo):])
            for f in _filas_gspread()
            if str(f["Número de certificado"]).startswith(prefijo)
        ]
        numero = f"{prefijo}{(max(usados) + 1 if usados else 1):05d}"
    _hoja().append_row(
        [fecha_hora, nombre, cedula, puntaje, "Aprobado" if aprobado else "No aprobado", numero],
        value_input_option="USER_ENTERED",
    )
    return numero
