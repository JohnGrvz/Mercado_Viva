import logging
from typing import Optional
import redis
from redis.exceptions import RedisError
from app.config import REDIS_URL, RESERVA_TTL_SEGUNDOS

logger = logging.getLogger("Middleware-Events")
_client: Optional[redis.Redis] = None


def _redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=0.4,
            socket_timeout=0.4,
        )
    return _client


def ping() -> bool:
    try:
        return bool(_redis().ping())
    except RedisError:
        return False


def leer_stock(producto_id: int) -> Optional[int]:
    try:
        valor = _redis().get(f"stock:{producto_id}")
        return int(valor) if valor is not None else None
    except RedisError:
        logger.warning("[REDIS] Caída al leer stock. Fallback a PostgreSQL (RNF-02).")
        return None


def escribir_stock(producto_id: int, cantidad: int) -> None:
    try:
        _redis().set(f"stock:{producto_id}", cantidad)
    except RedisError:
        logger.warning("[REDIS] No se pudo actualizar caché de stock:%s", producto_id)


def leer_reserva(producto_id: int) -> int:
    try:
        valor = _redis().get(f"reserva:{producto_id}")
        return int(valor) if valor else 0
    except RedisError:
        return 0


def reservar(producto_id: int, cantidad: int) -> bool:
    try:
        clave = f"reserva:{producto_id}"
        pipe = _redis().pipeline()
        pipe.incrby(clave, cantidad)
        pipe.expire(clave, RESERVA_TTL_SEGUNDOS)
        pipe.execute()
        return True
    except RedisError:
        logger.warning("[REDIS] No se pudo crear bloqueo RN-01 para producto %s.", producto_id)
        return False


def liberar_reserva(producto_id: int, cantidad: int) -> None:
    try:
        clave = f"reserva:{producto_id}"
        r = _redis()
        nuevo = r.decrby(clave, cantidad)
        if nuevo <= 0:
            r.delete(clave)
    except RedisError:
        pass
