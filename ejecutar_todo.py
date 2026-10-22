"""Corre todo el análisis en orden: uv run python ejecutar_todo.py"""
import subprocess
import sys
from pathlib import Path

PASOS = ["01_descargar.py", "02_procesar_focos.py", "03_comparar.py", "04_raster_densidad.py",
         "05_dnbr_caso.py", "06_figuras.py", "07_tablero.py"]

for paso in PASOS:
    print(f"\n{'=' * 70}\n{paso}\n{'=' * 70}", flush=True)
    subprocess.run([sys.executable, str(Path("src") / paso), *sys.argv[1:]], check=True)
