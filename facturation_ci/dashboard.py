import sys
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt

from page._dashboard_view import Ui_DashboardView
from models.invoice import InvoiceModel

class DashboardModule(QWidget):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.invoice_model = InvoiceModel(self.db_manager)

        self.ui = Ui_DashboardView()
        self.ui.setupUi(self)

        self.setup_custom_style()
        self.load_stats()

    def setup_custom_style(self):
        """Applique les styles CSS spécifiques pour les classes de la Dashboard."""

        # Application des classes CSS définies dans theme.py

        # KPI Revenue
        self.ui.revenue_label.setProperty("class", "kpi-label")
        self.ui.revenue_value.setProperty("class", "kpi-value")

        # KPI Count
        self.ui.count_label.setProperty("class", "kpi-label")
        self.ui.invoice_count_value.setProperty("class", "kpi-value")

        # Titres de page (si existants, ici on utilise les titres de groupe)

        # Forcer la mise à jour du style
        self.setStyleSheet(self.styleSheet()) # Refresh cascade

    def load_stats(self):
        """Charge les statistiques et met à jour l'interface utilisateur."""
        stats = self.invoice_model.get_dashboard_stats()

        if not stats:
            # Handle case where stats can't be fetched
            return

        # Mise à jour des indicateurs clés
        revenue = stats.get('revenue_last_30_days', 0)
        invoice_count = stats.get('invoices_this_month', 0)

        self.ui.revenue_value.setText(f"{revenue:,.0f} XOF".replace(",", " "))

        self.ui.invoice_count_value.setText(str(invoice_count))

        # Mise à jour du résumé des statuts
        status_summary = stats.get('status_summary', {})

        # On pourrait styliser ces labels aussi
        self.ui.summary_draft_label.setText(f"Brouillons: {status_summary.get('draft', 0)}")
        self.ui.summary_certified_label.setText(f"Certifiées: {status_summary.get('certified', 0)}")
        self.ui.summary_paid_label.setText(f"Payées: {status_summary.get('paid', 0)}")
        self.ui.summary_cancelled_label.setText(f"Annulées: {status_summary.get('cancelled', 0)}")

    def refresh_data(self):
        """Méthode publique pour rafraîchir les données du tableau de bord."""
        self.load_stats()
