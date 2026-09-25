"""Genera el certificado en PDF (A4 horizontal) con fpdf2."""

from datetime import date
from pathlib import Path

from fpdf import FPDF

import config

RAIZ = Path(__file__).resolve().parent.parent
FUENTES = RAIZ / "fonts"
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def _rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def fecha_en_letras(d: date) -> str:
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def formato_cedula(cedula: str) -> str:
    return f"{int(cedula):,}".replace(",", ".")


def _registrar_fuentes(pdf: FPDF) -> str:
    """Usa Montserrat si está en /fonts; si no, Helvetica."""
    try:
        pdf.add_font("Montserrat", "", str(FUENTES / "Montserrat-Regular.ttf"))
        pdf.add_font("Montserrat", "B", str(FUENTES / "Montserrat-Bold.ttf"))
        return "Montserrat"
    except Exception:
        return "Helvetica"


def generar_certificado(nombre: str, cedula: str, numero: str, fecha: date) -> bytes:
    rojo = _rgb(config.COLOR_PRINCIPAL)
    gris = (90, 90, 90)
    pdf = FPDF(orientation="L", unit="mm", format="A4")  # 297 x 210 mm
    pdf.set_auto_page_break(False)
    pdf.set_margins(0, 0, 0)
    pdf.add_page()
    fuente = _registrar_fuentes(pdf)
    W, H = 297, 210

    # Marco: franja lateral roja + borde fino
    pdf.set_fill_color(*rojo)
    pdf.rect(0, 0, 14, H, style="F")
    pdf.set_draw_color(*rojo)
    pdf.set_line_width(0.6)
    pdf.rect(22, 10, W - 32, H - 20)
    pdf.set_line_width(0.2)
    pdf.rect(24.5, 12.5, W - 37, H - 25)

    cx, ancho = 30, W - 44  # zona de texto

    # Logo (solo si existe el archivo en assets/)
    logo = RAIZ / config.LOGO_PATH
    if logo.exists():
        pdf.image(str(logo), x=W / 2 - 22 + 7, y=20, h=22, keep_aspect_ratio=True, w=44)

    # Título
    pdf.set_text_color(*rojo)
    pdf.set_font(fuente, "B", 30)
    pdf.set_xy(cx, 50)
    pdf.cell(ancho, 14, "CERTIFICADO", align="C")
    pdf.set_font(fuente, "", 11)
    pdf.set_text_color(*gris)
    pdf.set_xy(cx, 64)
    pdf.cell(ancho, 6, "DE APROBACIÓN", align="C")

    # Cuerpo
    pdf.set_xy(cx, 78)
    pdf.cell(ancho, 7, f"{config.ORGANIZACION} certifica que", align="C")

    pdf.set_text_color(30, 30, 30)
    pdf.set_font(fuente, "B", 24)
    tam = 24
    while pdf.get_string_width(nombre.upper()) > ancho - 20 and tam > 14:
        tam -= 1
        pdf.set_font(fuente, "B", tam)
    pdf.set_xy(cx, 87)
    pdf.cell(ancho, 12, nombre.upper(), align="C")
    pdf.set_draw_color(*rojo)
    pdf.set_line_width(0.4)
    pdf.line(W / 2 - 60 + 7, 101, W / 2 + 60 + 7, 101)

    pdf.set_text_color(*gris)
    pdf.set_font(fuente, "", 11)
    pdf.set_xy(cx, 104)
    pdf.cell(ancho, 7, f"identificado(a) con cédula de ciudadanía No. {formato_cedula(cedula)}", align="C")
    pdf.set_xy(cx, 112)
    pdf.cell(ancho, 7, "aprobó satisfactoriamente el curso", align="C")

    pdf.set_text_color(*rojo)
    pdf.set_font(fuente, "B", 15)
    pdf.set_xy(cx + 10, 121)
    pdf.multi_cell(ancho - 20, 8, config.NOMBRE_CURSO, align="C")

    horas = config.INTENSIDAD_HORARIA
    texto_horas = f"{horas} hora" if horas == 1 else f"{horas} horas"
    pdf.set_text_color(*gris)
    pdf.set_font(fuente, "", 11)
    pdf.set_xy(cx, pdf.get_y() + 2)
    pdf.cell(ancho, 7, f"con una intensidad de {texto_horas}.", align="C")
    pdf.set_xy(cx, pdf.get_y() + 7)
    pdf.cell(ancho, 7, f"Expedido el {fecha_en_letras(fecha)}.", align="C")

    # Firma
    fx, fy, fw = W / 2 - 40 + 7, 166, 80
    firma = RAIZ / config.FIRMA_PATH
    if firma.exists():
        pdf.image(str(firma), x=fx + 15, y=fy - 18, w=50, h=17, keep_aspect_ratio=True)
    pdf.set_draw_color(60, 60, 60)
    pdf.set_line_width(0.3)
    pdf.line(fx, fy, fx + fw, fy)
    pdf.set_text_color(30, 30, 30)
    pdf.set_font(fuente, "B", 10)
    pdf.set_xy(fx, fy + 1.5)
    pdf.cell(fw, 5, config.FIRMANTE_NOMBRE, align="C")
    if config.FIRMANTE_CARGO:
        pdf.set_font(fuente, "", 9)
        pdf.set_text_color(*gris)
        pdf.set_xy(fx, fy + 6.5)
        pdf.cell(fw, 5, config.FIRMANTE_CARGO, align="C")

    # Número de certificado
    pdf.set_font(fuente, "", 8)
    pdf.set_text_color(*gris)
    pdf.set_xy(W - 110, H - 22)
    pdf.cell(80, 5, f"Certificado No. {numero}", align="R")

    return bytes(pdf.output())
