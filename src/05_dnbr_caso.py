"""Paso 5 · Del foco al área quemada: dNBR con Sentinel-2 en el incendio más grande del
departamento con el récord más marcado.

Un foco de calor NO es un incendio ni mide superficie. Para pasar a hectáreas:
  1. Agrupar focos 2026: focos a ≤ 1 km y ≤ 48 h pertenecen al mismo incendio.
  2. Tomar el incendio con más focos (ya terminado antes del corte) y su recuadro + 2 km.
  3. Buscar Sentinel-2 L2A en Planetary Computer y medir las nubes SOBRE LA ZONA con la
     capa SCL (el % de nubes de la escena entera engaña: es de un cuadro de 110 km).
  4. Elegir la imagen PREVIA más reciente y la POSTERIOR más temprana con ≤ 10 % de
     píxeles inválidos en la zona.
  5. NBR = (NIR − SWIR2) / (NIR + SWIR2) con B8A y B12 (20 m); dNBR = NBR_pre − NBR_post.
  6. Clases de severidad USGS (Key y Benson, 2006); hectáreas por clase y por distrito.

Uso:  uv run python src/05_dnbr_caso.py  [--departamento CUSCO]
"""
import json
import sys
from datetime import timedelta

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import planetary_computer
import pystac_client
import rasterio
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch
from rasterio.features import rasterize
from rasterio.windows import Window, from_bounds
from rasterio.windows import transform as win_transform
from scipy import ndimage
from shapely.geometry import box, mapping, shape
from sklearn.cluster import DBSCAN

from config import ANIO_OBJETIVO, CORTE_DIA, CORTE_MES, FIG, PROC, RAW, TAB
from estilo import SEVERIDAD, TINTA, TINTA_2, aplicar_estilo

STAC = "https://planetarycomputer.microsoft.com/api/stac/v1"
MAX_INVALIDOS = 10.0              # % máximo de píxeles nube/sombra/sin dato en la zona
SCL_INVALIDO = {0, 1, 3, 8, 9, 10, 11}   # sin dato, saturado, sombra, nubes, cirros, nieve
SCL_AGUA = 6
CORTES_DNBR = [-np.inf, -0.25, -0.10, 0.10, 0.27, 0.44, 0.66, np.inf]
CLASES = list(SEVERIDAD)          # mismo orden que los cortes
# Umbral principal 0,10 (límite inferior de «severidad baja» USGS). El 0,27 se calibró en
# bosques: en puna y matorral el NBR previo ya es bajo y el dNBR no llega a 0,27 aunque todo
# se queme (ver la figura). Se reportan ambos, más RdNBR, como sensibilidad.
UMBRAL_QUEMADO = 0.10
UMBRAL_CONSERVADOR = 0.27
UMBRAL_RDNBR = 69                 # Miller y Thode (2007): «baja» desde 69
PIXEL_HA = 20 * 20 / 1e4          # 0,04 ha por píxel de 20 m
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


# --- 1-2 · del foco al incendio -------------------------------------------------------------
def elegir_departamento() -> str:
    if "--departamento" in sys.argv:
        return sys.argv[sys.argv.index("--departamento") + 1].upper()
    rec = pd.read_csv(TAB / "record_departamentos_ene_corte.csv")
    rec = rec[rec["es_record"]].sort_values("focos_2026", ascending=False)
    # entre los departamentos con récord, el de más focos: tiene incendios grandes que medir
    return rec.iloc[0]["departamento"]


def agrupar_incendios(f: pd.DataFrame) -> pd.DataFrame:
    """≤ 1 km y ≤ 48 h = mismo incendio. Con métrica de Chebyshev sobre (x km, y km, días/2)
    y eps = 1, dos focos se enlazan si |dx| ≤ 1 km, |dy| ≤ 1 km y |dt| ≤ 2 días."""
    g = gpd.GeoDataFrame(f, geometry=gpd.points_from_xy(f.lon, f.lat), crs=4326).to_crs(32718)
    t = (f["fecha"] - f["fecha"].min()).dt.days.values
    X = np.column_stack([g.geometry.x / 1000, g.geometry.y / 1000, t / 2])
    f = f.copy()
    f["incendio"] = DBSCAN(eps=1.0, min_samples=1, metric="chebyshev").fit_predict(X)
    return f


# --- 3-4 · imágenes y nubes sobre la zona --------------------------------------------------
def leer_ventana(href: str, bounds, out_shape=None):
    with rasterio.open(href) as src:
        win = from_bounds(*bounds, transform=src.transform).round_offsets().round_lengths()
        arr = src.read(1, window=win, out_shape=out_shape, boundless=True, fill_value=0)
        return arr, win_transform(win, src.transform), src.crs


def pct_invalidos(item, bounds) -> tuple[float, float]:
    scl, _, _ = leer_ventana(item.assets["SCL"].href, bounds)
    nubes = np.isin(scl, [3, 8, 9, 10]).mean() * 100
    invalido = np.isin(scl, list(SCL_INVALIDO)).mean() * 100
    return round(nubes, 1), round(invalido, 1)


def reflectancia(dn: np.ndarray, baseline: str) -> np.ndarray:
    """Desde el baseline 04.00 (ene-2022) los DN traen +1000 de offset."""
    x = dn.astype("float32")
    off = 1000 if float(baseline) >= 4.0 else 0
    r = (x - off) / 10000
    r[dn == 0] = np.nan
    return r


def nbr(item, bounds, shape):
    b8a, tr, crs = leer_ventana(item.assets["B8A"].href, bounds)
    b12, _, _ = leer_ventana(item.assets["B12"].href, bounds)
    bl = item.properties["s2:processing_baseline"]
    nir, swir = reflectancia(b8a, bl), reflectancia(b12, bl)
    with np.errstate(invalid="ignore", divide="ignore"):
        return (nir - swir) / (nir + swir), tr, crs


def falso_color(item, bounds, shape) -> np.ndarray:
    """SWIR2-NIR-Rojo: lo quemado se ve marrón/rojizo, la vegetación verde."""
    bl = item.properties["s2:processing_baseline"]
    capas = []
    for banda in ("B12", "B8A", "B04"):
        arr, _, _ = leer_ventana(item.assets[banda].href, bounds, out_shape=shape)
        capas.append(reflectancia(arr, bl))
    rgb = np.dstack(capas)
    lo, hi = np.nanpercentile(rgb, 2), np.nanpercentile(rgb, 98)
    return np.clip((rgb - lo) / (hi - lo), 0, 1)


def main() -> None:
    aplicar_estilo()
    depto = elegir_departamento()
    focos = pd.read_parquet(PROC / "focos_2012_2026.parquet")
    f = focos[(focos["anio"] == ANIO_OBJETIVO) & (focos["departamento"] == depto)
              & (focos["mes"] >= 7)].copy()
    f = f[f["mes"] * 100 + f["dia"] <= CORTE_MES * 100 + CORTE_DIA]
    f = agrupar_incendios(f)
    resumen = (f.groupby("incendio")
               .agg(focos=("lat", "size"), inicio=("fecha", "min"), fin=("fecha", "max"),
                    lat=("lat", "mean"), lon=("lon", "mean"), frp=("frp", "sum"))
               .sort_values("focos", ascending=False))
    print(f"{depto}: {len(f):,} focos jul-oct 2026 agrupados en {len(resumen):,} incendios")
    print(resumen.head(8).to_string())
    resumen.head(20).to_csv(TAB / "dnbr_incendios_candidatos.csv")

    distritos = gpd.read_file(RAW / "limites" / "peru_distrital_simple.geojson").to_crs(4326)
    cat = pystac_client.Client.open(STAC, modifier=planetary_computer.sign_inplace)
    corte = pd.Timestamp(ANIO_OBJETIVO, CORTE_MES, CORTE_DIA)

    # se prueba incendio por incendio (de mayor a menor) hasta tener un par de imágenes limpias
    for inc_id, inc in resumen.head(6).iterrows():
        pts = f[f["incendio"] == inc_id]
        g = gpd.GeoSeries(gpd.points_from_xy(pts.lon, pts.lat), crs=4326)
        zona_ll = box(*g.total_bounds).buffer(0.02)             # ~2 km de margen
        print(f"\nIncendio {inc_id}: {inc.focos} focos, {inc.inicio:%d-%m} a {inc.fin:%d-%m}")

        items = list(cat.search(collections=["sentinel-2-l2a"], intersects=mapping(zona_ll),
                                datetime=f"{inc.inicio - timedelta(days=75):%Y-%m-%d}/"
                                         f"{corte + timedelta(days=1):%Y-%m-%d}").items())
        # la zona debe caer entera dentro de la parte con datos de la escena
        items = [it for it in items if shape(it.geometry).contains(zona_ll)]
        if not items:
            print("  sin escenas que cubran toda la zona")
            continue
        # una sola cuadrícula MGRS para que pre y post coincidan píxel a píxel
        tile = pd.Series([it.properties["s2:mgrs_tile"] for it in items]).mode()[0]
        items = sorted([it for it in items if it.properties["s2:mgrs_tile"] == tile],
                       key=lambda it: it.datetime)
        props = items[0].properties
        crs_tile = props.get("proj:code") or f"EPSG:{props['proj:epsg']}"
        bounds = gpd.GeoSeries([zona_ll], crs=4326).to_crs(crs_tile).total_bounds

        filas = []
        for it in items:
            nubes, inval = pct_invalidos(it, bounds)
            fecha = pd.Timestamp(it.datetime.date())
            momento = "previa" if fecha < inc.inicio else ("posterior" if fecha > inc.fin
                                                            else "durante")
            filas.append({"fecha": fecha.date(), "escena": it.id, "momento": momento,
                          "orbita": it.properties.get("sat:relative_orbit"),
                          "nubes_escena_%": round(it.properties["eo:cloud_cover"], 1),
                          "nubes_zona_%": nubes, "invalidos_zona_%": inval})
        cand = pd.DataFrame(filas)
        print(cand.to_string(index=False))
        pre = cand[(cand.momento == "previa") & (cand["invalidos_zona_%"] <= MAX_INVALIDOS)]
        post = cand[(cand.momento == "posterior") & (cand["invalidos_zona_%"] <= MAX_INVALIDOS)]
        if pre.empty or post.empty:
            print("  sin par limpio previa/posterior; siguiente incendio")
            continue
        sel_post = post.iloc[0]
        # misma órbita relativa = mismo ángulo de visión e iluminación antes y después
        misma = pre[pre["orbita"] == sel_post["orbita"]]
        sel_pre = (misma if not misma.empty else pre).iloc[-1]
        cand.to_csv(TAB / "dnbr_imagenes_candidatas.csv", index=False)
        break
    else:
        raise SystemExit("Ningún incendio tuvo un par de imágenes limpias.")

    it_pre = next(it for it in items if it.id == sel_pre.escena)
    it_post = next(it for it in items if it.id == sel_post.escena)
    print(f"\nPREVIA   {sel_pre.fecha}  nubes zona {sel_pre['nubes_zona_%']} %  ({it_pre.id})")
    print(f"POSTERIOR {sel_post.fecha}  nubes zona {sel_post['nubes_zona_%']} %  ({it_post.id})")

    # --- 5 · NBR y dNBR ---------------------------------------------------------------------
    nbr_pre, tr, crs = nbr(it_pre, bounds, None)
    nbr_post, _, _ = nbr(it_post, bounds, None)
    scl_pre, _, _ = leer_ventana(it_pre.assets["SCL"].href, bounds)
    scl_post, _, _ = leer_ventana(it_post.assets["SCL"].href, bounds)
    validos = (~np.isin(scl_pre, list(SCL_INVALIDO | {SCL_AGUA}))
               & ~np.isin(scl_post, list(SCL_INVALIDO | {SCL_AGUA}))
               & np.isfinite(nbr_pre) & np.isfinite(nbr_post))
    dnbr = np.where(validos, nbr_pre - nbr_post, np.nan).astype("float32")
    print(f"píxeles válidos en la zona: {validos.mean():.1%} de {validos.size:,}")

    perfil = dict(driver="GTiff", height=dnbr.shape[0], width=dnbr.shape[1], count=1,
                  dtype="float32", crs=crs, transform=tr, nodata=np.nan, compress="deflate")
    with rasterio.open(PROC / "dnbr_caso.tif", "w", **perfil) as dst:
        dst.write(dnbr, 1)

    # --- 6 · severidad y hectáreas ------------------------------------------------------------
    clase = np.digitize(dnbr, CORTES_DNBR[1:-1])           # 0..6
    clase = np.where(validos, clase, -1)
    ha_clase = pd.Series({CLASES[k]: (clase == k).sum() * PIXEL_HA for k in range(7)},
                         name="hectareas")

    # "sembrado": solo manchas quemadas conectadas (≤ 375 m) a un foco VIIRS del incendio;
    # así no se cuentan cambios sueltos por sombras, cultivos o ruido lejos del fuego
    pts_utm = gpd.GeoSeries(gpd.points_from_xy(pts.lon, pts.lat), crs=4326).to_crs(crs)
    semilla = rasterize(((p.buffer(375), 1) for p in pts_utm), out_shape=dnbr.shape,
                        transform=tr, fill=0, dtype="uint8").astype(bool)

    def sembrar(mascara: np.ndarray) -> np.ndarray:
        etiquetas, _ = ndimage.label(mascara)
        ids = np.unique(etiquetas[semilla & mascara])
        return np.isin(etiquetas, ids[ids > 0])

    # RdNBR relativiza el cambio por la vegetación previa: sirve donde había poca biomasa
    with np.errstate(invalid="ignore", divide="ignore"):
        rdnbr = 1000 * dnbr / np.sqrt(np.maximum(np.abs(nbr_pre), 0.001))
    quemado = validos & (dnbr >= UMBRAL_QUEMADO)
    sembrado = sembrar(quemado)                          # ESTIMACIÓN PRINCIPAL
    sembrado_027 = sembrar(validos & (dnbr >= UMBRAL_CONSERVADOR))
    sembrado_rd = sembrar(validos & (rdnbr >= UMBRAL_RDNBR))

    areas = {
        "dNBR ≥ 0,27 (toda la zona)": (validos & (dnbr >= UMBRAL_CONSERVADOR)).sum() * PIXEL_HA,
        "dNBR ≥ 0,27 conectado a focos": sembrado_027.sum() * PIXEL_HA,
        "dNBR ≥ 0,10 (toda la zona)": quemado.sum() * PIXEL_HA,
        "dNBR ≥ 0,10 conectado a focos (principal)": sembrado.sum() * PIXEL_HA,
        "RdNBR ≥ 69 conectado a focos": sembrado_rd.sum() * PIXEL_HA,
    }
    for k, v in areas.items():
        print(f"  {k:<45} {v:>10,.0f} ha")
    nbr_pre_quemado = float(np.nanmedian(nbr_pre[sembrado]))
    print(f"  NBR previo mediano en lo quemado: {nbr_pre_quemado:.2f} "
          f"(un bosque denso suele estar sobre 0,5)")

    dist = distritos.to_crs(crs)
    dist = dist[dist.intersects(box(*bounds))].reset_index(drop=True)
    id_dist = rasterize(((geom, i + 1) for i, geom in enumerate(dist.geometry)),
                        out_shape=dnbr.shape, transform=tr, fill=0, dtype="int32")
    por_dist = []
    for i, d in dist.iterrows():
        m = id_dist == i + 1
        fila = {"departamento": d["NOMBDEP"], "provincia": d["NOMBPROV"],
                "distrito": d["NOMBDIST"],
                "ha_quemadas_sembrado": (sembrado & m).sum() * PIXEL_HA}
        for k in range(3, 7):
            fila[f"ha_{CLASES[k]}"] = ((clase == k) & sembrado & m).sum() * PIXEL_HA
        por_dist.append(fila)
    por_dist = pd.DataFrame(por_dist).sort_values("ha_quemadas_sembrado", ascending=False)
    por_dist = por_dist[por_dist["ha_quemadas_sembrado"] > 0]
    por_dist.to_csv(TAB / "dnbr_hectareas_distrito.csv", index=False)
    print(por_dist.round(0).to_string(index=False))

    ha_sembrado_clase = pd.Series({CLASES[k]: ((clase == k) & sembrado).sum() * PIXEL_HA
                                   for k in range(3, 7)})
    tabla = pd.DataFrame({"zona_completa_ha": ha_clase,
                          "conectado_a_focos_ha": ha_sembrado_clase}).reindex(CLASES).fillna(0)
    tabla.to_csv(TAB / "dnbr_hectareas_severidad.csv")

    distrito_principal = por_dist.iloc[0] if len(por_dist) else None
    resumen_json = {
        "departamento": depto,
        "distrito_principal": None if distrito_principal is None else
            f"{distrito_principal['distrito'].title()}, {distrito_principal['provincia'].title()}",
        "incendio": {"focos": int(inc.focos), "inicio": f"{inc.inicio:%Y-%m-%d}",
                     "fin": f"{inc.fin:%Y-%m-%d}", "frp_total_mw": round(float(inc.frp), 1),
                     "lat": round(float(inc.lat), 4), "lon": round(float(inc.lon), 4)},
        "imagen_previa": {"fecha": str(sel_pre.fecha), "escena": it_pre.id,
                          "nubes_zona_%": float(sel_pre["nubes_zona_%"]),
                          "nubes_escena_%": float(sel_pre["nubes_escena_%"])},
        "imagen_posterior": {"fecha": str(sel_post.fecha), "escena": it_post.id,
                             "nubes_zona_%": float(sel_post["nubes_zona_%"]),
                             "nubes_escena_%": float(sel_post["nubes_escena_%"])},
        "zona_km2": round(dnbr.size * PIXEL_HA / 100, 1),
        "pixeles_validos_%": round(float(validos.mean() * 100), 1),
        "hectareas": {k: round(float(v), 1) for k, v in areas.items()},
        "hectareas_por_clase_sembrado": {k: round(float(v), 1)
                                         for k, v in ha_sembrado_clase.items()},
        "umbral_quemado": UMBRAL_QUEMADO,
        "estimacion_principal_ha": round(float(sembrado.sum() * PIXEL_HA), 1),
        "nbr_previo_mediano_quemado": round(nbr_pre_quemado, 3),
        "bbox_lonlat": [round(v, 4) for v in zona_ll.bounds],
    }
    (TAB / "dnbr_resumen.json").write_text(json.dumps(resumen_json, ensure_ascii=False, indent=2),
                                           encoding="utf-8")

    # --- figura -----------------------------------------------------------------------------------
    rgb_pre = falso_color(it_pre, bounds, dnbr.shape)
    rgb_post = falso_color(it_post, bounds, dnbr.shape)
    ext = (tr.c, tr.c + tr.a * dnbr.shape[1], tr.f + tr.e * dnbr.shape[0], tr.f)
    fig, ejes = plt.subplots(1, 3, figsize=(13.5, 5.2))
    for ax, img, titulo in ((ejes[0], rgb_pre, f"Antes · {sel_pre.fecha}"),
                            (ejes[1], rgb_post, f"Después · {sel_post.fecha}")):
        ax.imshow(img, extent=ext)
        ax.set_title(f"{titulo}\nSentinel-2 falso color (SWIR2-NIR-rojo)", loc="left")
    cmap = ListedColormap([SEVERIDAD[c] for c in CLASES])
    norm = BoundaryNorm(np.arange(-0.5, 7.5, 1), cmap.N)
    ejes[2].imshow(np.ma.masked_less(clase, 0), extent=ext, cmap=cmap, norm=norm,
                   interpolation="nearest")
    ejes[2].contour(sembrado.astype(int), levels=[0.5], colors=[TINTA], linewidths=0.6,
                    extent=ext, origin="upper")
    ejes[2].scatter(pts_utm.x, pts_utm.y, s=9, c="white", edgecolors=TINTA, linewidths=0.6,
                    zorder=3, label="foco VIIRS")
    ejes[2].set_title(f"Severidad dNBR · {sembrado.sum() * PIXEL_HA:,.0f} ha quemadas\n"
                      "(dNBR ≥ 0,10 conectado a focos; contorno negro)", loc="left")
    leyenda = [Patch(color=SEVERIDAD[c], label=c) for c in CLASES]
    ejes[2].legend(handles=leyenda, loc="lower left", fontsize=7, bbox_to_anchor=(1.01, 0))
    for ax in ejes:
        ax.set_xticks([]), ax.set_yticks([]), ax.grid(False)
    lugar = resumen_json["distrito_principal"] or depto
    fig.suptitle(f"Incendio de {lugar} ({depto.title()}), {inc.inicio.day}–{inc.fin.day} de "
                 f"{MESES[inc.fin.month - 1]} de 2026 · {int(inc.focos)} focos VIIRS", x=0.01, ha="left",
                 fontsize=12, fontweight="semibold", color=TINTA)
    fig.text(0.01, 0.01, f"Nubes sobre la zona (SCL): antes {sel_pre['nubes_zona_%']} %, "
             f"después {sel_post['nubes_zona_%']} %. Píxel de 20 m. Fuente: Sentinel-2 L2A, "
             "Microsoft Planetary Computer; focos NASA FIRMS/INPE.", fontsize=7.5, color=TINTA_2)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(FIG / "dnbr_caso.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("figura: outputs/figuras/dnbr_caso.png")


if __name__ == "__main__":
    main()
