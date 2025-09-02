from models.invoice import InvoiceModel
from views.dashboard_view import MainWindow

class DashboardController:
    def __init__(self, db_manager, main_window):
        self.db_manager = db_manager
        self.main_window = main_window.ui

        self.invoice_model = InvoiceModel(self.db_manager)
        self.view = MainWindow()

        # Remplacer le widget placeholder dans la MainWindow (index 0)
        dashboard_widget_index = 0
        old_widget = self.main_window.stacked_widget.widget(dashboard_widget_index)
        self.main_window.stacked_widget.removeWidget(old_widget)
        self.main_window.stacked_widget.insertWidget(dashboard_widget_index, self.view)

        # Connecter le signal de changement d'onglet pour rafraîchir les données
        self.main_window.stacked_widget.currentChanged.connect(self.on_tab_changed)

        # Charger les données une première fois si le dashboard est la vue initiale
        if self.main_window.stacked_widget.currentIndex() == dashboard_widget_index:
            self.load_dashboard_data()

    def on_tab_changed(self, index):
        """Appelé lorsque l'utilisateur change d'onglet."""
        # Vérifier si le nouvel onglet est le dashboard
        if self.main_window.stacked_widget.widget(index) == self.view:
            self.load_dashboard_data()

    def load_dashboard_data(self):
        """Charge les statistiques et met à jour la vue."""
        self.main_window.statusBar().showMessage("Chargement des statistiques du tableau de bord...")
        stats = self.invoice_model.get_dashboard_stats()
        self.view.update_stats(stats)
        self.main_window.statusBar().showMessage("Prêt")
