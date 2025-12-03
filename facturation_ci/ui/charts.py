from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QPainterPath
from PyQt6.QtCore import Qt, QRectF, QPointF
from ui.theme import BG_CARD, TEXT_MAIN, TEXT_SEC, PRIMARY, SUCCESS, DANGER, BORDER, BG_SIDEBAR

class BaseCustomChart(QWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.title = title
        self.setStyleSheet(f"background-color: {BG_CARD}; border-radius: 12px; border: 1px solid {BORDER};")
        self.setMinimumHeight(300)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fond
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 12, 12)
        painter.fillPath(path, QColor(BG_CARD))

        # Bordure
        pen = QPen(QColor(BORDER))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawPath(path)

        # Titre
        if self.title:
            painter.setPen(QColor(TEXT_MAIN))
            painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            painter.drawText(QRectF(20, 15, self.width()-40, 30), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, self.title)

class RevenueBarChart(BaseCustomChart):
    def __init__(self, parent=None):
        super().__init__("Chiffre d'Affaires (6 derniers mois)", parent)
        self.data = [] # List of (month, value)
        self.max_value = 100

    def update_data(self, data):
        self.data = data
        if self.data:
            self.max_value = max([v for k, v in data]) * 1.1 if data else 100
        self.update() # Trigger repaint

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Marges
        margin_left = 60
        margin_bottom = 40
        margin_top = 60
        margin_right = 20

        graph_width = self.width() - margin_left - margin_right
        graph_height = self.height() - margin_top - margin_bottom

        # Dessiner les axes
        pen_axis = QPen(QColor(TEXT_SEC))
        pen_axis.setWidth(1)
        painter.setPen(pen_axis)

        # Axe Y
        painter.drawLine(margin_left, margin_top, margin_left, self.height() - margin_bottom)
        # Axe X
        painter.drawLine(margin_left, self.height() - margin_bottom, self.width() - margin_right, self.height() - margin_bottom)

        # Dessiner les barres
        bar_width = graph_width / len(self.data) * 0.6
        spacing = graph_width / len(self.data) * 0.4

        bar_brush = QBrush(QColor(PRIMARY))

        for i, (month, value) in enumerate(self.data):
            x = margin_left + (spacing / 2) + (i * (bar_width + spacing))

            if self.max_value > 0:
                bar_height = (value / self.max_value) * graph_height
            else:
                bar_height = 0

            y = self.height() - margin_bottom - bar_height

            # Barre
            rect = QRectF(x, y, bar_width, bar_height)
            painter.setBrush(bar_brush)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 4, 4)

            # Label X (Mois)
            painter.setPen(QColor(TEXT_SEC))
            painter.setFont(QFont("Segoe UI", 9))
            label_rect = QRectF(x - 10, self.height() - margin_bottom + 5, bar_width + 20, 20)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, month)

            # Label Y (Valeur au dessus)
            painter.setPen(QColor(TEXT_MAIN))
            value_rect = QRectF(x - 10, y - 20, bar_width + 20, 20)
            # Afficher 1k, 1M etc pour la lisibilité si besoin, ici simple
            display_val = f"{value/1000:.0f}k" if value >= 1000 else f"{value:.0f}"
            painter.drawText(value_rect, Qt.AlignmentFlag.AlignCenter, display_val)

class StatusPieChart(BaseCustomChart):
    def __init__(self, parent=None):
        super().__init__("Répartition des Factures", parent)
        self.status_counts = {}
        self.colors = {
            'paid': QColor(SUCCESS),
            'certified': QColor(PRIMARY),
            'draft': QColor(TEXT_SEC),
            'cancelled': QColor(DANGER)
        }
        self.labels_map = {
            'paid': 'Payées',
            'certified': 'Certifiées',
            'draft': 'Brouillons',
            'cancelled': 'Annulées'
        }

    def update_data(self, status_counts):
        self.status_counts = status_counts
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)

        total = sum(self.status_counts.values())
        if total == 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dimensions pour le Pie
        margin_top = 50
        pie_size = min(self.width(), self.height() - margin_top) * 0.8
        center_x = self.width() / 3  # Pie à gauche
        center_y = (self.height() + margin_top) / 2

        rect = QRectF(center_x - pie_size/2, center_y - pie_size/2, pie_size, pie_size)

        start_angle = 90 * 16 # Qt utilise des 1/16ème de degrés

        # Dessin du Donut
        for status, count in self.status_counts.items():
            if count > 0:
                span_angle = -(count / total) * 360 * 16
                color = self.colors.get(status, QColor(TEXT_SEC))

                painter.setBrush(QBrush(color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPie(rect, int(start_angle), int(span_angle))

                start_angle += span_angle

        # Trou du Donut
        hole_size = pie_size * 0.6
        hole_rect = QRectF(center_x - hole_size/2, center_y - hole_size/2, hole_size, hole_size)
        painter.setBrush(QBrush(QColor(BG_CARD)))
        painter.drawEllipse(hole_rect)

        # Légende (à droite)
        legend_x = self.width() * 0.6
        legend_y = margin_top + 20
        legend_spacing = 30

        painter.setFont(QFont("Segoe UI", 10))

        for status, count in self.status_counts.items():
            if count > 0:
                color = self.colors.get(status, QColor(TEXT_SEC))
                label = self.labels_map.get(status, status)

                # Carré de couleur
                painter.setBrush(QBrush(color))
                painter.drawRoundedRect(QRectF(legend_x, legend_y, 15, 15), 3, 3)

                # Texte
                painter.setPen(QColor(TEXT_MAIN))
                painter.drawText(QRectF(legend_x + 25, legend_y, 200, 20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"{label} ({count})")

                legend_y += legend_spacing
