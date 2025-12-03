import sys
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFrame
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt

from page._dashboard_view import Ui_DashboardView
from models.invoice import InvoiceModel
from charts import RevenueBarChart, StatusPieChart

class DashboardModule(QWidget):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.invoice_model = InvoiceModel(self.db_manager)

        self.ui = Ui_DashboardView()
        self.ui.setupUi(self)

        self.setup_charts()
        self.setup_custom_style()
        self.load_stats()

    def setup_custom_style(self):
        """Applique les styles CSS spécifiques pour les classes de la Dashboard."""
        # KPI Revenue
        self.ui.revenue_label.setProperty("class", "kpi-label")
        self.ui.revenue_value.setProperty("class", "kpi-value")
        # KPI Count
        self.ui.count_label.setProperty("class", "kpi-label")
        self.ui.invoice_count_value.setProperty("class", "kpi-value")

        self.setStyleSheet(self.styleSheet()) # Refresh cascade

    def setup_charts(self):
        """Intègre les graphiques dans le layout."""
        # On va remplacer le placeholder_group par nos graphiques
        # Le layout existant est un QGridLayout

        # 1. Nettoyer le placeholder
        if self.ui.placeholder_group.layout():
             # Vider le layout existant s'il y a des items
             pass
        else:
             self.ui.placeholder_group.setLayout(QVBoxLayout())

        # On remplace tout le contenu du groupe par un layout horizontal contenant les 2 charts
        # En fait, le placeholder_group est à droite. On va y mettre le Pie Chart (Status).
        # Et on va ajouter le Bar Chart (Revenue) en bas, ou à la place.

        # Stratégie :
        # - Utiliser placeholder_group pour le Pie Chart
        # - Ajouter une nouvelle ligne au grid layout pour le Bar Chart (qui prend toute la largeur)

        # Setup Pie Chart (dans placeholder_group)
        self.pie_chart = StatusPieChart()
        layout_pie = QVBoxLayout()
        layout_pie.addWidget(self.pie_chart)
        # On doit supprimer les widgets existants du placeholder (label)
        for i in reversed(range(self.ui.placeholder_group.layout().count())):
            self.ui.placeholder_group.layout().itemAt(i).widget().setParent(None)

        # On remplace le layout ou on ajoute au layout existant (qui est un QVBoxLayout dans le .ui)
        self.ui.placeholder_group.layout().addWidget(self.pie_chart)
        self.ui.placeholder_group.setTitle("Répartition")

        # Setup Bar Chart (Nouvelle section en bas)
        self.bar_chart = RevenueBarChart()
        # Le layout principal est un QVBoxLayout qui contient un QGridLayout
        # self.ui.verticalLayout contient self.gridLayout

        # On ajoute le bar chart au layout principal (verticalLayout) en dessous du grid
        self.ui.verticalLayout.addWidget(self.bar_chart)
        # On lui donne une hauteur minimum
        self.bar_chart.setMinimumHeight(300)

    def load_stats(self):
        """Charge les statistiques et met à jour l'interface utilisateur."""
        stats = self.invoice_model.get_dashboard_stats()
        revenue_data = self.invoice_model.get_revenue_per_month(6)

        if not stats:
            return

        # Mise à jour des indicateurs clés
        revenue = stats.get('revenue_last_30_days', 0)
        invoice_count = stats.get('invoices_this_month', 0)

        self.ui.revenue_value.setText(f"{revenue:,.0f} XOF".replace(",", " "))
        self.ui.invoice_count_value.setText(str(invoice_count))

        # Mise à jour du résumé des statuts
        status_summary = stats.get('status_summary', {})

        self.ui.summary_draft_label.setText(f"Brouillons: {status_summary.get('draft', 0)}")
        self.ui.summary_certified_label.setText(f"Certifiées: {status_summary.get('certified', 0)}")
        self.ui.summary_paid_label.setText(f"Payées: {status_summary.get('paid', 0)}")
        self.ui.summary_cancelled_label.setText(f"Annulées: {status_summary.get('cancelled', 0)}")

        # Mise à jour des graphiques
        self.pie_chart.update_data(status_summary)
        self.bar_chart.update_data(revenue_data)

    def refresh_data(self):
        """Méthode publique pour rafraîchir les données du tableau de bord."""
        self.load_stats()
