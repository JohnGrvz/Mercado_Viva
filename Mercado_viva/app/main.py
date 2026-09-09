from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import UMBRAL_SEGURIDAD, RESERVA_TTL_SEGUNDOS
from app.models import (
    Producto,
    SolicitudVerificacionDTO,
    ResultadoVerificacionDTO,
    PedidoConfirmadoDTO,
    InfraEstadoDTO,
)
from app.services import InventarioService
from app.db import init_db, postgres_ok
from app import cache, broker


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Mercado Viva - Middleware API",
    version="1.0.0",
    description="Middleware de inventario con PostgreSQL, Redis y RabbitMQ.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/api/v1/productos", response_model=List[Producto])
def obtener_catalogo():
    return InventarioService.obtener_catalogo()


@app.post("/api/v1/inventario/verificar-lote", response_model=ResultadoVerificacionDTO)
def verificar_lote(solicitud: SolicitudVerificacionDTO):
    return InventarioService.verificar_lote(solicitud)


@app.post("/api/v1/pedidos/confirmar", response_model=PedidoConfirmadoDTO, status_code=status.HTTP_201_CREATED)
def confirmar_pedido(solicitud: SolicitudVerificacionDTO):
    resultado = InventarioService.verificar_lote(solicitud, bloquear=False, considerar_reservas=False)
    if not resultado.aprobado:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=resultado.mensaje,
        )

    pedido = InventarioService.procesar_reserva_y_notificar(solicitud)
    return PedidoConfirmadoDTO(
        orden_id=pedido["orden_id"],
        estado="Stock Reservado - Notificado a Picking",
        items=pedido["items"],
    )


@app.get("/api/v1/pedidos", response_model=List[PedidoConfirmadoDTO])
def listar_pedidos():
    return [
        PedidoConfirmadoDTO(
            orden_id=p["orden_id"],
            estado=p["estado"],
            items=p["items"],
        )
        for p in InventarioService.obtener_pedidos()
    ]


@app.get("/api/v1/infra", response_model=InfraEstadoDTO)
def estado_infra():
    return InfraEstadoDTO(
        postgres=postgres_ok(),
        redis=cache.ping(),
        rabbitmq=broker.ping(),
        umbral_seguridad=UMBRAL_SEGURIDAD,
        reserva_ttl_segundos=RESERVA_TTL_SEGUNDOS,
    )
