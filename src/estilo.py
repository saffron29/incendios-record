"""Colores y estilo de gráficos, en un solo lugar para que todas las figuras se lean igual."""
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
TENUE = "#898781"
GRILLA = "#e1e0d9"
NEUTRO = "#f0efec"

AZUL = "#2a78d6"       # serie histórica / por debajo del promedio
ROJO = "#e34948"       # 2026 / por encima del promedio
GRIS_BASE = "#c3c2b7"  # años de referencia sin destacar

# Divergente: azul (menos que lo normal) <-> gris neutro <-> rojo (más que lo normal)
DIVERGENTE = LinearSegmentedColormap.from_list(
    "azul_rojo",
    ["#104281", "#3987e5", "#9ec5f4", NEUTRO, "#f4b4ad", "#e34948", "#8f1d1d"])

# Severidad dNBR (USGS): rebrote en azules, no quemado gris, quemado de claro a oscuro
SEVERIDAD = {
    "Rebrote alto": "#256abf",
    "Rebrote bajo": "#9ec5f4",
    "No quemado": "#e1e0d9",
    "Baja": "#f6c7a4",
    "Moderada-baja": "#ec8a55",
    "Moderada-alta": "#c9502a",
    "Alta": "#7f2410",
}


def aplicar_estilo() -> None:
    plt.rcParams.update({
        "figure.dpi": 110,
        "figure.facecolor": SUPERFICIE,
        "axes.facecolor": SUPERFICIE,
        "savefig.facecolor": SUPERFICIE,
        "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
        "font.size": 9,
        "text.color": TINTA,
        "axes.labelcolor": TINTA_2,
        "axes.edgecolor": GRIS_BASE,
        "axes.titlesize": 10.5,
        "axes.titleweight": "semibold",
        "xtick.color": TENUE,
        "ytick.color": TENUE,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": GRILLA,
        "grid.linewidth": 0.8,
        "grid.alpha": 1.0,
        "legend.frameon": False,
    })
