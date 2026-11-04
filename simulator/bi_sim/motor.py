"""Motor de simulacion: genera la lectura de una hora de produccion de una maquina.

No toca la base de datos ni el reloj: recibe un perfil calibrado con los datos historicos,
un generador aleatorio y la hora que se simula. Asi se puede probar y reproducir con una semilla.

La fuente no registra eventos, solo los minutos de cada codigo por turno. Por eso la
duracion de un evento individual es un SUPUESTO (MEDIA_EVENTO_MIN y MEDIA_FALLA_MIN). La
frecuencia de cada evento se calcula para que, en promedio, los minutos de paro por hora
trabajada coincidan con los de la historia de la maquina.

Todas las duraciones se manejan en decimas de minuto (enteros) para que las sumas sean
exactas y cumplan las restricciones de la tabla ops.lectura_hora.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime

DECIMAS_POR_HORA = 600

MEDIA_EVENTO_MIN = 8.0
MEDIA_FALLA_MIN = 25.0
MIN_EVENTO_DECIMAS = 5
PROBABILIDAD_MAXIMA = 0.95

RENDIMIENTO_SD = 0.10
RENDIMIENTO_MIN = 0.20
RENDIMIENTO_MAX = 1.25

FACTOR_DEGRADADO_PAROS = 2.0
FACTOR_DEGRADADO_RENDIMIENTO = 0.85
FALLA_DECIMAS = (300, 550)

MODOS = ("normal", "degradado", "falla")

_TURNOS = (
    (6, 14, "6am-2pm (Turno 1)"),
    (14, 22, "2pm-10pm (Turno 2)"),
    (22, 6, "10pm-6am (Turno 3)"),
)


def turno_de(hora: int) -> str:
    for inicio, fin, nombre in _TURNOS:
        if inicio < fin and inicio <= hora < fin:
            return nombre
        if inicio > fin and (hora >= inicio or hora < fin):
            return nombre
    raise ValueError(f"Hora fuera de rango: {hora}")


@dataclass(frozen=True)
class Causa:
    codigo: int
    nombre: str
    sistema: str
    subcodigo: str
    programado: bool
    es_falla: bool
    tasa: float  # minutos de paro por hora trabajada, segun la historia


@dataclass(frozen=True)
class Referencia:
    nombre: str
    unidades_por_minuto: float
    peso: float


@dataclass(frozen=True)
class Perfil:
    maquina: str
    causas: tuple[Causa, ...]
    referencias: tuple[Referencia, ...]
    rendimiento_medio: float


@dataclass
class Orden:
    """Referencia que la maquina produce en este momento y horas que le quedan."""

    referencia: Referencia | None = None
    horas_restantes: int = 0


@dataclass(frozen=True)
class Paro:
    causa: Causa
    minutos: float


@dataclass(frozen=True)
class Lectura:
    maquina: str
    hora_simulada: datetime
    turno: str
    referencia: str
    escenario: str
    minutos_programados: float
    minutos_planificados: float
    minutos_no_programados: float
    minutos_operativos: float
    unidades_teoricas: float
    unidades_producidas: float
    paros: tuple[Paro, ...] = field(default_factory=tuple)

    @property
    def disponibilidad(self) -> float | None:
        return self.minutos_operativos / self.minutos_planificados if self.minutos_planificados else None


FALLA_GENERICA = Causa(
    codigo=1,
    nombre="[01] Falla del sistema electromecánico y/o de control",
    sistema="Sin especificar",
    subcodigo="Sin especificar",
    programado=False,
    es_falla=True,
    tasa=0.0,
)


def _asegurar_orden(perfil: Perfil, orden: Orden, rng: random.Random) -> Referencia:
    if orden.referencia is None or orden.horas_restantes <= 0:
        pesos = [r.peso for r in perfil.referencias]
        orden.referencia = rng.choices(perfil.referencias, weights=pesos)[0]
        orden.horas_restantes = rng.randint(24, 72)
    orden.horas_restantes -= 1
    return orden.referencia


def _sortear_evento(causa: Causa, factor: float, tope: int, rng: random.Random) -> int:
    """Decimas de minuto que dura el evento de esta causa en la hora, o 0 si no ocurre."""
    if tope <= 0:
        return 0
    media = MEDIA_FALLA_MIN if causa.es_falla else MEDIA_EVENTO_MIN
    probabilidad = min(PROBABILIDAD_MAXIMA, causa.tasa * factor / media)
    if rng.random() >= probabilidad:
        return 0
    duracion = int(round(rng.expovariate(1.0 / media) * 10))
    return min(max(duracion, MIN_EVENTO_DECIMAS), tope)


def _falla_forzada(perfil: Perfil, rng: random.Random) -> Causa:
    candidatas = [c for c in perfil.causas if c.es_falla and not c.programado]
    if not candidatas:
        return FALLA_GENERICA
    return rng.choices(candidatas, weights=[c.tasa for c in candidatas])[0]


def generar_lectura(perfil: Perfil, orden: Orden, modo: str, hora: datetime, rng: random.Random) -> Lectura:
    if modo not in MODOS:
        raise ValueError(f"Modo desconocido: {modo}")
    referencia = _asegurar_orden(perfil, orden, rng)
    paros: list[tuple[Causa, int]] = []

    # Primero los paros programados: reducen el tiempo planificado.
    programados = 0
    for causa in (c for c in perfil.causas if c.programado):
        decimas = _sortear_evento(causa, 1.0, DECIMAS_POR_HORA - programados, rng)
        if decimas:
            paros.append((causa, decimas))
            programados += decimas
    planificado = DECIMAS_POR_HORA - programados

    # Luego los no programados, que no pueden exceder el tiempo planificado.
    no_programados = 0
    if modo == "falla":
        decimas = min(rng.randint(*FALLA_DECIMAS), planificado)
        if decimas:
            paros.append((_falla_forzada(perfil, rng), decimas))
            no_programados += decimas
    factor = FACTOR_DEGRADADO_PAROS if modo == "degradado" else 1.0
    for causa in (c for c in perfil.causas if not c.programado):
        decimas = _sortear_evento(causa, factor, planificado - no_programados, rng)
        if decimas:
            paros.append((causa, decimas))
            no_programados += decimas

    operativo = planificado - no_programados
    rendimiento = min(max(rng.gauss(perfil.rendimiento_medio, RENDIMIENTO_SD), RENDIMIENTO_MIN), RENDIMIENTO_MAX)
    if modo == "degradado":
        rendimiento *= FACTOR_DEGRADADO_RENDIMIENTO
    teoricas = round(operativo / 10 * referencia.unidades_por_minuto, 2)
    producidas = round(teoricas * rendimiento, 2)

    return Lectura(
        maquina=perfil.maquina,
        hora_simulada=hora,
        turno=turno_de(hora.hour),
        referencia=referencia.nombre,
        escenario=modo,
        minutos_programados=programados / 10,
        minutos_planificados=planificado / 10,
        minutos_no_programados=no_programados / 10,
        minutos_operativos=operativo / 10,
        unidades_teoricas=teoricas,
        unidades_producidas=producidas,
        paros=tuple(Paro(causa, decimas / 10) for causa, decimas in paros),
    )
