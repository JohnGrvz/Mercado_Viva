import os

UMBRAL_SEGURIDAD = int(os.getenv("UMBRAL_SEGURIDAD", "2"))
RESERVA_TTL_SEGUNDOS = int(os.getenv("RESERVA_TTL_SEGUNDOS", "600"))
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://viva:viva@localhost:5432/mercado_viva",
)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
SQLITE_FALLBACK = "sqlite:///./mercado_viva.db"
