"""Paso 3 · ¿Es 2026 un año récord? Comparación 2026 vs 2012-2025 por departamento.

Unidad de comparación: número de focos VIIRS S-NPP en la MISMA ventana del calendario
en cada año (1 de enero al día de corte). Se reportan cuatro medidas por departamento:

  rango      posición de 2026 entre los 15 años (1 = el más alto de la serie)
  razón      focos 2026 / promedio 2012-2025   (1,0 = un año típico)
  z          (2026 − promedio) / desviación estándar 2012-2025
  récord     2026 supera al máximo previo, y por cuánto

Sensibilidad: se repite con otras dos ventanas (temporada jul–oct y solo octubre) y
con la energía radiativa (FRP), para ver si la conclusión depende de la elección.

Uso:  uv run python src/03_comparar.py
"""
import geopandas as gpd
import numpy as np
import pandas as pd

from config import (ANIO_OBJETIVO, ANIOS_BASE, CORTE_DIA, CORTE_MES, CRS_METRICO, PROC, RAW,
                    TAB)

MUESTRA_MINIMA = 30   # focos promedio por año en la ventana

VENTANAS = {
    "ene_corte": ((1, 1), (CORTE_MES, CORTE_DIA)),     # principal: año a la fecha
    "jul_corte": ((7, 1), (CORTE_MES, CORTE_DIA)),     # temporada seca de quemas
    "oct_corte": ((10, 1), (CORTE_MES, CORTE_DIA)),    # el pico de octubre
}


def en_ventana(df: pd.DataFrame, inicio: tuple, fin: tuple) -> pd.Series:
    md = df["mes"] * 100 + df["dia"]
    return (md >= inicio[0] * 100 + inicio[1]) & (md <= fin[0] * 100 + fin[1])


def panel_anual(focos: pd.DataFrame, deptos: list[str], valor: str = "n") -> pd.DataFrame:
    """Tabla departamento × año (todos los departamentos y años, ceros incluidos)."""
    if valor == "n":
        t = focos.groupby(["departamento", "anio"]).size()
    else:
        t = focos.groupby(["departamento", "anio"])[valor].sum()
    anios = ANIOS_BASE + [ANIO_OBJETIVO]
    return t.unstack("anio").reindex(index=deptos, columns=anios).fillna(0)


def resumen_record(panel: pd.DataFrame) -> pd.DataFrame:
    base = panel[ANIOS_BASE]
    obj = panel[ANIO_OBJETIVO]
    r = pd.DataFrame(index=panel.index)
    r["focos_2026"] = obj
    r["prom_2012_2025"] = base.mean(axis=1)
    r["mediana_2012_2025"] = base.median(axis=1)
    r["max_previo"] = base.max(axis=1)
    r["anio_max_previo"] = base.idxmax(axis=1)
    r["razon_vs_prom"] = obj / r["prom_2012_2025"].replace(0, np.nan)
    r["cambio_vs_prom_%"] = 100 * (r["razon_vs_prom"] - 1)
    r["z"] = (obj - r["prom_2012_2025"]) / base.std(axis=1, ddof=1).replace(0, np.nan)
    # rango: 1 = el año más alto entre 2012 y 2026; empates cuentan a favor del pasado
    r["rango_2026"] = (panel.gt(obj, axis=0)).sum(axis=1) + 1
    r["es_record"] = obj > r["max_previo"]
    r["margen_vs_record_%"] = 100 * (obj / r["max_previo"].replace(0, np.nan) - 1)
    # con menos de 30 focos al año, un par de quemas cambia el ranking: leer con cautela
    r["muestra_pequena"] = r["prom_2012_2025"] < MUESTRA_MINIMA
    return r


def main() -> None:
    focos = pd.read_parquet(PROC / "focos_2012_2026.parquet")
    deptos_gdf = gpd.read_file(RAW / "limites" / "peru_departamental_simple.geojson")
    deptos_gdf = deptos_gdf.rename(columns={"NOMBDEP": "departamento", "FIRST_IDDP": "ubigeo"})
    # áreas en un CRS métrico, nunca en grados (EPSG:4326)
    deptos_gdf["area_km2"] = deptos_gdf.to_crs(CRS_METRICO).geometry.area / 1e6
    deptos = sorted(deptos_gdf["departamento"])
    area = deptos_gdf.set_index("departamento")["area_km2"]

    salidas = {}
    for nombre, (ini, fin) in VENTANAS.items():
        sub = focos[en_ventana(focos, ini, fin)]
        panel = panel_anual(sub, deptos)
        panel.to_csv(TAB / f"panel_focos_{nombre}.csv")
        res = resumen_record(panel)
        res["area_km2"] = area
        res["focos_2026_por_1000km2"] = 1000 * res["focos_2026"] / res["area_km2"]
        res = res.sort_values("razon_vs_prom", ascending=False)
        res.to_csv(TAB / f"record_departamentos_{nombre}.csv")
        salidas[nombre] = (panel, res)

        nac = panel.sum()
        print(f"\n=== Ventana {nombre}: {ini[1]:02d}/{ini[0]:02d} a {fin[1]:02d}/{fin[0]:02d} ===")
        print("Perú, focos por año:", ", ".join(f"{a}: {int(v):,}" for a, v in nac.items()))
        base = nac[ANIOS_BASE]
        print(f"2026 = {int(nac[ANIO_OBJETIVO]):,} | promedio base {base.mean():,.0f} | "
              f"razón {nac[ANIO_OBJETIVO] / base.mean():.2f} | "
              f"máximo previo {int(base.max()):,} ({base.idxmax()}) | "
              f"rango 2026: {int((nac > nac[ANIO_OBJETIVO]).sum() + 1)} de {len(nac)}")
        print(f"Departamentos con récord: {int(res['es_record'].sum())} de {len(res)}")
        cols = ["focos_2026", "prom_2012_2025", "max_previo", "anio_max_previo",
                "razon_vs_prom", "z", "rango_2026", "es_record"]
        print(res[cols].round(2).to_string())

    # Medida alternativa: energía radiativa del fuego (FRP, MW) en la ventana principal
    ini, fin = VENTANAS["ene_corte"]
    sub = focos[en_ventana(focos, ini, fin)]
    panel_frp = panel_anual(sub, deptos, valor="frp")
    res_frp = resumen_record(panel_frp).sort_values("razon_vs_prom", ascending=False)
    panel_frp.to_csv(TAB / "panel_frp_ene_corte.csv")
    res_frp.to_csv(TAB / "record_departamentos_frp_ene_corte.csv")
    print("\n=== FRP total (MW), ventana principal ===")
    print(res_frp[["focos_2026", "prom_2012_2025", "razon_vs_prom", "rango_2026", "es_record"]]
          .round(2).to_string())

    # Tabla de sensibilidad: ¿el veredicto de récord cambia con la ventana o la medida?
    sens = pd.DataFrame({
        f"record_{n}": salidas[n][1]["es_record"] for n in VENTANAS
    })
    sens["record_frp"] = res_frp["es_record"]
    for n in VENTANAS:
        sens[f"rango_{n}"] = salidas[n][1]["rango_2026"]
    sens["n_criterios_record"] = sens.filter(like="record_").sum(axis=1)
    sens = sens.sort_values(["n_criterios_record", "rango_ene_corte"], ascending=[False, True])
    sens.to_csv(TAB / "sensibilidad_record.csv")
    print("\n=== Sensibilidad del veredicto ===\n", sens.to_string())

    # Serie mensual nacional (para el gráfico de estacionalidad)
    # 2026 solo hasta el corte: el día en curso viene incompleto
    pasado_corte = ((focos["anio"] == ANIO_OBJETIVO)
                    & (focos["mes"] * 100 + focos["dia"] > CORTE_MES * 100 + CORTE_DIA))
    mensual = (focos[~pasado_corte].groupby(["anio", "mes"]).size().unstack("mes")
               .reindex(columns=range(1, 13)))
    mensual.to_csv(TAB / "serie_mensual_nacional.csv")


if __name__ == "__main__":
    main()
