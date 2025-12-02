from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtCore import Qt
from ui.theme import BG_CARD, TEXT_MAIN, TEXT_SEC, PRIMARY, SUCCESS, DANGER, BORDER

try:
    from PyQt6.QtCharts import QChart, QChartView, QBarSet, QBarSeries, QPieSeries, QBarCategoryAxis, QValueAxis
    CHARTS_AVAILABLE = True
except ImportError as e:
    CHARTS_AVAILABLE = False
    IMPORT_ERROR = str(e)
    # Define dummy classes to avoid NameError if import failed
    QChartView = QWidget
    QChart = object

class FallbackChart(QWidget):
    """Widget affiché en cas d'erreur de chargement des graphiques."""
    def __init__(self, error_msg, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel(f"Graphiques indisponibles.\nErreur: {error_msg}")
        label.setStyleSheet(f"color: {TEXT_SEC}; font-style: italic;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setStyleSheet(f"background-color: {BG_CARD}; border-radius: 12px; border: 1px solid {BORDER};")

    def update_data(self, data):
        pass # Do nothing

if CHARTS_AVAILABLE:
    class BaseChart(QChartView):
        def __init__(self, title="", parent=None):
            super().__init__(parent)
            self.chart = QChart()
            self.setChart(self.chart)
            self.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Style global du chart
            self.chart.setBackgroundBrush(QColor(BG_CARD))
            self.chart.setTitleBrush(QColor(TEXT_MAIN))
            self.chart.setTitleFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            self.chart.setTitle(title)
            self.chart.legend().setLabelColor(QColor(TEXT_SEC))
            self.chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)

            # Enlever les marges excessives
            self.chart.layout().setContentsMargins(0, 0, 0, 0)
            self.chart.setBackgroundRoundness(12)

    class RevenueBarChart(BaseChart):
        def __init__(self, parent=None):
            super().__init__("Chiffre d'Affaires (6 derniers mois)", parent)
            self.series = QBarSeries()
            self.chart.addSeries(self.series)

            # Axes
            self.axis_x = QBarCategoryAxis()
            self.axis_x.setLabelsColor(QColor(TEXT_SEC))
            self.axis_x.setGridLineVisible(False)
            self.chart.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
            self.series.attachAxis(self.axis_x)

            self.axis_y = QValueAxis()
            self.axis_y.setLabelsColor(QColor(TEXT_SEC))
            self.axis_y.setLabelFormat("%.0f")
            self.axis_y.setGridLineColor(QColor(BORDER))
            self.chart.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)
            self.series.attachAxis(self.axis_y)

        def update_data(self, data):
            """
            data: list of tuples (month_name, revenue_amount)
            Ex: [("Jan", 100000), ("Fev", 150000), ...]
            """
            self.series.clear()

            bar_set = QBarSet("Revenus")
            bar_set.setColor(QColor(PRIMARY))
            bar_set.setBorderColor(QColor(PRIMARY))

            categories = []
            max_val = 0

            for month, revenue in data:
                bar_set.append(revenue)
                categories.append(month)
                if revenue > max_val:
                    max_val = revenue

            self.series.append(bar_set)
            self.axis_x.setCategories(categories)
            self.axis_y.setRange(0, max_val * 1.1) # +10% de marge

    class StatusPieChart(BaseChart):
        def __init__(self, parent=None):
            super().__init__("Répartition des Factures", parent)
            self.series = QPieSeries()
            self.series.setHoleSize(0.4) # Donut style
            self.chart.addSeries(self.series)

            # Customisation des couleurs
            self.colors = {
                'paid': QColor(SUCCESS),     # Vert
                'certified': QColor(PRIMARY), # Orange
                'draft': QColor(TEXT_SEC),    # Gris
                'cancelled': QColor(DANGER)   # Rouge
            }

        def update_data(self, status_counts):
            """
            status_counts: dict {'paid': 10, 'draft': 5, ...}
            """
            self.series.clear()

            total = sum(status_counts.values())
            if total == 0:
                return

            map_labels = {
                'paid': 'Payées',
                'certified': 'Certifiées',
                'draft': 'Brouillons',
                'cancelled': 'Annulées'
            }

            for status, count in status_counts.items():
                if count > 0:
                    label = map_labels.get(status, status)
                    slice_ = self.series.append(label, count)
                    slice_.setBrush(self.colors.get(status, QColor(TEXT_SEC)))
                    slice_.setLabelVisible(True)
                    slice_.setLabelColor(QColor(TEXT_MAIN))
else:
    # Fallback Classes
    class RevenueBarChart(FallbackChart):
        def __init__(self, parent=None):
            super().__init__(IMPORT_ERROR, parent)

    class StatusPieChart(FallbackChart):
        def __init__(self, parent=None):
            super().__init__(IMPORT_ERROR, parent)
