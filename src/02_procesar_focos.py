"""Paso 2 · Integración y limpieza de los focos de calor 2012-2026.

En este paso se integran los CSV descargados en una sola tabla de focos para el periodo
2012-2026, a la vez que se asigna a cada foco el departamento en el que se ubica. Debe tenerse
presente que, para que la comparación entre años sea válida, todas las decisiones de limpieza
se aplican de la misma forma a los quince años de la serie:

  1. Se utiliza un solo sensor, VIIRS a bordo de Suomi-NPP (375 m).
  2. Se eliminan los duplicados, entendidos como dos focos de la misma pasada (misma hora)
     ubicados a menos de 100 m entre sí. En ese sentido, se observó que el CSV casi en tiempo
     real de INPE 2026 contiene alrededor de 6 % de estos duplicados, frente a cerca de 1 %
     en el archivo histórico de FIRMS (ver la bitácora de limpieza).
  3. Se eliminan las fuentes fijas. Para ello, se construye una máscara de 500 m alrededor de
     todo foco que FIRMS clasificó como volcán activo (type=1) u otra fuente estática
     (type=2, como industrias o quema de gas) entre 2012 y 2025, y se descarta todo foco que
     caiga dentro de ella, sin importar el año. Así, 2026, cuyos datos de INPE no incluyen el
     campo «type», recibe el mismo filtro.
  4. Se conservan únicamente los focos ubicados dentro de algún departamento del Perú según
     los límites del INEI, por lo que se excluyen aquellos situados en el mar o en los países
     vecinos que entran en el rectángulo de descarga.
  5. Se utiliza como fecha la de adquisición en UTC, tanto para FIRMS como para INPE.

Finalmente, se calibra INPE frente a FIRMS en los periodos en que ambas fuentes se traslapan.

Uso:  uv run python src/02_procesar_focos.py
"""
import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from config import ANIOS_BASE, CRS_METRICO, PROC, RAW, SATELITES_INPE, TAB

BUFFER_FUENTES_FIJAS_M = 500   # pixel VIIRS = 375 m; 500 m absorbe el error de geolocalización
DISTANCIA_DUPLICADO_M = 100    # dos píxeles VIIRS vecinos distan ~375 m: < 100 m es el mismo


def normalizar_firms(df: pd.DataFrame, fuente: str = "FIRMS") -> pd.DataFrame:
    hora = df["acq_time"].astype(int).astype(str).str.zfill(4)
    return pd.DataFrame({
        "fuente": fuente,
        "hora": pd.to_datetime(df["acq_date"] + " " + hora, format="%Y-%m-%d %H%M"),
        "fecha": pd.to_datetime(df["acq_date"]),
        "lat": df["latitude"],
        "lon": df["longitude"],
        "frp": df["frp"],
        "confianza": df["confidence"],
        "tipo_firms": df["type"] if "type" in df else pd.NA,
    })


def leer_firms() -> pd.DataFrame:
    partes = [pd.read_csv(RAW / "firms" / f"viirs-snpp_{a}_Peru.csv") for a in ANIOS_BASE]
    return normalizar_firms(pd.concat(partes, ignore_index=True))


def leer_inpe(meses: list[str]) -> pd.DataFrame:
    partes = [pd.read_csv(RAW / "inpe" / f"focos_inpe_peru_{ym}.csv") for ym in meses]
    df = pd.concat(partes, ignore_index=True)
    df = df[df["satelite"].isin(SATELITES_INPE)]
    hora = pd.to_datetime(df["data_hora_gmt"])
    return pd.DataFrame({
        "fuente": "INPE",
        "hora": hora,
        "fecha": hora.dt.normalize(),
        "lat": df["lat"].astype(float),
        "lon": df["lon"].astype(float),
        "frp": pd.to_numeric(df["frp"], errors="coerce"),
        "confianza": pd.NA,
        "tipo_firms": pd.NA,
    })


def a_puntos(df: pd.DataFrame) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["lon"], df["lat"]), crs=4326)


def mascara_fuentes_fijas(firms: pd.DataFrame) -> gpd.GeoDataFrame:
    fijas = firms[firms["tipo_firms"].isin([1, 2])]
    zona = (a_puntos(fijas).to_crs(CRS_METRICO)
            .buffer(BUFFER_FUENTES_FIJAS_M).union_all())
    return gpd.GeoDataFrame(geometry=[zona], crs=CRS_METRICO)


def deduplicar(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina los focos de una misma pasada que se encuentran a menos de 100 m de otro foco ya
    conservado. Para ello, el tiempo se incorpora como una tercera coordenada de gran magnitud,
    de modo que los focos de pasadas distintas nunca queden «cerca» entre sí en el árbol de
    búsqueda."""
    df = df.reset_index(drop=True)
    x = np.radians(df["lon"].values) * 6_371_000 * np.cos(np.radians(df["lat"].values))
    y = np.radians(df["lat"].values) * 6_371_000
    t = (df["hora"] - pd.Timestamp("2012-01-01")).dt.total_seconds().values * 1e4
    pares = cKDTree(np.column_stack([x, y, t])).query_pairs(DISTANCIA_DUPLICADO_M,
                                                            output_type="ndarray")
    fuera = np.unique(pares.max(axis=1)) if len(pares) else np.array([], dtype=int)
    return df.drop(index=fuera)


def limpiar(puntos: gpd.GeoDataFrame, mascara: gpd.GeoDataFrame,
            deptos: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, dict]:
    n_ini = len(puntos)
    puntos = a_puntos(deduplicar(pd.DataFrame(puntos.drop(columns="geometry"))))
    n0 = len(puntos)
    met = puntos.to_crs(CRS_METRICO)
    dentro_fija = met.within(mascara.geometry.iloc[0]).values
    puntos = puntos[~dentro_fija]
    n1 = len(puntos)
    puntos = gpd.sjoin(puntos, deptos[["departamento", "ubigeo", "geometry"]],
                       how="inner", predicate="within").drop(columns="index_right")
    return puntos, {"iniciales": n_ini, "duplicados": n_ini - n0, "fuente_fija": n0 - n1,
                    "fuera_del_peru": n1 - len(puntos),
                    "finales": len(puntos)}


def main() -> None:
    deptos = gpd.read_file(RAW / "limites" / "peru_departamental_simple.geojson")
    deptos = deptos.rename(columns={"NOMBDEP": "departamento", "FIRST_IDDP": "ubigeo"})
    deptos = deptos[["departamento", "ubigeo", "geometry"]].to_crs(4326)
    print(f"{len(deptos)} departamentos")

    firms = leer_firms()
    meses_2026 = [f"2026{m:02d}" for m in range(1, 11)]
    inpe = leer_inpe(meses_2026)
    print(f"FIRMS 2012-2025: {len(firms):,} focos  |  INPE 2026 (S-NPP día+noche): {len(inpe):,}")

    mascara = mascara_fuentes_fijas(firms)
    area_ha = mascara.geometry.area.iloc[0] / 1e4
    print(f"máscara de fuentes fijas: {area_ha:,.0f} ha "
          f"(a partir de {firms['tipo_firms'].isin([1, 2]).sum():,} focos tipo 1-2)")
    mascara.to_crs(4326).to_file(PROC / "mascara_fuentes_fijas.geojson", driver="GeoJSON")

    bitacora = {}
    limpios = []
    for nombre, df in (("FIRMS 2012-2025", firms), ("INPE 2026", inpe)):
        g, b = limpiar(a_puntos(df), mascara, deptos)
        bitacora[nombre] = b
        limpios.append(g)
    focos = pd.concat(limpios, ignore_index=True)
    focos["anio"] = focos["fecha"].dt.year
    focos["mes"] = focos["fecha"].dt.month
    focos["dia"] = focos["fecha"].dt.day
    # Se verifica que los archivos mensuales de INPE no incluyan focos de otros años
    focos = focos[(focos["anio"] >= 2012) & (focos["anio"] <= 2026)]

    bit = pd.DataFrame(bitacora).T
    print("\nBitácora de limpieza:\n", bit.to_string())
    bit.to_csv(TAB / "bitacora_limpieza.csv")

    cols = ["fuente", "hora", "fecha", "anio", "mes", "dia", "lat", "lon", "frp", "confianza",
            "departamento", "ubigeo"]
    focos[cols].to_parquet(PROC / "focos_2012_2026.parquet", index=False)
    print(f"\nguardado: {len(focos):,} focos -> data/processed/focos_2012_2026.parquet")

    calibrar(deptos, mascara)


def calibrar(deptos: gpd.GeoDataFrame, mascara: gpd.GeoDataFrame) -> None:
    """Verifica si INPE y FIRMS registran lo mismo. Para ello, se comparan ambas fuentes en los
    dos periodos en que se traslapan: septiembre de 2025 (archivo FIRMS frente a INPE) y los
    últimos días disponibles (FIRMS NRT de siete días frente a INPE)."""
    filas = []

    # (a) septiembre de 2025
    f25 = normalizar_firms(pd.read_csv(RAW / "firms" / "viirs-snpp_2025_Peru.csv"))
    f25 = f25[f25["fecha"].dt.month == 9]
    i25 = leer_inpe(["202509"])
    for nombre, df in (("FIRMS", f25), ("INPE", i25)):
        g, _ = limpiar(a_puntos(df), mascara, deptos)
        filas.append({"ventana": "sep-2025", "fuente": nombre, "focos": len(g)})

    # (b) traslape FIRMS NRT 7 días con INPE de octubre 2026
    nrt = normalizar_firms(pd.read_csv(RAW / "firms" / "SUOMI_VIIRS_C2_South_America_7d.csv"),
                           fuente="FIRMS NRT")
    ioct = leer_inpe(["202610"])
    # Se consideran solo los días completos presentes en ambas fuentes
    dias = sorted(set(nrt["fecha"].dt.normalize()) & set(ioct["fecha"]))
    dias = dias[1:-1]  # el primero y el último del archivo 7d suelen estar incompletos
    if not dias:
        # Considerando que el archivo de siete días es móvil, si se ejecuta después de octubre ya
        # no se traslapa con INPE
        print("\nFIRMS NRT 7d no se traslapa con INPE oct-2026: se calibra solo con sep-2025 "
              "(la corrida original dio −0,9 % en 15-19 oct, ver README)")
    for nombre, df in (("FIRMS NRT", nrt), ("INPE", ioct)) if dias else ():
        df = df[df["fecha"].dt.normalize().isin(dias)]
        g, _ = limpiar(a_puntos(df), mascara, deptos)
        filas.append({"ventana": f"{dias[0]:%d}-{dias[-1]:%d} oct-2026", "fuente": nombre,
                      "focos": len(g)})

    cal = pd.DataFrame(filas).pivot(index="ventana", columns="fuente", values="focos")
    referencia = cal["FIRMS"].fillna(cal["FIRMS NRT"]) if "FIRMS NRT" in cal else cal["FIRMS"]
    cal["dif_INPE_vs_FIRMS_%"] = 100 * (cal["INPE"] / referencia - 1)
    print("\nCalibración INPE vs FIRMS (S-NPP, Perú, tras limpieza):\n", cal.round(1).to_string())
    cal.to_csv(TAB / "calibracion_inpe_firms.csv")


if __name__ == "__main__":
    main()
