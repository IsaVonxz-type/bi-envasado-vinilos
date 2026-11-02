import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date

import numpy as np
import pandas as pd

from . import anonymize
from .catalogs import (
    CODIGOS,
    GENERAL,
    MAQUINAS,
    MOTIVO_CORRECCIONES,
    SIN_ESPECIFICAR,
    SIN_SUBCODIGO,
    SUBCODIGO_ALIAS,
    SUBCODIGOS,
    TIPO_SIN_CLASIFICAR,
    TIPOS_NO_OPERACION,
    TURNO_ALIAS,
    TURNO_DESCONOCIDO,
    TURNO_NO_APLICA,
    TURNOS,
)

MAX_PACAS_POR_HORA = 100
HORAS_POR_DIA = 24
INICIO_VIGENCIA = date(2022, 1, 1)
FIN_VIGENCIA = date(9999, 12, 31)
REFERENCIA_DESCONOCIDA = "Desconocida"
REFERENCIA_NO_APLICA = "No aplica"
PERSONA_SIN_REGISTRO = "SIN-REGISTRO"
PERSONA_NO_APLICA = "NO-APLICA"
MOTIVO_NO_APLICA = "No aplica"
NOMBRES_MES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
NOMBRES_DIA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
COLUMNAS_MINUTOS = [f"min_{codigo}" for codigo in CODIGOS]
TOLERANCIA_CUADRE = 0.01
SUBCODIGOS_POR_CODIGO = {1: "subcodigo_1", 3: "subcodigo_3", 5: "subcodigo_5"}
COLUMNAS_PARO = [
    "fila_origen",
    "fecha",
    "maquina_nk",
    "turno_nk",
    "referencia_nk",
    "operario",
    "personal_involucrado",
    "area_involucrada",
    "causa_key",
    "minutos_paro",
]


@dataclass
class Resultado:
    dimensiones: dict[str, pd.DataFrame] = field(default_factory=dict)
    hechos: dict[str, pd.DataFrame] = field(default_factory=dict)
    calidad: list[dict] = field(default_factory=list)
    conteos: list[dict] = field(default_factory=list)
    cuadre: list[dict] = field(default_factory=list)

    def regla(self, regla: str, descripcion: str, tratamiento: str, afectados: int, unidad: str = "filas") -> None:
        self.calidad.append(
            {"regla": regla, "descripcion": descripcion, "tratamiento": tratamiento, "afectados": int(afectados), "unidad": unidad}
        )

    def conteo(self, etapa: str, filas: int) -> None:
        self.conteos.append({"orden": len(self.conteos) + 1, "etapa": etapa, "filas": int(filas)})


def sin_acentos(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFKD", texto)
    return "".join(caracter for caracter in descompuesto if not unicodedata.combining(caracter))


def normalizar_texto(valor) -> str:
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return ""
    return re.sub(r"\s+", " ", sin_acentos(str(valor))).strip().upper()


def es_vacio(valor) -> bool:
    return normalizar_texto(valor) == ""


def clave_referencia(valor) -> str:
    return re.sub(r"[^A-Z0-9]", "", normalizar_texto(valor)).replace("ALOCDOR", "ALOCOLOR").replace("STILOKIDS", "ESTILOKIDS")


def formato_referencia(valor: str) -> str:
    texto = re.sub(r"\s+", " ", str(valor)).strip()
    texto = re.sub(r"\bAlocdor\b", "Alocolor", texto)
    texto = re.sub(r"^Stilo Kids", "Estilo Kids", texto)
    texto = re.sub(r"(\d+)\s*cc", r"\1cc", texto)
    return re.sub(r"\((\d+)\s*col\)", r"(\1 col)", texto)


def atributos_referencia(referencia: str) -> dict:
    volumen = re.search(r"(\d+)cc", referencia)
    colores = re.search(r"\((\d+) col\)", referencia)
    familia = re.split(r"\s+\d+cc", referencia)[0].strip()
    return {
        "familia": familia,
        "volumen_cc": int(volumen.group(1)) if volumen else None,
        "colores": int(colores.group(1)) if colores else None,
    }


def normalizar_subcodigo(valor) -> str | None:
    texto = normalizar_texto(valor)
    if not texto or texto == normalizar_texto(SIN_ESPECIFICAR):
        return None
    if texto in SUBCODIGO_ALIAS:
        return SUBCODIGO_ALIAS[texto]
    coincidencia = re.match(r"^(\d+)\.(\d+)\.?([A-Z0-9])?(?=\s|$)", texto)
    if not coincidencia:
        return None
    mayor, menor, detalle = coincidencia.groups()
    candidato = f"{mayor}.{menor}.{detalle}" if detalle else f"{mayor}.{menor}"
    resto = texto[coincidencia.end():].strip()
    con_texto = f"{candidato} {resto}"
    if con_texto in SUBCODIGO_ALIAS:
        return SUBCODIGO_ALIAS[con_texto]
    return SUBCODIGO_ALIAS.get(candidato, candidato)


def normalizar_motivo(valor) -> str:
    texto = normalizar_texto(valor)
    if not texto or texto == "NO APLICA":
        return MOTIVO_NO_APLICA
    for error, correccion in MOTIVO_CORRECCIONES.items():
        texto = texto.replace(error, correccion)
    return texto.capitalize()


def normalizar_turno(valor) -> str:
    if es_vacio(valor):
        return TURNO_DESCONOCIDO
    texto = re.sub(r"\s+", " ", str(valor)).strip()
    return TURNO_ALIAS.get(texto, texto)


def clave_fecha(serie: pd.Series) -> pd.Series:
    return serie.dt.year * 10000 + serie.dt.month * 100 + serie.dt.day


def construir_dim_fecha(inicio: pd.Timestamp, fin: pd.Timestamp) -> pd.DataFrame:
    fechas = pd.date_range(date(inicio.year, 1, 1), date(fin.year, 12, 31), freq="D")
    return pd.DataFrame(
        {
            "fecha_key": clave_fecha(fechas.to_series()).astype(int).values,
            "fecha": fechas.date,
            "anio": fechas.year,
            "semestre": (fechas.month > 6).astype(int) + 1,
            "trimestre": fechas.quarter,
            "mes": fechas.month,
            "nombre_mes": [NOMBRES_MES[mes - 1] for mes in fechas.month],
            "anio_mes": fechas.strftime("%Y-%m"),
            "semana_iso": fechas.isocalendar().week.astype(int).values,
            "dia_semana": fechas.dayofweek + 1,
            "nombre_dia": [NOMBRES_DIA[dia] for dia in fechas.dayofweek],
            "es_fin_semana": fechas.dayofweek >= 5,
        }
    )


def construir_dim_causa() -> pd.DataFrame:
    filas = []
    for codigo, (nombre, area, programado, es_falla) in CODIGOS.items():
        base = {
            "codigo": codigo,
            "codigo_nombre": nombre,
            "area_impacto": area,
            "clasificacion_oee": "Programado" if programado else "No programado",
            "es_falla": es_falla,
        }
        if codigo in SUBCODIGOS_POR_CODIGO:
            filas.append({**base, "causa_nk": f"{codigo}.SE", "sistema": SIN_ESPECIFICAR, "subcodigo": SIN_ESPECIFICAR})
            for nk, (sistema, subcodigo) in SUBCODIGOS.items():
                if nk.startswith(f"{codigo}."):
                    filas.append({**base, "causa_nk": nk, "sistema": sistema, "subcodigo": subcodigo})
        else:
            filas.append({**base, "causa_nk": f"{codigo}.NA", "sistema": SIN_SUBCODIGO, "subcodigo": SIN_SUBCODIGO})
    dimension = pd.DataFrame(filas)
    dimension.insert(0, "causa_key", range(1, len(dimension) + 1))
    return dimension


def _a_numero(base: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    resultado = base.copy()
    for columna in columnas:
        resultado[columna] = pd.to_numeric(resultado[columna], errors="coerce")
    return resultado


def _totales(base: pd.DataFrame) -> dict[str, float]:
    return {
        "pacas": float(base["pacas"].sum()),
        "horas_trabajadas": float(base["horas_trabajadas"].sum()),
        "minutos_paro": float(base[COLUMNAS_MINUTOS].sum().sum()),
        "horas_no_trabajadas": float(base["horas_no_trabajadas"].sum()),
    }


def _limpiar_filas(base: pd.DataFrame, resultado: Resultado) -> tuple[pd.DataFrame, dict[str, float]]:
    resultado.conteo("Filas leídas de Base De Datos", len(base))
    tiene_paro = base[COLUMNAS_MINUTOS].fillna(0).sum(axis=1) > 0
    tiene_produccion = base["pacas"].notna() | base["horas_trabajadas"].notna()
    tiene_no_operacion = base["horas_no_trabajadas"].fillna(0) > 0

    vacias = ~(tiene_paro | tiene_produccion | tiene_no_operacion)
    resultado.regla(
        "R01",
        "Filas sin pacas, horas trabajadas, horas no trabajadas ni minutos de paro",
        "Se eliminan: no aportan ninguna medida",
        vacias.sum(),
    )
    resultado.conteo("Tras eliminar filas sin medidas (R01)", (~vacias).sum())

    columnas_negocio = [columna for columna in base.columns if columna != "fila_origen"]
    firma = base[columnas_negocio].astype(str).agg("|".join, axis=1)
    duplicada = firma.duplicated(keep="first")
    duplicada_produccion = duplicada & tiene_produccion
    resultado.regla(
        "R02",
        "Filas idénticas en todas las columnas y con producción",
        "Se conserva la primera: una transcripción repetida contaría dos veces las pacas",
        duplicada_produccion.sum(),
    )
    duplicada_sin_produccion = duplicada & ~tiene_produccion & (tiene_paro | tiene_no_operacion)
    resultado.regla(
        "R03",
        "Filas idénticas sin producción, solo con paro u horas no trabajadas",
        "Se conservan: dos paros iguales en un turno pueden ser eventos distintos",
        duplicada_sin_produccion.sum(),
    )

    excluir = vacias | duplicada_produccion
    excluidos = _totales(base[excluir])
    limpia = base[~excluir].copy()
    resultado.conteo("Tras eliminar duplicados con producción (R02)", len(limpia))
    return limpia, excluidos


def _normalizar_dimensiones_fila(base: pd.DataFrame, resultado: Resultado) -> pd.DataFrame:
    limpia = base.copy()
    invalidas = sorted(set(limpia["maquina"]) - set(MAQUINAS))
    if invalidas:
        raise ValueError(f"Máquinas no reconocidas: {invalidas}")

    limpia["fecha"] = pd.to_datetime(limpia["fecha"])
    limpia["turno_nk"] = limpia["turno"].map(normalizar_turno)
    validos = {turno[0] for turno in TURNOS}
    fuera_catalogo = sorted(set(limpia["turno_nk"]) - validos)
    if fuera_catalogo:
        raise ValueError(f"Turnos no reconocidos: {fuera_catalogo}")
    resultado.regla(
        "R04",
        "Filas sin turno, concentradas en 2022 y 2023",
        f"Se asigna el miembro '{TURNO_DESCONOCIDO}': no hay datos para recuperarlo",
        limpia["turno"].map(es_vacio).sum(),
    )
    resultado.regla(
        "R05",
        "Columna 'Unidad por display' con valores de turno, siempre iguales a la columna Turno",
        "Se ignora: es redundante y no aporta datos nuevos",
        limpia["unidad_por_display"].notna().sum(),
    )

    limpia["referencia_nk"] = limpia["referencia"].map(
        lambda valor: REFERENCIA_DESCONOCIDA if es_vacio(valor) else formato_referencia(valor)
    )
    corregidas = limpia["referencia"].notna() & (limpia["referencia"].astype(str) != limpia["referencia_nk"])
    resultado.regla(
        "R06",
        "Referencias con errores de escritura o formato inconsistente",
        "Se normalizan al formato 'Familia NNcc (K col)'",
        corregidas.sum(),
    )
    resultado.regla(
        "R07",
        "Filas sin referencia",
        f"Se asigna '{REFERENCIA_DESCONOCIDA}'; el rendimiento no se calcula",
        limpia["referencia"].map(es_vacio).sum(),
    )
    return limpia


def _validar_produccion(base: pd.DataFrame, resultado: Resultado) -> pd.DataFrame:
    limpia = base.copy()
    limpia["minutos_fila"] = limpia[COLUMNAS_MINUTOS].fillna(0).sum(axis=1)
    pacas_por_hora = (limpia["pacas"] / limpia["horas_trabajadas"]).where(limpia["horas_trabajadas"] > 0)
    limpia["alerta_pacas_atipicas"] = pacas_por_hora > MAX_PACAS_POR_HORA
    limpia["pacas_validas"] = limpia["pacas"].where(~limpia["alerta_pacas_atipicas"])
    resultado.regla(
        "R08",
        f"Pacas imposibles: más de {MAX_PACAS_POR_HORA} pacas por hora",
        "Se conserva el valor reportado y se excluye de pacas válidas, unidades y rendimiento",
        limpia["alerta_pacas_atipicas"].sum(),
    )
    limpia["alerta_paro_excede"] = limpia["minutos_fila"] / 60 > limpia["horas_trabajadas"]
    resultado.regla(
        "R09",
        "Filas con más minutos de paro que horas trabajadas",
        "Se conservan con alerta; el tiempo operativo se limita a cero",
        limpia["alerta_paro_excede"].sum(),
    )
    resultado.regla(
        "R10",
        "Producción con 0 horas trabajadas",
        "Se conserva; se evita la división por cero al agregar tiempos antes de dividir",
        (limpia["horas_trabajadas"] == 0).sum(),
    )
    return limpia


def _construir_personas(base: pd.DataFrame, sal: str, resultado: Resultado):
    con_ajuste = base["min_5"].fillna(0) > 0
    involucrados = base.loc[con_ajuste, "personal_involucrado"]
    canonicos = anonymize.agrupar_variantes(pd.concat([base["operario"], involucrados]).dropna().tolist())

    operarios = {canonicos[anonymize.normalizar_nombre(n)] for n in base["operario"].dropna() if not anonymize.es_marcador_vacio(n)}
    filas = [
        {"seudonimo": PERSONA_SIN_REGISTRO, "rol": "Sin registro"},
        {"seudonimo": PERSONA_NO_APLICA, "rol": "No aplica"},
    ]
    seudonimos = {}
    for canonico in sorted(set(canonicos.values())):
        seudonimos[canonico] = anonymize.seudonimo(canonico, sal)
        filas.append({"seudonimo": seudonimos[canonico], "rol": "Operación" if canonico in operarios else "Mantenimiento"})
    filas = [filas[0], filas[1], *sorted(filas[2:], key=lambda fila: fila["seudonimo"])]
    dimension = pd.DataFrame(filas)
    dimension.insert(0, "persona_key", range(1, len(dimension) + 1))
    claves = dict(zip(dimension["seudonimo"], dimension["persona_key"]))

    def clave_persona(valor) -> int:
        if valor is None or (isinstance(valor, float) and np.isnan(valor)):
            return claves[PERSONA_SIN_REGISTRO]
        if anonymize.es_marcador_vacio(valor):
            return claves[PERSONA_NO_APLICA]
        return claves[seudonimos[canonicos[anonymize.normalizar_nombre(valor)]]]

    variantes = len(canonicos) - len(set(canonicos.values()))
    resultado.regla(
        "R11",
        "Nombres de personas en Operario y Personal involucrado",
        "Se reemplazan por un seudónimo HMAC-SHA256 con sal secreta; ningún nombre llega a la base",
        len(set(canonicos.values())),
        "personas",
    )
    resultado.regla(
        "R12",
        "Variantes de escritura de una misma persona (nombre completo o error tipográfico)",
        "Se unifican por reglas; un nombre de pila suelto no se une, porque podría ser otra persona",
        variantes,
        "variantes",
    )
    resultado.regla(
        "R13",
        "Valores 'No' y 'No aplica' en Operario",
        "Se asignan al miembro 'NO-APLICA'",
        base["operario"].map(lambda v: v is not None and not pd.isna(v) and anonymize.es_marcador_vacio(v)).sum(),
    )
    resultado.regla(
        "R14",
        "Columna Observaciones con texto libre que puede contener nombres",
        "No se carga: minimización de datos personales",
        base["observaciones"].notna().sum(),
    )
    return dimension, clave_persona


def _construir_estandares(estandares: pd.DataFrame, referencias: dict[str, int], resultado: Resultado) -> pd.DataFrame:
    catalogo = estandares.copy()
    catalogo["unidades_por_paca"] = pd.to_numeric(catalogo["unidades_por_paca"], errors="coerce")
    catalogo["unidades_por_minuto"] = pd.to_numeric(catalogo["unidades_por_minuto"], errors="coerce")
    invalidas = ~((catalogo["unidades_por_paca"] > 0) & (catalogo["unidades_por_minuto"] > 0))
    catalogo = catalogo[~invalidas].copy()
    catalogo["referencia_nk"] = catalogo["referencia"].map(formato_referencia)
    catalogo["clave"] = catalogo["referencia_nk"].map(clave_referencia)
    repetidas = catalogo.duplicated(["maquina", "clave"], keep="first")
    resultado.regla(
        "R15",
        "Catálogo de velocidades: filas sin estándar o repetidas para la misma máquina y referencia",
        "Se excluyen; se conserva la primera aparición",
        invalidas.sum() + repetidas.sum(),
    )
    catalogo = catalogo[~repetidas]

    velocidad_maquina = catalogo.groupby("maquina")["unidades_por_minuto"].agg(lambda serie: serie.mode().iloc[0]).to_dict()
    por_clave = catalogo.drop_duplicates("clave").set_index("clave")
    exactos = {(fila.maquina, fila.clave): fila for fila in catalogo.itertuples()}

    filas = []
    for (maquina, referencia), _ in sorted(referencias.items()):
        clave = clave_referencia(referencia)
        if (maquina, clave) in exactos:
            origen = exactos[(maquina, clave)]
            filas.append((maquina, referencia, origen.unidades_por_paca, origen.unidades_por_minuto, "catalogo"))
        elif clave in por_clave.index:
            filas.append(
                (maquina, referencia, por_clave.loc[clave, "unidades_por_paca"], velocidad_maquina[maquina], "inferido")
            )
    dimension = pd.DataFrame(filas, columns=["maquina_nk", "referencia_nk", "unidades_por_paca", "unidades_por_minuto", "origen"])
    dimension.insert(0, "estandar_key", range(1, len(dimension) + 1))
    dimension["valido_desde"] = INICIO_VIGENCIA
    dimension["valido_hasta"] = FIN_VIGENCIA
    dimension["es_vigente"] = True
    return dimension


def _construir_paros(base: pd.DataFrame, causa_keys: dict[str, int], resultado: Resultado) -> pd.DataFrame:
    filas = []
    sin_especificar = {1: 0, 3: 0, 5: 0}
    no_reconocidos: set[str] = set()
    for codigo in CODIGOS:
        columna = f"min_{codigo}"
        con_paro = base[base[columna].fillna(0) > 0]
        for fila in con_paro.itertuples(index=False):
            if codigo in SUBCODIGOS_POR_CODIGO:
                crudo = getattr(fila, SUBCODIGOS_POR_CODIGO[codigo])
                nk = normalizar_subcodigo(crudo)
                if nk is not None and (nk not in SUBCODIGOS or not nk.startswith(f"{codigo}.")):
                    no_reconocidos.add(normalizar_texto(crudo))
                    nk = None
                if nk is None:
                    sin_especificar[codigo] += 1
                    nk = f"{codigo}.SE"
            else:
                nk = f"{codigo}.NA"
            filas.append(
                {
                    "fila_origen": fila.fila_origen,
                    "fecha": fila.fecha,
                    "maquina_nk": fila.maquina,
                    "turno_nk": fila.turno_nk,
                    "referencia_nk": fila.referencia_nk,
                    "operario": fila.operario,
                    "personal_involucrado": fila.personal_involucrado if codigo == 5 else None,
                    "area_involucrada": fila.area_involucrada if codigo == 5 else None,
                    "causa_key": causa_keys[nk],
                    "minutos_paro": getattr(fila, columna),
                }
            )
    if no_reconocidos:
        raise ValueError(f"Subcódigos no reconocidos: {sorted(no_reconocidos)}")

    for codigo, regla in ((1, "R16"), (3, "R17"), (5, "R18")):
        resultado.regla(
            regla,
            f"Paros de código {codigo:02d} sin subcódigo",
            f"Se asignan a '{SIN_ESPECIFICAR}' dentro del código {codigo:02d}",
            sin_especificar[codigo],
        )
    con_sub_sin_minutos = (base["min_5"].fillna(0) <= 0) & base["subcodigo_5"].map(
        lambda valor: normalizar_subcodigo(valor) is not None
    )
    resultado.regla(
        "R19",
        "Subcódigo 5 diligenciado sin minutos de paro",
        "Se ignora: no hay duración que asignar",
        con_sub_sin_minutos.sum(),
    )
    originales = pd.concat([base["subcodigo_1"], base["subcodigo_3"], base["subcodigo_5"]]).dropna()
    canonicos = {nk.split(" ")[0] for nk in SUBCODIGOS}
    variantes = originales.map(lambda valor: not normalizar_texto(valor).startswith(tuple(f"{c} " for c in canonicos))
                               and normalizar_subcodigo(valor) is not None)
    resultado.regla(
        "R20",
        "Subcódigos con formato o numeración anterior (1.2C frente a 1.2.C; 4.x frente a 5.x)",
        "Se unifican al catálogo vigente",
        variantes.sum(),
    )
    paros = pd.DataFrame(filas, columns=COLUMNAS_PARO)
    paros["fecha"] = pd.to_datetime(paros["fecha"])
    return paros


def _construir_no_operacion(base: pd.DataFrame, resultado: Resultado) -> tuple[pd.DataFrame, pd.DataFrame]:
    tipo_clave = base["tipo_paro"].map(normalizar_texto)
    mapeo = tipo_clave.map(lambda valor: TIPOS_NO_OPERACION.get(valor, TIPO_SIN_CLASIFICAR))
    trabajo = base.assign(
        tipo=mapeo.map(lambda par: par[0]),
        categoria=mapeo.map(lambda par: par[1]),
        motivo=base["observacion_paro"].map(normalizar_motivo),
    )
    reconocidos = tipo_clave.isin(TIPOS_NO_OPERACION)
    unificados = tipo_clave[reconocidos].nunique() - trabajo.loc[reconocidos, "tipo"].nunique()
    resultado.regla(
        "R21",
        "Dos catálogos de 'Tipo de paro' conviviendo en la fuente",
        "Se unifican por equivalencia documentada",
        unificados,
        "valores",
    )
    registros = trabajo[trabajo["horas_no_trabajadas"].fillna(0) > 0]
    resultado.regla(
        "R22",
        "Horas no trabajadas sin tipo de paro clasificable",
        f"Se asignan a '{TIPO_SIN_CLASIFICAR[0]}'",
        (registros["tipo"] == TIPO_SIN_CLASIFICAR[0]).sum(),
    )

    horas_dia = (
        trabajo.groupby(["fecha", "maquina"], as_index=False)["horas_trabajadas"].sum().rename(columns={"horas_trabajadas": "horas_dia"})
    )
    agrupado = (
        registros.groupby(["fecha", "maquina", "tipo", "categoria", "motivo"], as_index=False)
        .agg(horas_reportadas=("horas_no_trabajadas", "sum"), filas_origen=("fila_origen", "count"))
        .merge(horas_dia, on=["fecha", "maquina"], validate="many_to_one")
    )
    total_dia = agrupado.groupby(["fecha", "maquina"])["horas_reportadas"].transform("sum")
    tope = (HORAS_POR_DIA - agrupado["horas_dia"]).clip(lower=0)
    factor = (tope / total_dia).clip(upper=1)
    agrupado["horas_ajustadas"] = (agrupado["horas_reportadas"] * factor).round(2)
    agrupado["horas_ajustadas"] = agrupado[["horas_ajustadas", "horas_reportadas"]].min(axis=1)

    excedidos = agrupado.loc[total_dia > tope, ["fecha", "maquina"]].drop_duplicates()
    resultado.regla(
        "R23",
        "Máquina-día con más horas no trabajadas de las posibles (24 h menos las trabajadas)",
        "Se conserva lo reportado y se ajusta proporcionalmente al tope en horas_ajustadas",
        len(excedidos),
        "máquina-día",
    )
    motivos = (
        agrupado[["tipo", "categoria", "motivo"]].drop_duplicates().sort_values(["tipo", "motivo"]).reset_index(drop=True)
    )
    motivos.insert(0, "motivo_key", range(1, len(motivos) + 1))
    agrupado = agrupado.merge(motivos, on=["tipo", "categoria", "motivo"], validate="many_to_one")
    resultado.regla(
        "R24",
        "Observaciones de paro con mayúsculas y errores de escritura",
        "Se normalizan; lista cerrada sin nombres de personas",
        base["observacion_paro"].notna().sum() - (base["observacion_paro"].map(normalizar_motivo) == base["observacion_paro"]).sum(),
    )
    return motivos, agrupado


def _agregar_cuadre(resultado: Resultado, fuente: dict, excluidos: dict, cargados: dict, atipicas: float, ajuste: float) -> None:
    explicaciones = {
        "pacas": ("pacas", f"Se excluye lo de R02. Además, pacas válidas descuenta {atipicas:,.0f} pacas imposibles (R08)"),
        "horas_trabajadas": ("horas", "Se excluye lo de filas duplicadas con producción (R02)"),
        "minutos_paro": ("minutos", "Se excluye lo de filas duplicadas con producción (R02)"),
        "horas_no_trabajadas": ("horas", f"Se excluye lo de R02. El análisis debe usar horas_ajustadas: {ajuste:,.2f} h menos por R23"),
    }
    for metrica, (unidad, explicacion) in explicaciones.items():
        esperado = fuente[metrica] - excluidos[metrica]
        diferencia = cargados[metrica] - esperado
        resultado.cuadre.append(
            {
                "metrica": metrica,
                "unidad": unidad,
                "fuente": round(fuente[metrica], 2),
                "excluido": round(excluidos[metrica], 2),
                "esperado": round(esperado, 2),
                "cargado": round(cargados[metrica], 2),
                "diferencia": round(diferencia, 2),
                "cuadra": abs(diferencia) <= TOLERANCIA_CUADRE,
                "explicacion": explicacion,
            }
        )


def transformar(base_cruda: pd.DataFrame, estandares: pd.DataFrame, sal: str) -> Resultado:
    resultado = Resultado()
    base = _a_numero(base_cruda, ["pacas", "horas_trabajadas", "horas_no_trabajadas", *COLUMNAS_MINUTOS])
    negativos = (base[["pacas", "horas_trabajadas", "horas_no_trabajadas", *COLUMNAS_MINUTOS]] < 0).any(axis=1).sum()
    if negativos:
        raise ValueError(f"La fuente tiene {negativos} filas con medidas negativas")

    fuente = _totales(base)
    limpia, excluidos = _limpiar_filas(base, resultado)
    limpia = _normalizar_dimensiones_fila(limpia, resultado)
    limpia = _validar_produccion(limpia, resultado)

    dim_fecha = construir_dim_fecha(limpia["fecha"].min(), limpia["fecha"].max())
    dim_maquina = pd.DataFrame(
        [{"maquina_key": linea, "maquina_nk": maquina, "numero_linea": linea} for maquina, linea in MAQUINAS.items()]
    )
    dim_turno = pd.DataFrame(TURNOS, columns=["turno_nk", "esquema", "hora_inicio", "hora_fin", "horas_nominales"])
    dim_turno.insert(0, "turno_key", range(1, len(dim_turno) + 1))

    nombres_referencia = sorted(set(limpia["referencia_nk"]) - {REFERENCIA_DESCONOCIDA, REFERENCIA_NO_APLICA})
    filas_referencia = [
        {"referencia_nk": REFERENCIA_DESCONOCIDA, "familia": REFERENCIA_DESCONOCIDA, "volumen_cc": None, "colores": None},
        {"referencia_nk": REFERENCIA_NO_APLICA, "familia": REFERENCIA_NO_APLICA, "volumen_cc": None, "colores": None},
        *[{"referencia_nk": nombre, **atributos_referencia(nombre)} for nombre in nombres_referencia],
    ]
    dim_referencia = pd.DataFrame(filas_referencia)
    dim_referencia.insert(0, "referencia_key", range(1, len(dim_referencia) + 1))

    dim_persona, clave_persona = _construir_personas(limpia, sal, resultado)
    dim_causa = construir_dim_causa()

    produccion = limpia[limpia["pacas"].notna() | limpia["horas_trabajadas"].notna()].copy()
    combinaciones = {
        (maquina, referencia): 1
        for maquina, referencia in zip(produccion["maquina"], produccion["referencia_nk"])
        if referencia not in (REFERENCIA_DESCONOCIDA, REFERENCIA_NO_APLICA)
    }
    dim_estandar = _construir_estandares(estandares, combinaciones, resultado)

    claves_turno = dict(zip(dim_turno["turno_nk"], dim_turno["turno_key"]))
    claves_referencia = dict(zip(dim_referencia["referencia_nk"], dim_referencia["referencia_key"]))
    claves_causa = dict(zip(dim_causa["causa_nk"], dim_causa["causa_key"]))
    claves_estandar = {
        (fila.maquina_nk, fila.referencia_nk): fila.estandar_key for fila in dim_estandar.itertuples()
    }
    unidades_paca = {
        (fila.maquina_nk, fila.referencia_nk): fila.unidades_por_paca for fila in dim_estandar.itertuples()
    }

    sin_estandar = [
        (maquina, referencia) not in claves_estandar for maquina, referencia in zip(produccion["maquina"], produccion["referencia_nk"])
    ]
    resultado.regla(
        "R25",
        "Producción sin estándar de velocidad o de unidades por paca (referencia ausente o fuera de catálogo)",
        "Disponibilidad sí se calcula; rendimiento y OEE no. La vista informa la cobertura",
        sum(sin_estandar),
    )
    inferidos = sum(
        1 for maquina, referencia in zip(produccion["maquina"], produccion["referencia_nk"])
        if (maquina, referencia) in claves_estandar and
        dim_estandar.loc[dim_estandar["estandar_key"] == claves_estandar[(maquina, referencia)], "origen"].iloc[0] == "inferido"
    )
    resultado.regla(
        "R26",
        "Referencia en catálogo de otra máquina, no en la máquina que la produjo",
        "Se usa sus unidades por paca y la velocidad habitual de la máquina; origen = 'inferido'",
        inferidos,
    )

    fact_produccion = pd.DataFrame(
        {
            "fila_origen": produccion["fila_origen"],
            "fecha_key": clave_fecha(produccion["fecha"]),
            "maquina_key": produccion["maquina"].map(MAQUINAS),
            "turno_key": produccion["turno_nk"].map(claves_turno),
            "referencia_key": produccion["referencia_nk"].map(claves_referencia),
            "operario_key": produccion["operario"].map(clave_persona),
            "estandar_key": [claves_estandar.get(par) for par in zip(produccion["maquina"], produccion["referencia_nk"])],
            "pacas_reportadas": produccion["pacas"],
            "pacas_validas": produccion["pacas_validas"],
            "unidades_producidas": [
                paca * unidades_paca[par] if par in unidades_paca and pd.notna(paca) else None
                for paca, par in zip(produccion["pacas_validas"], zip(produccion["maquina"], produccion["referencia_nk"]))
            ],
            "horas_trabajadas": produccion["horas_trabajadas"],
            "alerta_pacas_atipicas": produccion["alerta_pacas_atipicas"].astype(bool),
            "alerta_paro_excede": produccion["alerta_paro_excede"].astype(bool),
        }
    )

    paros = _construir_paros(limpia, claves_causa, resultado)
    fact_paro = pd.DataFrame(
        {
            "fila_origen": paros["fila_origen"],
            "fecha_key": clave_fecha(paros["fecha"]),
            "maquina_key": paros["maquina_nk"].map(MAQUINAS),
            "turno_key": paros["turno_nk"].map(claves_turno),
            "referencia_key": paros["referencia_nk"].map(claves_referencia),
            "operario_key": paros["operario"].map(clave_persona),
            "causa_key": paros["causa_key"],
            "persona_involucrada_key": paros["personal_involucrado"].map(clave_persona),
            "area_involucrada": paros["area_involucrada"],
            "minutos_paro": paros["minutos_paro"],
        }
    )

    dim_motivo, no_operacion = _construir_no_operacion(limpia, resultado)
    fact_no_operacion = pd.DataFrame(
        {
            "fecha_key": clave_fecha(no_operacion["fecha"]),
            "maquina_key": no_operacion["maquina"].map(MAQUINAS),
            "motivo_key": no_operacion["motivo_key"],
            "filas_origen": no_operacion["filas_origen"],
            "horas_reportadas": no_operacion["horas_reportadas"],
            "horas_ajustadas": no_operacion["horas_ajustadas"],
        }
    )

    estandar_final = dim_estandar.assign(
        maquina_key=dim_estandar["maquina_nk"].map(MAQUINAS),
        referencia_key=dim_estandar["referencia_nk"].map(claves_referencia),
    )[
        ["estandar_key", "maquina_key", "referencia_key", "unidades_por_paca", "unidades_por_minuto", "origen", "valido_desde", "valido_hasta", "es_vigente"]
    ]

    resultado.dimensiones = {
        "dim_fecha": dim_fecha,
        "dim_maquina": dim_maquina,
        "dim_turno": dim_turno,
        "dim_referencia": dim_referencia,
        "dim_persona": dim_persona,
        "dim_causa_paro": dim_causa[
            ["causa_key", "causa_nk", "codigo", "codigo_nombre", "area_impacto", "clasificacion_oee", "es_falla", "sistema", "subcodigo"]
        ],
        "dim_motivo_no_operacion": dim_motivo[["motivo_key", "tipo", "categoria", "motivo"]],
        "dim_estandar_produccion": estandar_final,
    }
    resultado.hechos = {
        "fact_produccion": fact_produccion,
        "fact_paro": fact_paro,
        "fact_no_operacion": fact_no_operacion,
    }

    cargados = {
        "pacas": float(fact_produccion["pacas_reportadas"].sum()),
        "horas_trabajadas": float(fact_produccion["horas_trabajadas"].sum()),
        "minutos_paro": float(fact_paro["minutos_paro"].sum()),
        "horas_no_trabajadas": float(fact_no_operacion["horas_reportadas"].sum()),
    }
    atipicas = float(produccion.loc[produccion["alerta_pacas_atipicas"], "pacas"].sum())
    ajuste = float(fact_no_operacion["horas_reportadas"].sum() - fact_no_operacion["horas_ajustadas"].sum())
    _agregar_cuadre(resultado, fuente, excluidos, cargados, atipicas, ajuste)

    resultado.conteo("fact_produccion", len(fact_produccion))
    resultado.conteo("fact_paro (una fila por código con minutos)", len(fact_paro))
    resultado.conteo("fact_no_operacion (máquina, día y motivo)", len(fact_no_operacion))
    return resultado
