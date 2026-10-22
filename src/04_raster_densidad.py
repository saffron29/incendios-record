"""Paso 4 · De puntos a raster: ¿DÓNDE, dentro de cada departamento, está el exceso de 2026?

Una tabla por departamento esconde la geografía interna: un departamento puede batir su
récord por un solo foco caliente. Se construyen tres rasters de 0,1° (~11 km):

  densidad_2026.tif        focos 2026 por celda (1 ene - corte)
  densidad_base_prom.tif   promedio anual 2012-2025 por celda (misma ventana)
  anomalia_2026.tif        diferencia 2026 − promedio (focos por celda)

y se vuelve de raster a tabla con zonal_stats, igual que en la clase de luces nocturnas,
para validar que la suma por departamento reproduce el conteo directo de puntos.

Uso:  uv run python src/04_raster_densidad.py
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib.colors import TwoSlopeNorm
from rasterio.features import rasterize
from rasterio.transform import from_origin
from rasterstats import zonal_stats

from config import (ANIO_OBJETIVO, ANIOS_BASE, BBOX_PERU, CORTE_DIA, CORTE_MES, FIG, PROC, RAW,
                    TAB)
from estilo import DIVERGENTE, TINTA, TINTA_2, aplicar_estilo

RES = 0.1          # grados por celda
NODATA = -9999.0


def grilla():
    lon_min, lat_min, lon_max, lat_max = BBOX_PERU
    ancho = int(np.ceil((lon_max - lon_min) / RES))
    alto = int(np.ceil((lat_max - lat_min) / RES))
    transform = from_origin(lon_min, lat_min + alto * RES, RES, RES)
    return transform, alto, ancho


def contar(df: pd.DataFrame, transform, alto: int, ancho: int) -> np.ndarray:
    col = np.floor((df["lon"].values - transform.c) / RES).astype(int)
    fil = np.floor((transform.f - df["lat"].values) / RES).astype(int)
    ok = (col >= 0) & (col < ancho) & (fil >= 0) & (fil < alto)
    m = np.zeros((alto, ancho), dtype="float32")
    np.add.at(m, (fil[ok], col[ok]), 1)
    return m


def guardar(ruta, matriz, transform) -> None:
    perfil = dict(driver="GTiff", height=matriz.shape[0], width=matriz.shape[1], count=1,
                  dtype="float32", crs="EPSG:4326", transform=transform, nodata=NODATA,
                  compress="deflate")
    with rasterio.open(ruta, "w", **perfil) as dst:
        dst.write(matriz.astype("float32"), 1)


def main() -> None:
    aplicar_estilo()
    focos = pd.read_parquet(PROC / "focos_2012_2026.parquet")
    md = focos["mes"] * 100 + focos["dia"]
    focos = focos[md <= CORTE_MES * 100 + CORTE_DIA]

    deptos = gpd.read_file(RAW / "limites" / "peru_departamental_simple.geojson")
    deptos = deptos.rename(columns={"NOMBDEP": "departamento"}).to_crs(4326)

    transform, alto, ancho = grilla()
    # máscara: celdas cuyo centro cae en el Perú; el resto queda como nodata
    peru = rasterize(((g, 1) for g in deptos.geometry), out_shape=(alto, ancho),
                     transform=transform, fill=0, dtype="uint8").astype(bool)

    d26 = contar(focos[focos["anio"] == ANIO_OBJETIVO], transform, alto, ancho)
    base = np.stack([contar(focos[focos["anio"] == a], transform, alto, ancho)
                     for a in ANIOS_BASE]).mean(axis=0)
    anom = d26 - base

    salidas = {}
    for nombre, m in (("densidad_2026", d26), ("densidad_base_prom", base),
                      ("anomalia_2026", anom)):
        m = np.where(peru, m, NODATA)
        ruta = PROC / f"{nombre}.tif"
        guardar(ruta, m, transform)
        salidas[nombre] = ruta
    print(f"rasters de {alto} × {ancho} celdas de {RES}° guardados en data/processed/")

    # raster -> tabla (zonal_stats), con nodata explícito y all_touched=False:
    # con all_touched=True una celda de borde se sumaría a DOS departamentos.
    zs = pd.DataFrame({
        "departamento": deptos["departamento"],
        "zonal_2026": [z["sum"] for z in zonal_stats(deptos, str(salidas["densidad_2026"]),
                                                     stats=["sum"], nodata=NODATA,
                                                     all_touched=False)],
        "zonal_anomalia": [z["sum"] for z in zonal_stats(deptos, str(salidas["anomalia_2026"]),
                                                         stats=["sum"], nodata=NODATA,
                                                         all_touched=False)],
        "celdas_exceso_fuerte": [z["count"] for z in zonal_stats(
            deptos, np.where(anom >= 10, 1.0, NODATA).astype("float32"), affine=transform,
            stats=["count"], nodata=NODATA, all_touched=False)],
    })
    directo = focos[focos["anio"] == ANIO_OBJETIVO].groupby("departamento").size()
    zs["conteo_puntos_2026"] = zs["departamento"].map(directo).fillna(0)
    zs["dif_%"] = 100 * (zs["zonal_2026"] / zs["conteo_puntos_2026"].replace(0, np.nan) - 1)
    zs = zs.sort_values("zonal_anomalia", ascending=False)
    zs.to_csv(TAB / "zonal_raster_departamentos.csv", index=False)
    print("\nValidación raster -> tabla (suma zonal vs conteo directo de puntos):")
    print(zs.round(1).to_string(index=False))
    total_z, total_p = zs["zonal_2026"].sum(), zs["conteo_puntos_2026"].sum()
    print(f"total: zonal {total_z:,.0f} vs puntos {total_p:,.0f} "
          f"({100 * (total_z / total_p - 1):+.1f} %): la diferencia son las celdas de borde")

    # --- mapa de la anomalía ---------------------------------------------------
    anom_m = np.ma.masked_where(~peru, anom)
    lim = float(np.nanpercentile(np.abs(anom[peru & (anom != 0)]), 99))
    fig, ax = plt.subplots(figsize=(6.6, 8.2))
    ext = (transform.c, transform.c + ancho * RES, transform.f - alto * RES, transform.f)
    im = ax.imshow(anom_m, extent=ext, cmap=DIVERGENTE,
                   norm=TwoSlopeNorm(vmin=-lim, vcenter=0, vmax=lim), interpolation="nearest")
    deptos.boundary.plot(ax=ax, color=TINTA_2, linewidth=0.4)
    cb = fig.colorbar(im, ax=ax, shrink=0.55, pad=0.02)
    cb.set_label("focos 2026 − promedio 2012-2025, por celda de ~11 km", color=TINTA_2)
    cb.outline.set_visible(False)
    ax.set_title(f"Dónde está el exceso de 2026\nfocos VIIRS S-NPP, 1 ene – {CORTE_DIA} oct",
                 loc="left", color=TINTA)
    ax.set_axis_off()
    fig.text(0.02, 0.01, "Rojo: más focos que el promedio; azul: menos. Fuente: NASA FIRMS, INPE.",
             fontsize=7.5, color=TINTA_2)
    fig.savefig(FIG / "mapa_anomalia_raster.png", dpi=170, bbox_inches="tight")
    plt.close(fig)
    print("figura: outputs/figuras/mapa_anomalia_raster.png")


if __name__ == "__main__":
    main()
