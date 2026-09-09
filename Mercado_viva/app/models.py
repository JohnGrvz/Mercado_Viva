from typing import List, Optional
from pydantic import BaseModel
from sqlmodel import SQLModel, Field

# Entidad de Base de Datos / Inventario
class ProductoBase(SQLModel):
    id: int = Field(primary_key=True)
    nombre: str
    stock_fisico: int
    pasillo: str

class Producto(ProductoBase, table=True):
    alternativas_ids: str = "" # IDs separados por coma (ej: "102,103")

# Esquemas DTO para API
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
    producto_rechazado_id: Optional[int] = None
    sustitutos_disponibles: Optional[List[DetalleSustitutoDTO]] = None

class PedidoConfirmadoDTO(BaseModel):
    orden_id: str
    estado: str
    items: List[ItemCarritoDTO]