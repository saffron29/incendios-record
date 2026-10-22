"""Paso 6 · Elaboración de las figuras estáticas del README.

En este paso se elaboran las figuras que acompañan al README, las cuales se construyen a
partir de las mismas tablas que utiliza el tablero interactivo:

  mapa_record.png          mapa coroplético de la razón 2026 / promedio 2012-2025,
                           con los récords marcados
  serie_nacional.png       focos del Perú entre el 1 de enero y el corte, 2012-2026
  franja_departamentos.png cada año de cada departamento frente a su propio promedio
  estacionalidad.png       focos por mes de 2026 frente al rango histórico

Uso:  uv run python src/06_figuras.py
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import TwoSlopeNorm

from config import ANIO_OBJETIVO, ANIOS_BASE, CORTE_DIA, CORTE_MES, FIG, RAW, TAB
from estilo import (AZUL, DIVERGENTE, GRIS_BASE, NEUTRO, ROJO, SUPERFICIE, TENUE, TINTA,
                    TINTA_2, aplicar_estilo)

VENTANA = f"1 ene – {CORTE_DIA} oct"
FUENTE = "Fuente: NASA FIRMS (VIIRS S-NPP 2012-2025) e INPE Queimadas (S-NPP 2026)."
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def titulo_depto(n: str) -> str:
    return n.title().replace(" De ", " de ")


def x_razon(v: float) -> str:
    return f"×{v:.1f}".replace(".", ",")


def miles(v, _=None) -> str:
    return f"{v / 1000:.0f} mil" if v else "0"


def mapa_record(rec: pd.DataFrame) -> None:
    deptos = gpd.read_file(RAW / "limites" / "peru_departamental_simple.geojson")
    deptos = deptos.rename(columns={"NOMBDEP": "departamento"}).merge(
        rec, left_on="departamento", right_index=True)
    fig, ax = plt.subplots(figsize=(7.2, 9))
    # Se utiliza una escala logarítmica centrada en 1, de modo que el doble (×2) y la mitad
    # (×0,5) tengan el mismo peso visual
    lim = 2.0                                                   # de ×0,25 a ×4
    norma = TwoSlopeNorm(vmin=-lim, vcenter=0, vmax=lim)
    deptos["log2_razon"] = np.log2(deptos["razon_vs_prom"].clip(lower=0.25, upper=4))
    chicos = deptos["muestra_pequena"]
    deptos[~chicos].plot(column="log2_razon", ax=ax, cmap=DIVERGENTE, norm=norma,
                         edgecolor=SUPERFICIE, linewidth=0.8)
    deptos[chicos].plot(ax=ax, color=NEUTRO, edgecolor=TENUE, linewidth=0.5, hatch="////")
    deptos[deptos["es_record"]].boundary.plot(ax=ax, color=TINTA, linewidth=1.6)
    for _, d in deptos[~chicos].iterrows():
        p = d.geometry.representative_point()
        txt = f"{titulo_depto(d.departamento)}\n{x_razon(d.razon_vs_prom)}"
        if d.es_record:
            txt += " ★"
        claro = abs(d.log2_razon) < lim * 0.55
        ax.annotate(txt, (p.x, p.y), ha="center", va="center", fontsize=6.3,
                    color=TINTA if claro else "white",
                    fontweight="semibold" if d.es_record else "normal")
    sm = plt.cm.ScalarMappable(cmap=DIVERGENTE, norm=norma)
    cb = fig.colorbar(sm, ax=ax, shrink=0.45, pad=0.01, orientation="horizontal",
                      location="bottom")
    cb.set_ticks([-2, -1, 0, 1, 2], labels=["×0,25", "×0,5", "×1", "×2", "×4"])
    cb.set_label("focos 2026 / promedio 2012-2025 (escala log)", color=TINTA_2)
    cb.outline.set_visible(False)
    n_rec = int(deptos["es_record"].sum())
    ax.set_title(f"¿Año récord? {n_rec} de {len(deptos)} departamentos superan en 2026 su máximo"
                 f" desde 2012\nFocos VIIRS S-NPP, {VENTANA} de cada año · ★ y borde negro = récord",
                 loc="left", fontsize=10)
    ax.set_axis_off()
    fig.text(0.02, 0.02, FUENTE + " Límites: INEI.\nRayado: Callao, menos de 30 focos al año "
             "(muestra insuficiente).", fontsize=7, color=TINTA_2)
    fig.savefig(FIG / "mapa_record.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def serie_nacional(panel: pd.DataFrame) -> None:
    nac = panel.sum()
    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    colores = [ROJO if a == ANIO_OBJETIVO else GRIS_BASE for a in nac.index]
    ax.bar(nac.index, nac.values, color=colores, width=0.62)
    prom = nac[ANIOS_BASE].mean()
    ax.axhline(prom, color=TINTA_2, linewidth=1)
    ax.text(2011.6, prom, f" promedio 2012-2025: {prom:,.0f}".replace(",", " "), va="bottom",
            fontsize=8, color=TINTA_2)
    for a in (nac[ANIOS_BASE].idxmax(), ANIO_OBJETIVO):
        ax.text(a, nac[a], f"{nac[a]:,.0f}".replace(",", " "), ha="center", va="bottom",
                fontsize=8, color=TINTA, fontweight="semibold")
    ax.set_xticks(nac.index, [str(a) for a in nac.index], fontsize=8)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(miles))
    ax.grid(axis="x", visible=False)
    ax.set_title(f"Perú: focos de calor del {VENTANA}, por año", loc="left")
    fig.text(0.01, -0.02, FUENTE, fontsize=7, color=TINTA_2)
    fig.savefig(FIG / "serie_nacional.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def franja(panel: pd.DataFrame, rec: pd.DataFrame) -> None:
    """Cada punto gris corresponde a un año entre 2012 y 2025, mientras que el rojo corresponde
    a 2026. Todos los valores se expresan como múltiplos del promedio propio de cada
    departamento, lo cual permite comparar departamentos de tamaños muy distintos."""
    rec = rec[~rec["muestra_pequena"]]
    orden = rec.sort_values("razon_vs_prom").index
    idx = panel.div(panel[ANIOS_BASE].mean(axis=1), axis=0).loc[orden]
    fig, ax = plt.subplots(figsize=(8, 8.2))
    for i, d in enumerate(orden):
        base = idx.loc[d, ANIOS_BASE].clip(lower=0.25)
        ax.scatter(base, np.full(len(base), i), s=22, color=GRIS_BASE, edgecolors=SUPERFICIE,
                   linewidths=1, zorder=2)
        v = max(idx.loc[d, ANIO_OBJETIVO], 0.25)
        ax.scatter([v], [i], s=58, color=ROJO, edgecolors=SUPERFICIE, linewidths=1.5, zorder=3)
        es_rec = bool(rec.loc[d, "es_record"])
        ax.text(1.01, i, x_razon(idx.loc[d, ANIO_OBJETIVO]) + ("  récord" if es_rec else ""),
                transform=ax.get_yaxis_transform(), va="center", fontsize=7.5,
                color=TINTA if es_rec else TINTA_2,
                fontweight="semibold" if es_rec else "normal")
    ax.text(1.01, len(orden) - 0.4, "2026", transform=ax.get_yaxis_transform(), fontsize=7.5,
            color=TINTA_2, va="bottom")
    ax.axvline(1, color=TINTA_2, linewidth=1)
    ax.set_xscale("log")
    ax.set_xticks([0.25, 0.5, 1, 2, 4], ["×0,25", "×0,5", "×1", "×2", "×4"])
    ax.minorticks_off()
    ax.set_xlim(0.24, 4)
    ax.set_yticks(range(len(orden)), [titulo_depto(d) for d in orden], fontsize=8)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("focos del año / promedio 2012-2025 del departamento (escala log)")
    ax.scatter([], [], s=22, color=GRIS_BASE, label="2012-2025 (un punto por año)")
    ax.scatter([], [], s=58, color=ROJO, label="2026")
    ax.legend(loc="lower left", fontsize=8)
    ax.set_title(f"Cada departamento contra su propia historia · {VENTANA}", loc="left")
    fig.text(0.01, -0.01, FUENTE + " Sin Callao (menos de 30 focos al año).", fontsize=7,
             color=TINTA_2)
    fig.savefig(FIG / "franja_departamentos.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def estacionalidad() -> None:
    m = pd.read_csv(TAB / "serie_mensual_nacional.csv", index_col=0)
    m.columns = m.columns.astype(int)
    base = m.loc[ANIOS_BASE]
    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    x = np.arange(1, 13)
    ax.fill_between(x, base.min(), base.max(), color=AZUL, alpha=0.10, linewidth=0,
                    label="rango 2012-2025")
    ax.plot(x, base.mean(), color=AZUL, linewidth=2, label="promedio 2012-2025")
    v26 = m.loc[ANIO_OBJETIVO, :CORTE_MES]
    ax.plot(v26.index, v26.values, color=ROJO, linewidth=2, marker="o", markersize=5,
            markeredgecolor=SUPERFICIE, label=f"2026 (octubre solo hasta el {CORTE_DIA})")
    ax.set_xticks(x, MESES)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(miles))
    ax.legend(fontsize=8, loc="upper left")
    ax.set_title("Perú: focos de calor por mes, 2026 frente a la historia", loc="left")
    fig.text(0.01, -0.02, FUENTE + " Octubre 2026 está incompleto: el punto ya supera "
             "el promedio de un octubre entero.", fontsize=7, color=TINTA_2)
    fig.savefig(FIG / "estacionalidad.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    aplicar_estilo()
    rec = pd.read_csv(TAB / "record_departamentos_ene_corte.csv", index_col=0)
    panel = pd.read_csv(TAB / "panel_focos_ene_corte.csv", index_col=0)
    panel.columns = panel.columns.astype(int)
    mapa_record(rec)
    serie_nacional(panel)
    franja(panel, rec)
    estacionalidad()
    print("figuras en outputs/figuras/")


if __name__ == "__main__":
    main()
