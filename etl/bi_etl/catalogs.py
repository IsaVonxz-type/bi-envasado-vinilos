from datetime import time

MAQUINAS = {"Vinilos_1": 1, "Vinilos_2": 2, "Vinilos_3": 3, "Vinilos_4": 4}

TURNO_DESCONOCIDO = "Desconocido"
TURNO_NO_APLICA = "No aplica"
TURNOS = [
    ("6am-2pm (Turno 1)", "3 turnos de 8 h", time(6), time(14), 8.0),
    ("2pm-10pm (Turno 2)", "3 turnos de 8 h", time(14), time(22), 8.0),
    ("10pm-6am (Turno 3)", "3 turnos de 8 h", time(22), time(6), 8.0),
    ("6am-4:30pm", "Jornada de 10,5 h", time(6), time(16, 30), 10.5),
    ("6am-6pm", "2 turnos de 12 h", time(6), time(18), 12.0),
    ("6pm-6am", "2 turnos de 12 h", time(18), time(6), 12.0),
    (TURNO_NO_APLICA, "No aplica", None, None, None),
    (TURNO_DESCONOCIDO, "Sin registro", None, None, None),
]
TURNO_ALIAS = {"6am-2pm": "6am-2pm (Turno 1)", "2pm-10pm": "2pm-10pm (Turno 2)", "10pm-6am": "10pm-6am (Turno 3)"}

CODIGOS = {
    1: ("[01] Falla del sistema electromecánico y/o de control", "Mantenimiento", False, True),
    2: ("[02] Espera de soporte de mantenimiento", "Mantenimiento", False, False),
    3: ("[03] Novedad en los sistemas de potencia (aire, energía, vapor)", "Mantenimiento", False, True),
    4: ("[04] Mantenimiento preventivo", "Mantenimiento", False, False),
    5: ("[05] Ajuste operativo", "Producción", False, False),
    6: ("[06] Limpieza por derrame operativo", "Producción", False, False),
    7: ("[07] Alistamiento de máquina / Cambio de referencia", "Producción", False, False),
    8: ("[08] Capacitación / Reunión", "Producción", False, False),
    9: ("[09] Falta de operario", "Producción", False, False),
    10: ("[10] Paro por ventaja / evacuación", "Producción", False, False),
    11: ("[11] Reproceso", "Producción", False, False),
    12: ("[12] Materia prima defectuosa o empaque no conforme", "Calidad", False, False),
    13: ("[13] Espera por aval del laboratorio de microbiología", "Calidad", False, False),
    14: ("[14] Falta de materia prima", "Almacén de materias primas", False, False),
    15: ("[15] Cambio de insumos (roscadores, O'ring, etiquetas)", "Paro programado", True, False),
    16: ("[16] Alimentación y aseo de la zona de trabajo y la máquina", "Paro programado", True, False),
    17: ("[17] Pausa activa", "Paro programado", True, False),
    18: ("[18] Desinfección", "Producción", False, False),
}

SIN_ESPECIFICAR = "Sin especificar"
SIN_SUBCODIGO = "No aplica"
GENERAL = "General"

SUBCODIGOS = {
    "1.1": ("1.1 Sistema alimentador de envases", GENERAL),
    "1.1.A": ("1.1 Sistema alimentador de envases", "1.1.A Banda"),
    "1.1.B": ("1.1 Sistema alimentador de envases", "1.1.B Motor"),
    "1.1.C": ("1.1 Sistema alimentador de envases", "1.1.C Sensor"),
    "1.2": ("1.2 Sistema de dosificación", GENERAL),
    "1.2.A": ("1.2 Sistema de dosificación", "1.2.A Cambio de racores"),
    "1.2.B": ("1.2 Sistema de dosificación", "1.2.B Ajuste de sensor"),
    "1.2.C": ("1.2 Sistema de dosificación", "1.2.C Cambio de válvula"),
    "1.2.D": ("1.2 Sistema de dosificación", "1.2.D Retenedores"),
    "1.2.E": ("1.2 Sistema de dosificación", "1.2.E O'ring"),
    "1.3": ("1.3 Sistema de banda de entrada", GENERAL),
    "1.3.A": ("1.3 Sistema de banda de entrada", "1.3.A Banda"),
    "1.3.B": ("1.3 Sistema de banda de entrada", "1.3.B Motor"),
    "1.4": ("1.4 Sistema de tapado", GENERAL),
    "1.4.A": ("1.4 Sistema de tapado", "1.4.A Motor del transfer"),
    "1.4.B": ("1.4 Sistema de tapado", "1.4.B Pisador de tapa"),
    "1.4.C": ("1.4 Sistema de tapado", "1.4.C Sensor"),
    "1.5": ("1.5 Sistema de alimentación de tapa", GENERAL),
    "1.5.A": ("1.5 Sistema de alimentación de tapa", "1.5.A Banda"),
    "1.5.B": ("1.5 Sistema de alimentación de tapa", "1.5.B Motor"),
    "1.5.C": ("1.5 Sistema de alimentación de tapa", "1.5.C Sensor"),
    "1.6": ("1.6 Sistema Video Jet", GENERAL),
    "1.6.A": ("1.6 Sistema Video Jet", "1.6.A Fotocelda"),
    "1.6.B": ("1.6 Sistema Video Jet", "1.6.B Sensor"),
    "1.7": ("1.7 Sistema de sujeción y roscadores", GENERAL),
    "1.7.A": ("1.7 Sistema de sujeción y roscadores", "1.7.A Banda de sujeción"),
    "1.7.B": ("1.7 Sistema de sujeción y roscadores", "1.7.B Roscadores"),
    "1.8": ("1.8 Sistema etiquetadora", GENERAL),
    "1.8.A": ("1.8 Sistema etiquetadora", "1.8.A Banda"),
    "1.8.B": ("1.8 Sistema etiquetadora", "1.8.B Motor"),
    "1.8.C": ("1.8 Sistema etiquetadora", "1.8.C Sensor"),
    "3.1": ("3.1 Fallo en la subestación", GENERAL),
    "3.2": ("3.2 Fallo en la red pública", GENERAL),
    "3.3": ("3.3 Falla en la red neumática o el compresor", GENERAL),
    "3.4": ("3.4 Falla en la red de enfriamiento o el chiller", GENERAL),
    "3.5": ("3.5 Falla en la red de vapor o la caldera", GENERAL),
    "5.1": ("5.1 Sistema alimentador de envases", GENERAL),
    "5.2": ("5.2 Sistema de dosificación de pintura", GENERAL),
    "5.3": ("5.3 Banda transportadora de entrada", GENERAL),
    "5.4": ("5.4 Banda transportadora de salida", GENERAL),
    "5.5": ("5.5 Transfer y pisador de tapa", GENERAL),
    "5.6": ("5.6 Sistema alimentador de tapa y tobogán", GENERAL),
    "5.7": ("5.7 Video Jet", GENERAL),
    "5.8": ("5.8 Banda de sujeción y roscadores", GENERAL),
    "5.9": ("5.9 Sistema de etiquetado", GENERAL),
    "5.10": ("5.10 Purga de color", GENERAL),
    "5.11": ("5.11 Lavado de boquilla", GENERAL),
}

SUBCODIGO_ALIAS = {
    "1.4.3": "1.4.C",
    "1.7.A CAMBIO DE ROSCADORES": "1.7.B",
    "4.1": "5.1",
    "4.2": "5.2",
    "4.3": "5.3",
    "4.4": "5.5",
    "4.5": "5.6",
    "4.6": "5.7",
    "4.7": "5.8",
    "4.8": "5.9",
}

TIPOS_NO_OPERACION = {
    "17. PARO DE MAQUINA": ("Paro de máquina por ventas", "Comercial"),
    "[18] PARO DE MAQUINA POR VENTAS": ("Paro de máquina por ventas", "Comercial"),
    "9.FALTA DE PROGRAMACION (PLANEACION)": ("Falta de programación", "Planeación"),
    "16. PARO POR PROCESO ANTERIOR": ("Paro por proceso anterior", "Producción"),
    "10. PARO POR MATERIA PRIMA O MATERIAL DE EMPAQUE NO CONFORME": ("Materia prima o empaque no conforme", "Calidad"),
    "[12] MATERIA PRIMA DEFECTUOSA O MATERIAL DE EMPAQUE NO CONFORME": ("Materia prima o empaque no conforme", "Calidad"),
    "6. FALTA DE MATERIALES O MATERIAS PRIMAS": ("Falta de materia prima", "Materiales"),
    "[14] FALTA DE MATERIA PRIMA": ("Falta de materia prima", "Materiales"),
    "15. APROBACION DE LABORATORIO (MICROBIOLOGIA)": ("Espera de aval del laboratorio", "Calidad"),
    "[13] EN ESPERA POR EL AVAL DEL LABORATORIO DE MICROBIOLOGIA": ("Espera de aval del laboratorio", "Calidad"),
    "5. AISLAMIENTO/CAMBIO DE PRODUCTO": ("Alistamiento / cambio de referencia", "Producción"),
    "[07] ALISTAMIENTO DE MAQUINA / CAMBIO DE REFERENCIA": ("Alistamiento / cambio de referencia", "Producción"),
    "3. AJUSTE ELECTRICO O DE SERVICIOS (AIRE, CALDERA, GAS)": ("Novedad en sistemas de potencia", "Mantenimiento"),
    "[03] NOVEDAD EN LOS SISTEMAS DE POTENCIA (AIRE, ENERGIA, VAPOR)": ("Novedad en sistemas de potencia", "Mantenimiento"),
    "11. LIMPIEZA NO PROGRAMADA": ("Limpieza no programada", "Producción"),
    "4.AJUSTE DE OPERACION": ("Ajuste operativo", "Producción"),
    "[05] AJUSTE OPERATIVO": ("Ajuste operativo", "Producción"),
    "[09] FALTA DE OPERARIO": ("Falta de operario", "Producción"),
}
TIPO_SIN_CLASIFICAR = ("Sin clasificar", "Sin clasificar")

MOTIVO_CORRECCIONES = {
    "FALTADE": "FALTA DE",
    "PROGRAMOS": "PROGRAMO",
    "RESESO": "RECESO",
    "PROBEDOR": "PROVEEDOR",
    "EMERGETICA": "ENERGETICA",
    "SE CAMBIO DE REFERENCIA": "CAMBIO DE REFERENCIA",
}

TABLAS_ESTANDAR = {
    "Tabla8": (124, 178),
    "Tabla14": (179, 183),
    "Tabla15": (184, 227),
    "Tabla16": (228, 262),
}
