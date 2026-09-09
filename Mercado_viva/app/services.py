import time
import logging
from typing import List, Dict, Any, Tuple
from sqlmodel import select
from app.config import UMBRAL_SEGURIDAD
from app.db import get_session
from app import cache, broker
from app.models import (
    Producto,
    Pedido,
    ItemPedido,
    SolicitudVerificacionDTO,
    ResultadoVerificacionDTO,
    DetalleSustitutoDTO,
    PedidoItemDTO,
)

logger = logging.getLogger("Middleware-Events")


class InventarioService:

    @staticmethod
    def obtener_catalogo() -> List[Producto]:
        with get_session() as session:
            productos = session.exec(select(Producto).order_by(Producto.id)).all()
            resultado = []
            for prod in productos:
                stock, _fuente = InventarioService._stock(prod)
                resultado.append(
                    Producto(
                        id=prod.id,
                        nombre=prod.nombre,
                        stock_fisico=stock,
                        pasillo=prod.pasillo,
                        alternativas_ids=prod.alternativas_ids,
                    )
                )
            return resultado

    @staticmethod
    def verificar_lote(
        solicitud: SolicitudVerificacionDTO,
        bloquear: bool = True,
        considerar_reservas: bool = True,
    ) -> ResultadoVerificacionDTO:
        t_inicio = time.perf_counter()
        fuente = "postgres"

        with get_session() as session:
            for item in solicitud.items:
                prod = session.get(Producto, item.id)
                if not prod:
                    return ResultadoVerificacionDTO(
                        aprobado=False,
                        mensaje=f"Producto ID {item.id} no existe en catálogo.",
                        latencia_ms=_latencia(t_inicio),
                    )

                stock, fuente = InventarioService._stock(prod)
                reservado = cache.leer_reserva(prod.id) if considerar_reservas else 0
                resultante = stock - reservado - item.cantidad

                if resultante <= UMBRAL_SEGURIDAD:
                    logger.warning(
                        "[HU-02 RECHAZADO] '%s' dejaría stock en %s (<= umbral %s).",
                        prod.nombre,
                        resultante,
                        UMBRAL_SEGURIDAD,
                    )
                    return ResultadoVerificacionDTO(
                        aprobado=False,
                        mensaje=f"Producto no disponible para domicilio: '{prod.nombre}'.",
                        latencia_ms=_latencia(t_inicio),
                        fuente_stock=fuente,
                        producto_rechazado_id=prod.id,
                        sustitutos_disponibles=InventarioService._obtener_sustitutos(session, prod),
                    )

            if bloquear:
                for item in solicitud.items:
                    cache.reservar(item.id, item.cantidad)

        logger.info("[HU-02 APROBADO] Lote verificado en %s en %s ms (RNF-01).", fuente, _latencia(t_inicio))
        return ResultadoVerificacionDTO(
            aprobado=True,
            mensaje="Reserva de stock autorizada.",
            latencia_ms=_latencia(t_inicio),
            fuente_stock=fuente,
        )

    @staticmethod
    def procesar_reserva_y_notificar(solicitud: SolicitudVerificacionDTO) -> Dict[str, Any]:
        items_detalle: List[PedidoItemDTO] = []
        stocks_finales: Dict[int, int] = {}

        with get_session() as session:
            for item in solicitud.items:
                prod = session.get(Producto, item.id)
                nuevo_stock = prod.stock_fisico - item.cantidad
                prod.stock_fisico = nuevo_stock
                session.add(prod)
                stocks_finales[prod.id] = nuevo_stock
                items_detalle.append(
                    PedidoItemDTO(
                        id=prod.id,
                        nombre=prod.nombre,
                        cantidad=item.cantidad,
                        pasillo=prod.pasillo,
                    )
                )

            orden_id = f"ORD-{int(time.time() * 1000) % 8999 + 1000}"
            session.add(Pedido(orden_id=orden_id, estado="Stock Reservado"))
            session.flush()
            for det in items_detalle:
                session.add(
                    ItemPedido(
                        orden_id=orden_id,
                        producto_id=det.id,
                        nombre=det.nombre,
                        cantidad=det.cantidad,
                        pasillo=det.pasillo,
                    )
                )
            session.commit()

        for det in items_detalle:
            cache.escribir_stock(det.id, stocks_finales[det.id])
            cache.liberar_reserva(det.id, det.cantidad)

        payload = {
            "orden_id": orden_id,
            "items": [item.model_dump() for item in items_detalle],
        }
        broker.publicar("inventario.descontado", payload)
        broker.publicar("picking.ordenes", payload)
        logger.info("[HU-04 EVENTO] LoteInventarioDescontado para %s.", orden_id)
        logger.info("[HU-05 PICKING] OrdenListaParaRecoleccion enrutada a cola de picking.")

        return {
            "orden_id": orden_id,
            "estado": "Stock Reservado",
            "items": items_detalle,
        }

    @staticmethod
    def obtener_pedidos() -> List[Dict[str, Any]]:
        with get_session() as session:
            pedidos = session.exec(select(Pedido)).all()
            resultado = []
            for pedido in pedidos:
                items = session.exec(select(ItemPedido).where(ItemPedido.orden_id == pedido.orden_id)).all()
                resultado.append(
                    {
                        "orden_id": pedido.orden_id,
                        "estado": pedido.estado,
                        "items": [
                            PedidoItemDTO(
                                id=item.producto_id,
                                nombre=item.nombre,
                                cantidad=item.cantidad,
                                pasillo=item.pasillo,
                            )
                            for item in items
                        ],
                    }
                )
            resultado.sort(key=lambda p: p["orden_id"], reverse=True)
            return resultado

    @staticmethod
    def _stock(producto: Producto) -> Tuple[int, str]:
        cached = cache.leer_stock(producto.id)
        if cached is not None:
            return cached, "redis"
        cache.escribir_stock(producto.id, producto.stock_fisico)
        return producto.stock_fisico, "postgres"

    @staticmethod
    def _obtener_sustitutos(session, producto: Producto) -> List[DetalleSustitutoDTO]:
        if not producto.alternativas_ids:
            return []
        ids = [int(i.strip()) for i in producto.alternativas_ids.split(",") if i.strip()]
        sustitutos = []
        for alt_id in ids:
            alt = session.get(Producto, alt_id)
            if alt:
                stock, _ = InventarioService._stock(alt)
                sustitutos.append(DetalleSustitutoDTO(id=alt.id, nombre=alt.nombre, stock_fisico=stock))
        return sustitutos


def _latencia(t_inicio: float) -> float:
    return round((time.perf_counter() - t_inicio) * 1000, 2)
