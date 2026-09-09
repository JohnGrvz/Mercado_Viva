from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from app.models import Producto, SolicitudVerificacionDTO, ResultadoVerificacionDTO, PedidoConfirmadoDTO
from app.services import InventarioService

app = FastAPI(
    title="Mercado Viva - Middleware API",
    version="1.0.0",
    description="Backend en Python/FastAPI para validación de inventario omnicanal y gestión de eventos."
)

# Configuración CORS para conectar con el Frontend web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/productos", response_model=List[Producto])
def obtener_catalogo():
    return InventarioService.obtener_catalogo()

@app.post("/api/v1/inventario/verificar-lote", response_model=ResultadoVerificacionDTO)
def verificar_lote(solicitud: SolicitudVerificacionDTO):
    return InventarioService.verificar_lote(solicitud)

@app.post("/api/v1/pedidos/confirmar", response_model=PedidoConfirmadoDTO, status_code=status.HTTP_201_CREATED)
def confirmar_pedido(solicitud: SolicitudVerificacionDTO):
    # Re-validación estricta antes de confirmar
    resultado = InventarioService.verificar_lote(solicitud)
    if not resultado.aprobado:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=resultado.mensaje
        )
    
    orden_id = InventarioService.procesar_reserva_y_notificar(solicitud)
    
    return PedidoConfirmadoDTO(
        orden_id=orden_id,
        estado="Stock Reservado - Notificado a Picking",
        items=solicitud.items
    )