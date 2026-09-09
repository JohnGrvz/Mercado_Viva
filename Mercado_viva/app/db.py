import logging
from sqlmodel import Session, SQLModel, create_engine, select
from app.config import DATABASE_URL, SQLITE_FALLBACK
from app.models import ItemPedido, Pedido, Producto

_ = (Pedido, ItemPedido)

logger = logging.getLogger("Middleware-Events")

engine = create_engine(DATABASE_URL, echo=False)
usando_sqlite = False

SEED_PRODUCTOS = [
    Producto(id=101, nombre="Leche Entera Viva 1L", stock_fisico=5, pasillo="Pasillo 1 - Estante A", alternativas_ids="102,103"),
    Producto(id=102, nombre="Leche Deslactosada Viva 1L", stock_fisico=8, pasillo="Pasillo 1 - Estante A", alternativas_ids=""),
    Producto(id=103, nombre="Leche Almendras 1L", stock_fisico=4, pasillo="Pasillo 1 - Estante B", alternativas_ids=""),
    Producto(id=201, nombre="Arroz Premium 1Kg", stock_fisico=3, pasillo="Pasillo 3 - Estante C", alternativas_ids="202"),
    Producto(id=202, nombre="Arroz Integral 1Kg", stock_fisico=6, pasillo="Pasillo 3 - Estante C", alternativas_ids=""),
]


def get_session() -> Session:
    return Session(engine)


def postgres_ok() -> bool:
    try:
        with get_session() as session:
            session.exec(select(Producto).limit(1)).first()
        return not usando_sqlite
    except Exception:
        return False


def init_db() -> None:
    global engine, usando_sqlite
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        logger.info("[POSTGRES] Conectado a %s", DATABASE_URL.split("@")[-1])
    except Exception as exc:
        usando_sqlite = True
        engine = create_engine(SQLITE_FALLBACK, echo=False, connect_args={"check_same_thread": False})
        logger.warning("[POSTGRES] No disponible (%s). Usando SQLite local.", exc)

    SQLModel.metadata.create_all(engine)
    _seed()


def _seed() -> None:
    with get_session() as session:
        if session.get(Producto, 101):
            return
        for producto in SEED_PRODUCTOS:
            session.add(producto)
        session.commit()
        logger.info("[POSTGRES] Catálogo semilla cargado.")
