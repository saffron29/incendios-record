"""Parámetros compartidos por todos los pasos del análisis.

En este archivo se concentran las decisiones de método (años, fecha de corte, sensor y CRS),
de modo que cualquier modificación de estas se realice en un solo lugar.
"""
import sys
from pathlib import Path

# Se configura la salida en UTF-8, ya que la consola de Windows utiliza cp1252 y no imprime
# caracteres como «≥» o «·»
sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parents[1]
RAW = RAIZ / "data" / "raw"
PROC = RAIZ / "data" / "processed"
FIG = RAIZ / "outputs" / "figuras"
TAB = RAIZ / "outputs" / "tablas"
DOCS = RAIZ / "docs"

for carpeta in (RAW, PROC, FIG, TAB, DOCS):
    carpeta.mkdir(parents=True, exist_ok=True)

# --- la pregunta ---------------------------------------------------------------
ANIOS_BASE = list(range(2012, 2026))   # 2012-2025: la serie histórica
ANIO_OBJETIVO = 2026

# Ventana comparable: del 1 de enero al día de corte, es decir, el mismo tramo en todos los
# años. Considerando que 2026 todavía no termina, compararlo con años completos lo sesgaría
# hacia abajo.
CORTE_MES, CORTE_DIA = 10, 20          # último día completo en los datos INPE (UTC)

# --- el sensor -----------------------------------------------------------------
# Se utiliza solo VIIRS a bordo de Suomi-NPP, ya que es el único sensor de 375 m que observa
# todos los años desde 2012. Sumar NOAA-20 (2018) o NOAA-21 (2023) inflaría artificialmente
# los años recientes.
# Cabe resaltar que en INPE el mismo sensor aparece con dos etiquetas: «NPP-375» corresponde
# a los pasos diurnos (17-19 h UTC, órbita ascendente) y «NPP-375D» a los nocturnos (5-7 h
# UTC, descendente). Considerando que FIRMS incluye ambos, se suman para que 2026 sea
# comparable con 2012-2025.
SATELITES_INPE = ("NPP-375", "NPP-375D")

# Rectángulo que contiene al Perú (lon_min, lat_min, lon_max, lat_max)
BBOX_PERU = (-81.5, -18.5, -68.5, 0.1)

# CRS métrico para áreas y distancias en el Perú (el mismo utilizado en la clase de ráster)
CRS_METRICO = 24891
