import sys
import getpass
from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog

from views.main_window import MainWindow
from views.login_dialog import LoginDialog
from core.db_manager import DBManager
from controllers.auth_controller import AuthController
from controllers.client_controller import ClientController
from controllers.product_controller import ProductController
from controllers.invoice_controller import InvoiceController
from controllers.dashboard_controller import DashboardController

def main():
    """Point d'entrée principal de l'application."""
    app = QApplication(sys.argv)

    # --- Connexion à la base de données ---
    db_password = getpass.getpass("Veuillez entrer le mot de passe de la base de données: ")
    db_manager = DBManager(
        host="localhost",
        database="facturation_db",
        user="root", # À remplacer par un utilisateur dédié
        password=db_password
    )

    if not db_manager.get_connection():
        QMessageBox.critical(None, "Erreur de Base de Données",
                             "Impossible de se connecter à la base de données. "
                             "Vérifiez vos identifiants et que le service MySQL est bien démarré.\n"
                             "L'application va se fermer.")
        sys.exit(1)

    # --- Processus d'authentification ---
    auth_controller = AuthController(db_manager)
    login_dialog = LoginDialog()

    user_data = None
    # Boucle de connexion
    while True:
        if login_dialog.exec() == QDialog.DialogCode.Accepted:
            username, password = login_dialog.get_credentials()
            user_data = auth_controller.check_credentials(username, password)
            if user_data:
                break # Succès, on sort de la boucle
            else:
                QMessageBox.warning(login_dialog, "Échec de la connexion",
                                    "Nom d'utilisateur ou mot de passe incorrect.")
        else:
            # L'utilisateur a annulé la connexion
            db_manager.close()
            sys.exit(0) # On quitte proprement

    # --- Lancement de l'interface principale ---
    main_window = MainWindow(user_data)
    # Personnaliser la barre de statut avec le nom de l'utilisateur
    main_window.statusBar().showMessage(f"Connecté en tant que: {user_data['full_name']} ({user_data['role']})")

    # --- Initialisation des contrôleurs des modules ---
    dashboard_controller = DashboardController(db_manager, main_window)
    client_controller = ClientController(db_manager, main_window)
    product_controller = ProductController(db_manager, main_window)
    invoice_controller = InvoiceController(db_manager, main_window, user_data)
    # Les autres contrôleurs (rapports, paramètres) seraient initialisés ici

    main_window.show()

    # --- Démarrage de la boucle d'événements ---
    exit_code = app.exec()

    # --- Nettoyage avant de quitter ---
    db_manager.close()

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
