# Stylesheet Modern UI - Theme "Midnight Professional"

# Couleurs
BG_DARK = "#1e293b"      # Fond principal (Bleu-gris très foncé)
BG_CARD = "#334155"      # Fond des cartes/panneaux (Bleu-gris moyen)
BG_SIDEBAR = "#0f172a"   # Fond de la barre latérale (Encore plus foncé)
PRIMARY = "#ff9e1d"      # Orange SOGICI
PRIMARY_HOVER = "#e68a19"
TEXT_MAIN = "#f1f5f9"    # Blanc cassé pour le texte principal
TEXT_SEC = "#94a3b8"     # Gris clair pour le texte secondaire
BORDER = "#475569"       # Bordures subtiles
SUCCESS = "#10b981"      # Vert
DANGER = "#ef4444"       # Rouge

STYLESHEET = f"""
/* --- GLOBAL --- */
QMainWindow, QDialog {{
    background-color: {BG_DARK};
    color: {TEXT_MAIN};
}}

QWidget {{
    font-family: 'Segoe UI', 'Roboto', sans-serif;
    font-size: 14px;
    color: {TEXT_MAIN};
}}

/* --- SIDEBAR (QListWidget) --- */
QListWidget#nav_menu {{
    background-color: {BG_SIDEBAR};
    border: none;
    outline: none;
    padding-top: 20px;
}}

QListWidget#nav_menu::item {{
    background-color: transparent;
    color: {TEXT_SEC};
    height: 50px;
    padding-left: 15px;
    margin: 5px 10px;
    border-radius: 8px;
    border: 1px solid transparent;
}}

QListWidget#nav_menu::item:hover {{
    background-color: rgba(255, 255, 255, 0.05);
    color: {TEXT_MAIN};
}}

QListWidget#nav_menu::item:selected {{
    background-color: rgba(255, 158, 29, 0.15); /* Orange transparent */
    color: {PRIMARY};
    border: 1px solid {PRIMARY};
    font-weight: bold;
}}

/* --- STACKED WIDGET (CONTENT AREA) --- */
QStackedWidget {{
    background-color: {BG_DARK};
    border: none;
}}

/* --- CARDS (GroupBoxes) --- */
QGroupBox {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
    margin-top: 24px; /* Space for title */
    font-weight: bold;
    color: {PRIMARY};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 15px;
    padding: 0 5px;
    color: {TEXT_SEC};
}}

/* --- BUTTONS --- */
QPushButton {{
    background-color: {PRIMARY};
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: {PRIMARY_HOVER};
}}

QPushButton:pressed {{
    background-color: #d67d15;
    padding-top: 10px; /* Effect d'enfoncement */
    padding-bottom: 6px;
}}

QPushButton:disabled {{
    background-color: {BORDER};
    color: {TEXT_SEC};
}}

/* Boutons secondaires (Flat/Outline si besoin, à définir par classe) */
QPushButton[class="secondary"] {{
    background-color: transparent;
    border: 1px solid {BORDER};
    color: {TEXT_MAIN};
}}

QPushButton[class="secondary"]:hover {{
    border-color: {TEXT_MAIN};
    background-color: rgba(255,255,255,0.05);
}}

/* --- INPUTS & COMBOBOXES --- */
QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {BG_SIDEBAR}; /* Darker input bg */
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px;
    color: {TEXT_MAIN};
    selection-background-color: {PRIMARY};
}}

QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
    border: 1px solid {PRIMARY};
    background-color: {BG_DARK};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

/* --- TABLES (QTableWidget/QTableView) --- */
QTableWidget, QTableView {{
    background-color: {BG_CARD};
    alternate-background-color: rgba(255, 255, 255, 0.03);
    gridline-color: {BORDER};
    border: none;
    border-radius: 8px;
    color: {TEXT_MAIN};
    selection-background-color: {PRIMARY};
    selection-color: white;
}}

QHeaderView::section {{
    background-color: {BG_SIDEBAR};
    color: {TEXT_SEC};
    padding: 8px;
    border: none;
    border-bottom: 2px solid {BORDER};
    font-weight: bold;
}}

QTableWidget::item, QTableView::item {{
    padding: 5px;
}}

QTableWidget::item:selected, QTableView::item:selected {{
    background-color: rgba(255, 158, 29, 0.2);
    color: {PRIMARY};
    border-left: 3px solid {PRIMARY};
}}

/* --- SCROLLBARS --- */
QScrollBar:vertical {{
    border: none;
    background: {BG_SIDEBAR};
    width: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background: {TEXT_SEC};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* --- LABELS SPECIFIQUES --- */
/* Titres de page ou de section */
QLabel[class="page-title"] {{
    font-size: 24px;
    font-weight: bold;
    color: {TEXT_MAIN};
    margin-bottom: 15px;
}}

/* KPI Value (Gros chiffres) */
QLabel[class="kpi-value"] {{
    font-size: 36px;
    font-weight: 800;
    color: {PRIMARY};
}}

/* KPI Label (Petit texte) */
QLabel[class="kpi-label"] {{
    font-size: 14px;
    color: {TEXT_SEC};
    text-transform: uppercase;
    letter-spacing: 1px;
}}
"""
