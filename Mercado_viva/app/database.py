from typing import Dict, List
from app.models import Producto

# Parámetro global del Middleware
UMBRAL_SEGURIDAD = 2

# Base de datos en memoria para la demo
INVENTARIO_BD: Dict[int, Producto] = {
    101: Producto(id=101, nombre="Leche Entera Viva 1L", stock_fisico=5, pasillo="Pasillo 1 - Estante A", alternativas_ids="102,103"),
    102: Producto(id=102, nombre="Leche Deslactosada Viva 1L", stock_fisico=8, pasillo="Pasillo 1 - Estante A", alternativas_ids=""),
    103: Producto(id=103, nombre="Leche Almendras 1L", stock_fisico=4, pasillo="Pasillo 1 - Estante B", alternativas_ids=""),
    201: Producto(id=201, nombre="Arroz Premium 1Kg", stock_fisico=3, pasillo="Pasillo 3 - Estante C", alternativas_ids="202"),
    202: Producto(id=202, nombre="Arroz Integral 1Kg", stock_fisico=6, pasillo="Pasillo 3 - Estante C", alternativas_ids="")
}