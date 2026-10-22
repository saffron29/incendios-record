"""Paso 1 · Descargar los datos públicos (ninguno pide clave ni pago).

| Dato                         | Fuente                                         |
|------------------------------|------------------------------------------------|
| Focos VIIRS S-NPP 2012-2025  | NASA FIRMS, archivo anual por país (Perú)      |
| Focos 2026 (ene-oct)         | INPE Queimadas, CSV mensual de Sudamérica      |
| Focos últimos 7 días         | NASA FIRMS NRT, «South America 7d» (calibrar)  |
| Límites departamentales      | INEI con UBIGEO, repositorio juaneladio/peru-geojson |

FIRMS todavía no publica el archivo anual de 2026 (devuelve 404), por eso 2026 sale
de INPE, que reprocesa el mismo sensor. En 03_comparar.py se verifica que ambas
fuentes cuentan lo mismo en los días en que se traslapan.

Uso:  uv run python src/01_descargar.py
"""
import csv
import io
import sys

import requests

from config import ANIOS_BASE, BBOX_PERU, RAW

FIRMS_ANUAL = "https://firms.modaps.eosdis.nasa.gov/data/country/viirs-snpp/{a}/viirs-snpp_{a}_Peru.csv"
FIRMS_7D = ("https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/"
            "csv/SUOMI_VIIRS_C2_South_America_7d.csv")
INPE_MENSUAL = ("https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/mensal/"
                "America_Sul/focos_mensal_{ym}.csv")
GEOJSON = "https://raw.githubusercontent.com/juaneladio/peru-geojson/master/{n}"

# 2026 completo hasta octubre + septiembre 2025 para calibrar INPE contra FIRMS
MESES_INPE = [f"2026{m:02d}" for m in range(1, 11)] + ["202509"]


def bajar(url: str, destino, forzar: bool = False) -> None:
    """Descarga un archivo pequeño o mediano una sola vez (caché en disco)."""
    if destino.exists() and not forzar:
        print(f"  ya existe   {destino.name}")
        return
    r = requests.get(url, timeout=300)
    r.raise_for_status()
    destino.write_bytes(r.content)
    print(f"  descargado  {destino.name}  ({len(r.content) / 1e6:.1f} MB)")


def en_bbox(lat: float, lon: float) -> bool:
    lon_min, lat_min, lon_max, lat_max = BBOX_PERU
    return lat_min <= lat <= lat_max and lon_min <= lon <= lon_max


def bajar_inpe_filtrado(ym: str, destino) -> None:
    """Cada CSV mensual de INPE pesa 100-170 MB (toda Sudamérica, todos los satélites).
    Se lee en streaming y solo se guardan las filas dentro del rectángulo del Perú."""
    if destino.exists():
        print(f"  ya existe   {destino.name}")
        return
    with requests.get(INPE_MENSUAL.format(ym=ym), stream=True, timeout=600) as r:
        r.raise_for_status()
        lineas = (l.decode("utf-8", errors="replace") for l in r.iter_lines() if l)
        lector = csv.reader(lineas)
        cabecera = next(lector)
        i_lat, i_lon = cabecera.index("lat"), cabecera.index("lon")
        buf = io.StringIO()
        escritor = csv.writer(buf, lineterminator="\n")
        escritor.writerow(cabecera)
        n_tot = n_ok = 0
        for fila in lector:
            n_tot += 1
            try:
                if en_bbox(float(fila[i_lat]), float(fila[i_lon])):
                    escritor.writerow([c.strip() for c in fila])
                    n_ok += 1
            except (ValueError, IndexError):
                continue
    destino.write_text(buf.getvalue(), encoding="utf-8")
    print(f"  filtrado    {destino.name}  {n_ok:,} de {n_tot:,} filas en el rectángulo Perú")


def main() -> None:
    (RAW / "firms").mkdir(exist_ok=True)
    (RAW / "inpe").mkdir(exist_ok=True)
    (RAW / "limites").mkdir(exist_ok=True)

    print("1/4 FIRMS VIIRS S-NPP, archivo anual Perú 2012-2025")
    for a in ANIOS_BASE:
        bajar(FIRMS_ANUAL.format(a=a), RAW / "firms" / f"viirs-snpp_{a}_Peru.csv")

    print("2/4 FIRMS NRT últimos 7 días (para calibrar con INPE)")
    bajar(FIRMS_7D, RAW / "firms" / "SUOMI_VIIRS_C2_South_America_7d.csv", forzar="--7d" in sys.argv)

    print("3/4 INPE Queimadas, CSV mensual Sudamérica (filtrado al Perú)")
    for ym in MESES_INPE:
        # el mes en curso se vuelve a bajar si se pide --actualizar
        destino = RAW / "inpe" / f"focos_inpe_peru_{ym}.csv"
        if ym == MESES_INPE[-2] and "--actualizar" in sys.argv and destino.exists():
            destino.unlink()
        bajar_inpe_filtrado(ym, destino)

    print("4/4 Límites INEI (departamentos y distritos)")
    for n in ("peru_departamental_simple.geojson", "peru_distrital_simple.geojson"):
        bajar(GEOJSON.format(n=n), RAW / "limites" / n)


if __name__ == "__main__":
    main()
