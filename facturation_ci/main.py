import sys
import getpass
from PyQt6.QtWidgets import QApplication, QMessageBox

from core.db_manager import DBManager
from auth_dialog import AuthDialog
from main_window import MainWindow

# Import des nouveaux modules
from dashboard import DashboardModule
from client import ClientModule
from product import ProductModule
from invoice import InvoiceModule

def main():
    """Point d'entrée principal de l'application refactorisée."""
    app = QApplication(sys.argv)

    # --- Connexion à la base de données ---
    # Pour le développement, on peut hardcoder le mot de passe ou utiliser des variables d'environnement
    # db_password = getpass.getpass("Veuillez entrer le mot de passe de la base de données: ")
    db_password = "Admin@1234" # REMPLACER pour la production
    db_manager = DBManager(
        host="127.0.0.1",
        database="s_facture_plus", # Assurez-vous que c'est le bon nom de DB
        user="root",
        password=db_password
    )

    if not db_manager.get_connection():
        QMessageBox.critical(None, "Erreur de Base de Données",
                             "Impossible de se connecter à la base de données. "
                             "Vérifiez vos identifiants et que le service MySQL est bien démarré.\n"
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

    invoice_module = InvoiceModule(db_manager, user_data, main_window)
    main_window.set_module_widget(1, invoice_module)

    client_module = ClientModule(db_manager)
    main_window.set_module_widget(2, client_module)

    product_module = ProductModule(db_manager)
    main_window.set_module_widget(3, product_module)

    # Les autres modules (Rapports, Paramètres) ne sont pas implémentés
    # Leurs placeholders resteront.

    main_window.show()

    # --- Démarrage de la boucle d'événements ---
    exit_code = app.exec()

    # --- Nettoyage avant de quitter ---
    db_manager.close()

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
