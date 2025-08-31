import bcrypt
from mysql.connector import Error

class AuthController:
    def __init__(self, db_manager):
        """
        Initialise le contrôleur d'authentification.
        :param db_manager: Une instance de DBManager.
        """
        self.db_manager = db_manager
        self.current_user = None

    def check_credentials(self, username, password):
        """
        Vérifie les identifiants de l'utilisateur contre la base de données.
        :param username: Le nom d'utilisateur.
        :param password: Le mot de passe en clair.
        :return: Un dictionnaire avec les informations de l'utilisateur en cas de succès, sinon None.
        """
        connection = self.db_manager.get_connection()
        if not connection:
            print("Erreur: Impossible d'obtenir une connexion à la base de données.")
            return None

        cursor = None
        try:
            # Utiliser un dictionnaire pour le curseur est pratique pour récupérer les données par nom de colonne
            cursor = connection.cursor(dictionary=True)

            query = """
                SELECT u.id, u.username, u.full_name, u.password_hash, u.is_active, r.name as role
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.username = %s
            """
            cursor.execute(query, (username,))
            user_data = cursor.fetchone()

            if not user_data:
                print(f"Authentification échouée: L'utilisateur '{username}' n'existe pas.")
                return None

            if not user_data['is_active']:
                print(f"Authentification échouée: Le compte pour '{username}' est désactivé.")
                return None

            # Vérifier le mot de passe
            stored_hash = user_data['password_hash'].encode('utf-8')
            entered_password = password.encode('utf-8')

            if bcrypt.checkpw(entered_password, stored_hash):
                print(f"Authentification réussie pour l'utilisateur '{username}'.")
                self.current_user = user_data
                return user_data
            else:
                print(f"Authentification échouée: Mot de passe incorrect pour '{username}'.")
                return None

        except Error as e:
            print(f"Erreur de base de données lors de l'authentification: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def get_current_user(self):
        return self.current_user
