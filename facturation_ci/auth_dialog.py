from PyQt6.QtWidgets import QDialog, QMessageBox
import bcrypt

from page._login import Ui_LoginDialog

class AuthDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.user_data = None

        self.ui = Ui_LoginDialog()
        self.ui.setupUi(self)

        self.ui.button_box.accepted.connect(self.handle_login)

    def handle_login(self):
        username = self.ui.username_input.text()
        password = self.ui.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Champs vides", "Veuillez entrer un nom d'utilisateur et un mot de passe.")
            return

        user_data = self._check_credentials(username, password)
        if user_data:
            self.user_data = user_data
            self.accept()
        else:
            QMessageBox.warning(self, "Échec de la connexion", "Nom d'utilisateur ou mot de passe incorrect.")
            # Do not close the dialog, let the user try again.

    def _check_credentials(self, username, password):
        """Vérifie les identifiants et récupère les permissions de l'utilisateur."""
        connection = self.db_manager.get_connection()
        if not connection:
            return None

        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT
                u.id, u.username, u.password_hash, u.full_name, r.name as role,
                GROUP_CONCAT(p.name) as permissions
            FROM users u
            JOIN roles r ON u.role_id = r.id
            LEFT JOIN role_permissions rp ON r.id = rp.role_id
            LEFT JOIN permissions p ON rp.permission_id = p.id
            WHERE u.username = %s AND u.is_active = TRUE
            GROUP BY u.id
        """
        try:
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                # Remove password hash before returning user data
                del user['password_hash']
                # Convert permission string to a set for efficient lookups
                if user['permissions']:
                    user['permissions'] = set(user['permissions'].split(','))
                else:
                    user['permissions'] = set()
                return user
            return None
        except Exception as e:
            print(f"Erreur lors de la vérification des identifiants: {e}")
            return None
        finally:
            cursor.close()

    def get_user_data(self):
        """Retourne les données de l'utilisateur si la connexion a réussi."""
        return self.user_data
