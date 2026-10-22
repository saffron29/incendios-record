"""Paso 7 · Exportar los resultados a un tablero HTML autocontenido.

Escribe docs/index.html (listo para GitHub Pages: Settings → Pages → carpeta /docs).
No necesita servidor ni librerías: los datos van incrustados como JSON y el mapa se dibuja
en SVG a partir de los polígonos INEI simplificados.

Uso:  uv run python src/07_tablero.py
"""
import base64
import json
from datetime import datetime

import geopandas as gpd
import numpy as np
import pandas as pd

from config import (ANIO_OBJETIVO, ANIOS_BASE, CORTE_DIA, CORTE_MES, DOCS, FIG, RAIZ, RAW,
                    TAB)

VENTANAS = {"ene_corte": f"1 ene – {CORTE_DIA} oct", "jul_corte": f"1 jul – {CORTE_DIA} oct",
            "oct_corte": f"1 – {CORTE_DIA} oct"}
PLANTILLA = RAIZ / "src" / "plantilla_tablero.html"


def img64(nombre: str) -> str:
    return "data:image/png;base64," + base64.b64encode((FIG / nombre).read_bytes()).decode()


def svg_paths(deptos: gpd.GeoDataFrame, ancho: float = 520) -> tuple[dict, dict, str]:
    """Proyección equirectangular con corrección cos(latitud media): basta a esta escala."""
    lon0, lat0, lon1, lat1 = deptos.total_bounds
    k = np.cos(np.radians((lat0 + lat1) / 2))
    escala = ancho / ((lon1 - lon0) * k)
    alto = (lat1 - lat0) * escala

    def xy(lon, lat):
        return (lon - lon0) * k * escala, (lat1 - lat) * escala

    paths, centros = {}, {}
    for _, d in deptos.iterrows():
        geom = d.geometry.simplify(0.008, preserve_topology=True)
        polys = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
        partes = []
        for p in polys:
            pts = [xy(x, y) for x, y in p.exterior.coords]
            partes.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
        paths[d.departamento] = "".join(partes)
        c = d.geometry.representative_point()
        centros[d.departamento] = [round(v, 1) for v in xy(c.x, c.y)]
    return paths, centros, f"0 0 {ancho:.0f} {alto:.0f}"


def main() -> None:
    deptos = gpd.read_file(RAW / "limites" / "peru_departamental_simple.geojson")
    deptos = deptos.rename(columns={"NOMBDEP": "departamento", "FIRST_IDDP": "ubigeo"})
    paths, centros, viewbox = svg_paths(deptos.to_crs(4326))

    anios = ANIOS_BASE + [ANIO_OBJETIVO]
    datos = {"anios": anios, "ventanas": VENTANAS, "corte": f"{ANIO_OBJETIVO}-{CORTE_MES:02d}-"
             f"{CORTE_DIA:02d}", "generado": datetime.now().strftime("%Y-%m-%d %H:%M"),
             "viewbox": viewbox, "deptos": {}, "nacional": {}}
    for v in VENTANAS:
        panel = pd.read_csv(TAB / f"panel_focos_{v}.csv", index_col=0)
        rec = pd.read_csv(TAB / f"record_departamentos_{v}.csv", index_col=0)
        nac = panel.sum()
        base = nac[[str(a) for a in ANIOS_BASE]]
        datos["nacional"][v] = {
            "serie": [int(x) for x in nac.values],
            "prom": round(float(base.mean()), 1),
            "max_previo": int(base.max()),
            "anio_max_previo": int(base.idxmax()),
            "rango": int((nac > nac[str(ANIO_OBJETIVO)]).sum() + 1),
        }
        for d in panel.index:
            r = rec.loc[d]
            e = datos["deptos"].setdefault(d, {"path": paths[d], "c": centros[d],
                                               "area_km2": round(float(r["area_km2"]))})
            e[v] = {"serie": [int(x) for x in panel.loc[d].values],
                    "prom": round(float(r["prom_2012_2025"]), 1),
                    "max_previo": int(r["max_previo"]),
                    "anio_max_previo": int(r["anio_max_previo"]),
                    "razon": None if pd.isna(r["razon_vs_prom"]) else round(float(r["razon_vs_prom"]), 3),
                    "z": None if pd.isna(r["z"]) else round(float(r["z"]), 2),
                    "rango": int(r["rango_2026"]), "record": bool(r["es_record"]),
                    "dens": round(float(r["focos_2026_por_1000km2"]), 2)}

    frp = pd.read_csv(TAB / "record_departamentos_frp_ene_corte.csv", index_col=0)
    for d in frp.index:
        datos["deptos"][d]["frp_record"] = bool(frp.loc[d, "es_record"])
        datos["deptos"][d]["frp_razon"] = round(float(frp.loc[d, "razon_vs_prom"]), 2)

    sens = pd.read_csv(TAB / "sensibilidad_record.csv", index_col=0)
    datos["sensibilidad"] = {d: int(sens.loc[d, "n_criterios_record"]) for d in sens.index}
    datos["dnbr"] = json.loads((TAB / "dnbr_resumen.json").read_text(encoding="utf-8"))
    datos["dnbr_clases"] = pd.read_csv(TAB / "dnbr_hectareas_severidad.csv", index_col=0) \
        .round(1).reset_index().rename(columns={"index": "clase"}).to_dict("records")
    datos["dnbr_imagenes"] = pd.read_csv(TAB / "dnbr_imagenes_candidatas.csv").to_dict("records")
    cal = pd.read_csv(TAB / "calibracion_inpe_firms.csv")
    datos["calibracion"] = json.loads(cal.round(2).to_json(orient="records"))

    html = PLANTILLA.read_text(encoding="utf-8")
    html = (html.replace("/*__DATOS__*/null", json.dumps(datos, ensure_ascii=False))
            .replace("__IMG_DNBR__", img64("dnbr_caso.png"))
            .replace("__IMG_ANOMALIA__", img64("mapa_anomalia_raster.png"))
            .replace("__IMG_ESTACIONALIDAD__", img64("estacionalidad.png")))

    # GitHub Pages necesita el documento completo; el publicador de artifacts pone el suyo
    (RAIZ / "outputs" / "tablero_fragmento.html").write_text(html, encoding="utf-8")
    cabeza, cuerpo = html.split("</style>", 1)
    completo = ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width, initial-scale=1, '
                'viewport-fit=cover">\n' + cabeza + "</style>\n</head>\n<body>\n" + cuerpo
                + "\n</body>\n</html>\n")
    (DOCS / "index.html").write_text(completo, encoding="utf-8")
    print(f"tablero: docs/index.html ({len(completo) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
