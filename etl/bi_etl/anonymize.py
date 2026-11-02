import hashlib
import hmac
import re
import unicodedata
from difflib import SequenceMatcher

MARCADORES_VACIOS = {"", "NO", "NO APLICA", "N/A", "NA", "NONE", "NAN"}
SIMILITUD_MINIMA = 0.92
TOKENS_MINIMOS = 2
LONGITUD_MINIMA_TOKEN = 3


def normalizar_nombre(valor) -> str:
    if valor is None:
        return ""
    texto = unicodedata.normalize("NFKD", str(valor))
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    texto = re.sub(r"[^A-Za-z ]", " ", texto).upper()
    return re.sub(r"\s+", " ", texto).strip()


def es_marcador_vacio(valor) -> bool:
    return normalizar_nombre(valor) in MARCADORES_VACIOS


def _tokens_identificables(nombre: str) -> list[str]:
    return [token for token in nombre.split() if len(token) >= LONGITUD_MINIMA_TOKEN]


def _es_misma_persona(corto: str, largo: str) -> bool:
    tokens_corto = corto.split()
    tokens_validos = _tokens_identificables(corto)
    if len(tokens_validos) < TOKENS_MINIMOS or len(tokens_validos) != len(tokens_corto):
        return False
    if set(tokens_validos) <= set(largo.split()):
        return True
    return SequenceMatcher(None, corto, largo).ratio() >= SIMILITUD_MINIMA


def agrupar_variantes(nombres) -> dict[str, str]:
    unicos = sorted({normalizar_nombre(nombre) for nombre in nombres} - MARCADORES_VACIOS, key=lambda n: (-len(n), n))
    canonicos: dict[str, str] = {}
    for nombre in unicos:
        canonico = next((c for c in dict.fromkeys(canonicos.values()) if _es_misma_persona(nombre, c)), nombre)
        canonicos[nombre] = canonico
    return canonicos


def seudonimo(nombre_canonico: str, sal: str) -> str:
    firma = hmac.new(sal.encode(), nombre_canonico.encode(), hashlib.sha256).hexdigest()
    return f"PER-{firma[:10].upper()}"
