from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QStackedWidget, QLabel, QListWidgetItem
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QSize

class MainWindow(QMainWindow):
    def __init__(self, user_data, parent=None):
        super().__init__(parent)

        self.user_data = user_data
        self.setWindowTitle("Logiciel de Facturation")
        self.setGeometry(100, 100, 1200, 700)

        self.setup_ui()

    def setup_ui(self):
        # --- Création du widget central et du layout principal ---
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # --- Menu de navigation à gauche ---
        self.nav_menu = QListWidget()
        self.nav_menu.setFixedWidth(180)
        self.nav_menu.itemSelectionChanged.connect(self.change_view)
        main_layout.addWidget(self.nav_menu)

        # --- Zone d'affichage principale à droite (contenu) ---
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # --- Ajout des vues au menu et au stacked widget ---
        self.add_view("Dashboard", QLabel("Contenu du Dashboard"))
        self.add_view("Factures", QLabel("Contenu des Factures"))
        self.add_view("Clients", QLabel("Contenu des Clients"))
        self.add_view("Produits", QLabel("Contenu des Produits"))
        self.add_view("Rapports", QLabel("Contenu des Rapports"))
        self.add_view("Paramètres", QLabel("Contenu des Paramètres"))

        # --- Barre de statut ---
        self.statusBar().showMessage("Prêt")

        # Sélectionner le premier élément par défaut
        self.nav_menu.setCurrentRow(0)

    def add_view(self, name, widget):
        """Ajoute une vue au menu de navigation et au QStackedWidget."""
        # Pour l'instant, on utilise le widget passé. Plus tard, ce sera une classe de vue.
        self.stacked_widget.addWidget(widget)

        item = QListWidgetItem(name)
        # On pourrait ajouter une icône ici avec QIcon
        # item.setIcon(QIcon("path/to/icon.png"))
        self.nav_menu.addItem(item)

    def change_view(self):
        """Change la vue affichée dans le QStackedWidget en fonction du menu."""
        selected_row = self.nav_menu.currentRow()
        self.stacked_widget.setCurrentIndex(selected_row)

        # Mettre à jour la barre de statut
        selected_item = self.nav_menu.item(selected_row)
        self.statusBar().showMessage(f"Module : {selected_item.text()}")

# Pour tester cette fenêtre seule
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
