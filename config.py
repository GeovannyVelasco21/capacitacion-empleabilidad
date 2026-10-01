# =============================================================
#  CONFIGURACIÓN DE LA CAPACITACIÓN
#  Este es el único archivo que necesitas editar para cambiar
#  textos, puntajes o parámetros. Cambia solo lo que está
#  a la derecha del signo "=" y conserva las comillas.
# =============================================================

# --- Datos del curso -----------------------------------------
NOMBRE_CURSO = "Taller virtual de empleabilidad: Tu experiencia vale"
INTENSIDAD_HORARIA = 1              # horas que aparecen en la constancia
ORGANIZACION = "Nuevas Generaciones"  # quién otorga la constancia

# --- Evaluación ----------------------------------------------
PUNTAJE_MINIMO = 60                 # porcentaje mínimo para aprobar (0 a 100). 60 = 3 de 5 preguntas
MAX_INTENTOS = 0                    # intentos permitidos por cédula. 0 = sin límite

# --- Constancia ----------------------------------------------
FIRMANTE_NOMBRE = "Nuevas Generaciones"
FIRMANTE_CARGO = ""                 # ej.: "Coordinador(a) de Formación". Déjalo "" si no aplica
PREFIJO_CERTIFICADO = "NG"          # las constancias quedan como NG-2026-00001
LOGO_PATH = "assets/logo.png"       # opcional: si no existe, la constancia sale sin logo
FIRMA_PATH = "assets/firma.png"     # imagen de la firma (fondo transparente). Opcional

# --- Google Sheets -------------------------------------------
# Con la conexión por Apps Script (la recomendada) NO necesitas llenar SHEET_ID.
# Solo se usa si conectas con cuenta de servicio (alternativa).
# El ID es la parte larga de la dirección del Sheet:
# https://docs.google.com/spreadsheets/d/ESTE_ES_EL_ID/edit
SHEET_ID = "18w5iQXWoh2Tn3lGnBojuyyFitF8QBqY7EEAH6Xizpqc"
NOMBRE_HOJA = "Registros"           # nombre de la pestaña donde se guardan los intentos

# --- Acceso --------------------------------------------------
# True = pide una clave antes de entrar. La clave se guarda en los
# "Secrets" de Streamlit (campo clave_acceso), no aquí.
USAR_CLAVE_ACCESO = False

# --- Apariencia y archivos -----------------------------------
COLOR_PRINCIPAL = "#0070C0"         # azul de las diapositivas (botones, marco de la constancia)
COLOR_SUAVE = "#EAF3FB"             # azul muy claro para fondos y pasos completados
CARPETA_DIAPOSITIVAS = "."          # "." = las imágenes están en la carpeta principal del repositorio
ARCHIVO_PREGUNTAS = "preguntas.json"
ZONA_HORARIA = "America/Bogota"

# --- Texto de autorización de datos (Ley 1581 de 2012) --------
TEXTO_AUTORIZACION = (
    "De manera previa, expresa e informada, autorizo el tratamiento de mis datos "
    "personales (nombre y número de cédula) con la única finalidad de registrar mi "
    "participación en esta capacitación y expedir la constancia correspondiente, "
    "conforme a la Ley 1581 de 2012 y sus decretos reglamentarios. Conozco mi derecho "
    "a consultar, actualizar, rectificar o solicitar la supresión de mis datos."
)
