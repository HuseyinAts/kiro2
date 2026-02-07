"""
OSYM Diagram Styles - KIRO2

Contains style configurations and geographic data for diagram generation.
"""

from typing import Any, Dict

# OSYM Diagram Styling
OSYM_DIAGRAM_STYLE: Dict[str, Any] = {
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "black",
    "axes.linewidth": 1.5,
    "grid.color": "#cccccc",
    "grid.linestyle": "--",
    "grid.linewidth": 0.5,
    "text.color": "black",
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 12,
    "lines.linewidth": 1.5,
    "lines.color": "black",
    "patch.edgecolor": "black",
    "patch.linewidth": 1.5,
}

# Color definitions
COLORS = {
    "highlighted": "#666666",
    "default": "#e0e0e0",
    "component_bg": "#f0f0f0",
    "white": "white",
    "black": "black",
    "light_gray": "#f5f5f5",
    "root_bg": "#d0d0d0",
}

# Turkey Geographic Data
TURKEY_REGIONS: Dict[str, Dict[str, Any]] = {
    "Marmara": {
        "bbox": [(26, 40), (32, 42)],
        "cities": ["Istanbul", "Bursa", "Kocaeli", "Edirne", "Tekirdag"],
    },
    "Ege": {
        "bbox": [(26, 37), (30, 40)],
        "cities": ["Izmir", "Aydin", "Mugla", "Manisa", "Denizli"],
    },
    "Akdeniz": {
        "bbox": [(29, 36), (37, 38)],
        "cities": ["Antalya", "Adana", "Mersin", "Hatay", "Kahramanmaras"],
    },
    "Ic Anadolu": {
        "bbox": [(31, 38), (36, 41)],
        "cities": ["Ankara", "Konya", "Kayseri", "Sivas", "Eskisehir"],
    },
    "Karadeniz": {
        "bbox": [(31, 40), (42, 42)],
        "cities": ["Samsun", "Trabzon", "Ordu", "Zonguldak", "Rize"],
    },
    "Dogu Anadolu": {
        "bbox": [(38, 38), (45, 41)],
        "cities": ["Erzurum", "Van", "Elazig", "Malatya", "Agri"],
    },
    "Guneydogu Anadolu": {
        "bbox": [(37, 36), (43, 39)],
        "cities": ["Gaziantep", "Sanliurfa", "Diyarbakir", "Mardin", "Batman"],
    },
}

TURKEY_MAJOR_CITIES: Dict[str, Dict[str, Any]] = {
    "Istanbul": {"coords": (29.0, 41.0), "population": 15840000},
    "Ankara": {"coords": (32.85, 39.93), "population": 5747325},
    "Izmir": {"coords": (27.14, 38.42), "population": 4425789},
    "Bursa": {"coords": (29.06, 40.18), "population": 3194720},
    "Antalya": {"coords": (30.71, 36.89), "population": 2619832},
}

# World Continents Data
CONTINENTS: Dict[str, Dict[str, Any]] = {
    "Asya": {"bbox": (70, 10, 70, 50), "label_pos": (105, 30)},
    "Avrupa": {"bbox": (10, 35, 40, 35), "label_pos": (30, 52.5)},
    "Afrika": {"bbox": (15, -35, 40, 50), "label_pos": (35, 7.5)},
    "Kuzey Amerika": {"bbox": (-130, 15, 60, 55), "label_pos": (-100, 42.5)},
    "Guney Amerika": {"bbox": (-80, -55, 35, 55), "label_pos": (-62.5, -27.5)},
    "Avustralya": {"bbox": (113, -39, 40, 22), "label_pos": (133, -28)},
}

# Default figure size
DEFAULT_FIG_SIZE = (10, 7)
