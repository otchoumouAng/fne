import sys
import getpass
from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog

from core.db_manager import DBManager
from auth_dialog import AuthDialog
from main_window import MainWindow

# Import des nouveaux modules
from dashboard import DashboardModule
from client import ClientModule
from product import ProductModule
from invoice import InvoiceModule
from commande import CommandeModule
from settings import SettingsModule
from avoir_list_page import AvoirListPage

def main():
    """Point d'entrée principal de l'application refactorisée."""
    app = QApplication(sys.argv)

    # --- Connexion à la base de données ---
    try:
        db_manager = DBManager()
        # On force une première connexion pour vérifier que tout est OK avant de continuer.
        db_manager.get_connection()
    except ConnectionError as e:
        QMessageBox.critical(None, "Erreur de Base de Données",
                             f"{e}\n\nVérifiez vos identifiants et que le service MySQL est bien démarré.\n"
                             "L'application va se fermer.")
        sys.exit(1)

    # --- Processus d'authentification ---
    auth_dialog = AuthDialog(db_manager)
    if auth_dialog.exec() == QDialog.DialogCode.Accepted:
        user_data = auth_dialog.get_user_data()
        if not user_data:
            db_manager.close()
            sys.exit(0) # L'utilisateur a fermé la boîte de dialogue sans se connecter
    else:
        # L'utilisateur a annulé la connexion
        db_manager.close()
        sys.exit(0)

    # --- Lancement de l'interface principale ---
    main_window = MainWindow(user_data)

    # --- Initialisation des modules et insertion dans la MainWindow ---
    # Les index correspondent à l'ordre dans le QListWidget du .ui
    dashboard_module = DashboardModule(db_manager)
    main_window.set_module_widget(0, dashboard_module)

    commande_module = CommandeModule(db_manager, user_data, main_window)
    main_window.set_module_widget(1, commande_module)

    invoice_module = InvoiceModule(db_manager, user_data, main_window)
    main_window.set_module_widget(2, invoice_module)

    avoir_list_page = AvoirListPage(db_manager, main_window)
    main_window.set_module_widget(3, avoir_list_page)

    client_module = ClientModule(db_manager)
    main_window.set_module_widget(4, client_module)

    product_module = ProductModule(db_manager)
    main_window.set_module_widget(5, product_module)

    # Le module Rapports (index 6) n'est pas implémenté.
    settings_module = SettingsModule(db_manager)
    main_window.set_module_widget(7, settings_module)

    main_window.show()

    # --- Démarrage de la boucle d'événements ---
    exit_code = app.exec()

    # --- Nettoyage avant de quitter ---
    db_manager.close()

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
