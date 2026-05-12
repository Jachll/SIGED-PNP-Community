from dataclasses import dataclass
from datetime import date, datetime
from math import ceil

from fastapi import HTTPException

from app.observability import observe_operation
from app.repositories.recomendaciones_repository import (
    fetch_patrol_recommendation_candidates,
    save_patrol_recommendations,
)
from app.schemas.recomendaciones import (
    RecomendacionCriterios,
    RecomendacionMetricas,
    RecomendacionPatrullajeItem,
    RecomendacionPatrullajeResponse,
    RecomendacionRecursos,
    RecomendacionVentanaHoraria,
    RecomendacionZonaInfo,
)
from app.services.common_service import raise_query_error, validate_date_range


TURNOS_VALIDOS = {"MADRUGADA", "MANANA", "TARDE", "NOCHE"}
TURNO_A_VENTANA = {
    "MADRUGADA": ("00:00", "05:59"),
    "MANANA": ("06:00", "11:59"),
    "TARDE": ("12:00", "17:59"),
    "NOCHE": ("18:00", "23:59"),
}
PRIORIDAD_ORDEN = {"CRITICA": 4, "ALTA": 3, "MEDIA": 2, "BAJA": 1}


@dataclass(frozen=True)
class ReglaPatrullaje:
    codigo: str
    nombre: str
    prioridad: str
    tipo_recomendacion: str
    minimo_eventos_base: int
    eventos_por_dia: float
    minimo_participacion_franja: float
    minimo_indice_concentracion: float
    cantidad_efectivos: int
    cantidad_unidades: int

    def minimo_eventos(self, dias_analizados: int) -> int:
        return max(self.minimo_eventos_base, ceil(dias_analizados * self.eventos_por_dia))


REGLAS_PATRULLAJE = [
    ReglaPatrullaje(
        codigo="R1_REFUERZO_CRITICO",
        nombre="Refuerzo critico focalizado",
        prioridad="CRITICA",
        tipo_recomendacion="INTERVENCION_FOCALIZADA",
        minimo_eventos_base=6,
        eventos_por_dia=0.80,
        minimo_participacion_franja=0.40,
        minimo_indice_concentracion=1.35,
        cantidad_efectivos=6,
        cantidad_unidades=2,
    ),
    ReglaPatrullaje(
        codigo="R2_PATRULLAJE_DISUASIVO",
        nombre="Patrullaje disuasivo reforzado",
        prioridad="ALTA",
        tipo_recomendacion="PATRULLAJE_DISUASIVO",
        minimo_eventos_base=4,
        eventos_por_dia=0.50,
        minimo_participacion_franja=0.30,
        minimo_indice_concentracion=1.20,
        cantidad_efectivos=4,
        cantidad_unidades=1,
    ),
    ReglaPatrullaje(
        codigo="R3_PATRULLAJE_PREVENTIVO",
        nombre="Patrullaje preventivo focalizado",
        prioridad="MEDIA",
        tipo_recomendacion="PATRULLAJE_PREVENTIVO",
        minimo_eventos_base=3,
        eventos_por_dia=0.30,
        minimo_participacion_franja=0.25,
        minimo_indice_concentracion=1.10,
        cantidad_efectivos=2,
        cantidad_unidades=1,
    ),
]


def generate_patrol_recommendations(
    fecha_inicio: date | None,
    fecha_fin: date | None,
    fecha_operativa: date | None,
    id_delito: int | None,
    distrito: str | None,
    id_comisaria: int | None,
    region: str | None,
    division: str | None,
    comisaria: str | None,
    jurisdiccion: str | None,
    sector: str | None,
    turno: str | None,
    limite: int,
    guardar: bool,
) -> RecomendacionPatrullajeResponse:
    validate_date_range(fecha_inicio, fecha_fin)
    turno_normalizado = _normalize_turno(turno)
    fecha_operativa_final = fecha_operativa or date.today()
    fecha_generacion = datetime.now()
    candidate_limit = max(limite * 6, 50)

    try:
        with observe_operation(
            "recomendaciones.patrullaje",
            details={
                "limite": limite,
                "candidate_limit": candidate_limit,
                "turno": turno_normalizado,
                "distrito": distrito,
                "id_delito": id_delito,
                "id_comisaria": id_comisaria,
                "region": region,
                "division": division,
                "comisaria": comisaria,
                "jurisdiccion": jurisdiccion,
                "sector": sector,
                "guardar": guardar,
            },
        ):
            try:
                rows = fetch_patrol_recommendation_candidates(
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    id_delito=id_delito,
                    distrito=distrito,
                    id_comisaria=id_comisaria,
                    region=region,
                    division=division,
                    comisaria=comisaria,
                    jurisdiccion=jurisdiccion,
                    sector=sector,
                    turno=turno_normalizado,
                    limite=candidate_limit,
                )
            except Exception as exc:
                raise_query_error("candidatos de recomendaciones de patrullaje", exc)

            recomendaciones = [
                recomendacion
                for row in rows
                if (recomendacion := _build_recommendation(row, fecha_generacion, fecha_operativa_final))
                is not None
            ]

            recomendaciones.sort(
                key=lambda item: (
                    PRIORIDAD_ORDEN.get(item.prioridad, 0),
                    item.metricas.total_eventos_franja,
                    item.metricas.indice_concentracion,
                ),
                reverse=True,
            )
            recomendaciones = recomendaciones[:limite]

            if guardar and recomendaciones:
                try:
                    inserted_ids = save_patrol_recommendations(
                        [_serialize_recommendation_for_storage(item) for item in recomendaciones]
                    )
                except RuntimeError as exc:
                    raise HTTPException(
                        status_code=503,
                        detail="La persistencia de recomendaciones no esta disponible en este entorno.",
                    ) from exc
                except Exception as exc:
                    raise_query_error("persistencia de recomendaciones de patrullaje", exc)

                for recommendation, inserted_id in zip(recomendaciones, inserted_ids):
                    recommendation.id_recomendacion = inserted_id
                    recommendation.persistida = True

            if recomendaciones:
                periodo_inicio_respuesta = recomendaciones[0].periodo_inicio
                periodo_fin_respuesta = recomendaciones[0].periodo_fin
            elif rows:
                periodo_inicio_respuesta = rows[0]["periodo_inicio"]
                periodo_fin_respuesta = rows[0]["periodo_fin"]
            else:
                periodo_inicio_respuesta = fecha_inicio
                periodo_fin_respuesta = fecha_fin

            return RecomendacionPatrullajeResponse(
                fecha_generacion=fecha_generacion,
                fecha_operativa=fecha_operativa_final,
                periodo_inicio=periodo_inicio_respuesta,
                periodo_fin=periodo_fin_respuesta,
                total_recomendaciones=len(recomendaciones),
                reglas_evaluadas=[f"{regla.codigo}: {regla.nombre}" for regla in REGLAS_PATRULLAJE],
                recomendaciones=recomendaciones,
            )
    except HTTPException:
        raise


def _normalize_turno(turno: str | None) -> str | None:
    if turno is None:
        return None

    turno_normalizado = turno.strip().upper()
    if turno_normalizado not in TURNOS_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"turno invalido. Usa uno de: {', '.join(sorted(TURNOS_VALIDOS))}",
        )

    return turno_normalizado


def _build_recommendation(
    row: dict,
    fecha_generacion: datetime,
    fecha_operativa: date,
) -> RecomendacionPatrullajeItem | None:
    dias_analizados = int(row["dias_analizados"] or 0)
    if dias_analizados <= 0:
        return None

    regla = _match_rule(row, dias_analizados)
    if regla is None:
        return None

    hora_inicio, hora_fin = TURNO_A_VENTANA[row["turno"]]
    total_eventos_franja = int(row["total_eventos_franja"])
    total_eventos_zona = int(row["total_eventos_zona"])
    participacion_franja = float(row["participacion_franja"])
    promedio_diario_franja = float(row["promedio_diario_franja"])
    indice_concentracion = float(row["indice_concentracion"])
    minimo_eventos = regla.minimo_eventos(dias_analizados)

    nombre_zona = row["nombre_zona"]
    distrito = row["distrito"]
    turno = row["turno"]

    detalle_operativo = (
        f"Programar {regla.tipo_recomendacion} en {nombre_zona} ({distrito}) durante {turno} "
        f"de {hora_inicio} a {hora_fin}, reforzando presencia visible y recorrido preventivo."
    )

    justificacion = [
        (
            f"La zona {nombre_zona} acumula {total_eventos_franja} eventos en la franja {turno}, "
            f"superando el umbral de {minimo_eventos} para la regla {regla.codigo}."
        ),
        (
            f"La franja concentra {participacion_franja:.1%} del total de {total_eventos_zona} eventos "
            f"registrados en la zona durante el periodo analizado."
        ),
        (
            f"La concentracion de la franja es {indice_concentracion:.2f} veces el promedio esperado por "
            f"franja en la zona, con {promedio_diario_franja:.2f} eventos por dia."
        ),
    ]

    return RecomendacionPatrullajeItem(
        origen_datos=row["origen_datos"],
        regla_codigo=regla.codigo,
        regla_nombre=regla.nombre,
        prioridad=regla.prioridad,
        tipo_recomendacion=regla.tipo_recomendacion,
        fecha_generacion=fecha_generacion,
        fecha_operativa=fecha_operativa,
        periodo_inicio=row["periodo_inicio"],
        periodo_fin=row["periodo_fin"],
        dias_analizados=dias_analizados,
        ventana_horaria=RecomendacionVentanaHoraria(
            turno=turno,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
        ),
        zona=RecomendacionZonaInfo(
            id_zona=row["id_zona"],
            codigo_zona=row["codigo_zona"],
            nombre_zona=nombre_zona,
            tipo_zona=row["tipo_zona"],
            distrito=distrito,
            id_comisaria=row["id_comisaria"],
            nombre_comisaria=row["nombre_comisaria"],
            latitud=float(row["latitud"]),
            longitud=float(row["longitud"]),
        ),
        metricas=RecomendacionMetricas(
            total_eventos_franja=total_eventos_franja,
            total_eventos_zona=total_eventos_zona,
            promedio_diario_franja=promedio_diario_franja,
            participacion_franja=participacion_franja,
            indice_concentracion=indice_concentracion,
        ),
        criterios_regla=RecomendacionCriterios(
            minimo_eventos=minimo_eventos,
            minimo_participacion_franja=regla.minimo_participacion_franja,
            minimo_indice_concentracion=regla.minimo_indice_concentracion,
        ),
        detalle_operativo=detalle_operativo,
        justificacion=justificacion,
        recursos_sugeridos=RecomendacionRecursos(
            cantidad_efectivos=regla.cantidad_efectivos,
            cantidad_unidades=regla.cantidad_unidades,
        ),
    )


def _match_rule(row: dict, dias_analizados: int) -> ReglaPatrullaje | None:
    total_eventos_franja = int(row["total_eventos_franja"])
    participacion_franja = float(row["participacion_franja"])
    indice_concentracion = float(row["indice_concentracion"])

    for regla in REGLAS_PATRULLAJE:
        if total_eventos_franja < regla.minimo_eventos(dias_analizados):
            continue
        if participacion_franja < regla.minimo_participacion_franja:
            continue
        if indice_concentracion < regla.minimo_indice_concentracion:
            continue
        return regla

    return None


def _serialize_recommendation_for_storage(item: RecomendacionPatrullajeItem) -> dict:
    return {
        "fecha_operativa": item.fecha_operativa,
        "turno": item.ventana_horaria.turno,
        "id_hotspot": None,
        "id_zona": item.zona.id_zona,
        "id_comisaria": item.zona.id_comisaria,
        "distrito": item.zona.distrito,
        "prioridad": item.prioridad,
        "tipo_recomendacion": item.tipo_recomendacion,
        "detalle_operativo": item.detalle_operativo,
        "cantidad_efectivos": item.recursos_sugeridos.cantidad_efectivos,
        "cantidad_unidades": item.recursos_sugeridos.cantidad_unidades,
        "observaciones": " | ".join(item.justificacion),
    }
