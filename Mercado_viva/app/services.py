import time
import logging
from typing import List, Tuple
from app.database import INVENTARIO_BD, UMBRAL_SEGURIDAD
from app.models import SolicitudVerificacionDTO, ResultadoVerificacionDTO, DetalleSustitutoDTO, Producto

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Middleware-Events")

class InventarioService:

    @staticmethod
    def obtener_catalogo() -> List[Producto]:
        return list(INVENTARIO_BD.values())

    @staticmethod
    def verificar_lote(solicitud: SolicitudVerificacionDTO) -> ResultadoVerificacionDTO:
        t_inicio = time.perf_counter()

        for item in solicitud.items:
            prod_bd = INVENTARIO_BD.get(item.id)
            
            if not prod_bd:
                latencia = round((time.perf_counter() - t_inicio) * 1000, 2)
                return ResultadoVerificacionDTO(
                    aprobado=False,
                    mensaje=f"Producto ID {item.id} no existe en catálogo.",
                    latencia_ms=latencia
                )

            # Regla HU-02: El stock restante tras la compra debe ser superior al umbral
            stock_resultante = prod_bd.stock_fisico - item.cantidad
            
            if stock_resultante <= UMBRAL_SEGURIDAD:
                latencia = round((time.perf_counter() - t_inicio) * 1000, 2)
                logger.warning(
                    f"[HU-02 RECHAZADO] Producto '{prod_bd.nombre}' dejaría stock en {stock_resultante} "
                    f"(<= Umbral de seguridad {UMBRAL_SEGURIDAD})."
                )
                
                # Cargar alternativas para HU-03
                sustitutos = InventarioService._obtener_sustitutos(prod_bd)
                
                return ResultadoVerificacionDTO(
                    aprobado=False,
                    mensaje=f"El producto '{prod_bd.nombre}' excede el límite permitido para venta digital.",
                    latencia_ms=latencia,
                    producto_rechazado_id=prod_bd.id,
                    sustitutos_disponibles=sustitutos
                )

        latencia = round((time.perf_counter() - t_inicio) * 1000, 2)
        logger.info(f"[HU-02 APROBADO] Lote verificado correctamente en Redis/BD en {latencia} ms (RNF-01).")
        
        return ResultadoVerificacionDTO(
            aprobado=True,
            mensaje="Reserva de stock autorizada.",
            latencia_ms=latencia
        )

    @staticmethod
    def procesar_reserva_y_notificar(solicitud: SolicitudVerificacionDTO) -> str:
        # HU-04: Sincronización e impacto directo en base de datos / Redis
        for item in solicitud.items:
            prod_bd = INVENTARIO_BD[item.id]
            prod_bd.stock_fisico -= item.cantidad
            
        orden_id = f"ORD-{int(time.time() * 1000) % 8999 + 1000}"
        
        # HU-04 & HU-05: Publicación de evento en Broker de Mensajería (RabbitMQ)
        logger.info(f"[HU-04 EVENTO] Evento 'LoteInventarioDescontado' emitido a RabbitMQ para la Orden #{orden_id}.")
        logger.info(f"[HU-05 PICKING] Evento 'OrdenListaParaRecoleccion' enrutado a cola de Picking.")
        
        return orden_id

    @staticmethod
    def _obtener_sustitutos(producto: Producto) -> List[DetalleSustitutoDTO]:
        if not producto.alternativas_ids:
            return []
        
        ids = [int(i.strip()) for i in producto.alternativas_ids.split(",") if i.strip()]
        sustitutos = []
        for alt_id in ids:
            alt = INVENTARIO_BD.get(alt_id)
            if alt:
                sustitutos.append(DetalleSustitutoDTO(
                    id=alt.id,
                    nombre=alt.nombre,
                    stock_fisico=alt.stock_fisico
                ))
        return sustitutos