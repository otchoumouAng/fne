from PyQt6.QtWidgets import QMainWindow
from page._main_window import Ui_MainWindow

class MainWindow(QMainWindow):
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setup_navigation()
        self.setWindowTitle(f"Facturation - Connecté: {self.user_data['full_name']}")

    def setup_navigation(self):
        """Connecte le menu de navigation au QStackedWidget."""
        self.ui.nav_menu.currentRowChanged.connect(self.ui.stacked_widget.setCurrentIndex)
        # Set the initial page to Dashboard
        self.ui.nav_menu.setCurrentRow(0)

    def set_module_widget(self, index, widget):
        """Remplace un widget placeholder dans le QStackedWidget par le vrai module."""
        old_widget = self.ui.stacked_widget.widget(index)
        self.ui.stacked_widget.removeWidget(old_widget)
        self.ui.stacked_widget.insertWidget(index, widget)
        old_widget.deleteLater()
