from typing import List, Optional
from pydantic import BaseModel
from sqlmodel import SQLModel, Field


class Producto(SQLModel, table=True):
    id: int = Field(primary_key=True)
    nombre: str
    stock_fisico: int
    pasillo: str
    alternativas_ids: str = ""


class Pedido(SQLModel, table=True):
    orden_id: str = Field(primary_key=True)
    estado: str


class ItemPedido(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    orden_id: str = Field(index=True, foreign_key="pedido.orden_id")
    producto_id: int
    nombre: str
    cantidad: int
    pasillo: str


class ItemCarritoDTO(BaseModel):
    id: int
    cantidad: int


class SolicitudVerificacionDTO(BaseModel):
    items: List[ItemCarritoDTO]


class DetalleSustitutoDTO(BaseModel):
    id: int
    nombre: str
    stock_fisico: int


class ResultadoVerificacionDTO(BaseModel):
    aprobado: bool
    mensaje: str
    latencia_ms: float
    fuente_stock: str = "postgres"
    producto_rechazado_id: Optional[int] = None
    sustitutos_disponibles: Optional[List[DetalleSustitutoDTO]] = None


class PedidoItemDTO(BaseModel):
    id: int
    nombre: str
    cantidad: int
    pasillo: str


class PedidoConfirmadoDTO(BaseModel):
    orden_id: str
    estado: str
    items: List[PedidoItemDTO]


class InfraEstadoDTO(BaseModel):
    postgres: bool
    redis: bool
    rabbitmq: bool
    umbral_seguridad: int
    reserva_ttl_segundos: int
