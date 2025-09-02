from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout,QHBoxLayout, QGridLayout, QGroupBox, QLabel
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class DashboardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        grid_layout = QGridLayout()
        main_layout.addLayout(grid_layout)

        # --- Indicateurs Clés ---
        kpi_group = self.create_kpi_group()
        grid_layout.addWidget(kpi_group, 0, 0, 1, 2) # Span 1 row, 2 columns

        # --- Résumé des Factures ---
        summary_group = self.create_summary_group()
        grid_layout.addWidget(summary_group, 1, 0)

        # --- Placeholder pour d'autres stats ---
        placeholder_group = QGroupBox("Autres Statistiques")
        placeholder_layout = QVBoxLayout(placeholder_group)
        placeholder_layout.addWidget(QLabel("Graphiques ou autres indicateurs à venir..."))
        grid_layout.addWidget(placeholder_group, 1, 1)

    def create_kpi_group(self):
        """Crée le groupe pour les indicateurs de performance clés (KPI)."""
        kpi_group = QGroupBox("Indicateurs Clés")
        kpi_layout = QHBoxLayout(kpi_group)

        # Revenus 30 derniers jours
        revenue_layout = QVBoxLayout()
        revenue_label = QLabel("Chiffre d'affaires (30j)")
        self.revenue_value = self.create_kpi_value_label()
        revenue_layout.addWidget(revenue_label, alignment=Qt.AlignmentFlag.AlignCenter)
        revenue_layout.addWidget(self.revenue_value, alignment=Qt.AlignmentFlag.AlignCenter)
        kpi_layout.addLayout(revenue_layout)

        # Factures ce mois-ci
        count_layout = QVBoxLayout()
        count_label = QLabel("Factures (ce mois-ci)")
        self.invoice_count_value = self.create_kpi_value_label()
        count_layout.addWidget(count_label, alignment=Qt.AlignmentFlag.AlignCenter)
        count_layout.addWidget(self.invoice_count_value, alignment=Qt.AlignmentFlag.AlignCenter)
        kpi_layout.addLayout(count_layout)

        return kpi_group

    def create_summary_group(self):
        """Crée le groupe pour le résumé des statuts de factures."""
        summary_group = QGroupBox("Résumé des Factures")
        summary_layout = QGridLayout(summary_group)

        self.summary_draft_label = QLabel("Brouillons: 0")
        self.summary_certified_label = QLabel("Certifiées: 0")
        self.summary_paid_label = QLabel("Payées: 0")
        self.summary_cancelled_label = QLabel("Annulées: 0")

        summary_layout.addWidget(self.summary_draft_label, 0, 0)
        summary_layout.addWidget(self.summary_certified_label, 0, 1)
        summary_layout.addWidget(self.summary_paid_label, 1, 0)
        summary_layout.addWidget(self.summary_cancelled_label, 1, 1)

        return summary_group

    def create_kpi_value_label(self):
        """Helper pour créer un label de valeur formaté pour les KPIs."""
        label = QLabel("0")
        font = QFont("Arial", 24, QFont.Weight.Bold)
        label.setFont(font)
        label.setStyleSheet("color: #005B9A;")
        return label

    def update_stats(self, stats):
        """Met à jour les labels avec les nouvelles statistiques."""
        self.revenue_value.setText(f"{stats.get('revenue_last_30_days', 0):.2f} €")
        self.invoice_count_value.setText(str(stats.get('invoices_this_month', 0)))

        summary = stats.get('status_summary', {})
        self.summary_draft_label.setText(f"Brouillons: {summary.get('draft', 0)}")
        self.summary_certified_label.setText(f"Certifiées: {summary.get('certified', 0)}")
        self.summary_paid_label.setText(f"Payées: {summary.get('paid', 0) + summary.get('partially_paid', 0)}")
        self.summary_cancelled_label.setText(f"Annulées: {summary.get('cancelled', 0)}")
