import mysql.connector
from mysql.connector import Error
import sys

class DBManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DBManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, host=None, database=None, user=None, password=None):
        # The __init__ will be called every time, but we only connect once.
        if not hasattr(self, 'connection') or self.connection is None:
            if not all([host, database, user, password]):
                # This prevents re-initialization without parameters
                self.connection = None
                return

            self.host = host
            self.database = database
            self.user = user
            self.password = password
            self.connection = None
            self.connect()

    def connect(self):
        """Établit la connexion à la base de données."""
        if self.connection and self.connection.is_connected():
            return

        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            print("Connexion à la base de données réussie.")
        except Error as e:
            print(f"Erreur de connexion à la base de données : {e}")
            # Dans une vraie application, on afficherait une boîte de dialogue d'erreur.
            self.connection = None
            # On pourrait vouloir quitter l'application si la BDD est indisponible au démarrage.
            # sys.exit(1)

    def get_connection(self):
        """Retourne l'objet de connexion. Tente de se reconnecter si nécessaire."""
        if not self.connection or not self.connection.is_connected():
            print("Connexion perdue. Tentative de reconnexion...")
            self.connect()
        return self.connection

    def close(self):
        """Ferme la connexion à la base de données."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.connection = None
            print("Connexion à la base de données fermée.")

# Exemple d'utilisation (Singleton)
# from db_manager import DBManager
# db = DBManager(host='localhost', database='facturation_db', user='user', password='password')
# connection = db.get_connection()
# if connection:
#     cursor = connection.cursor()
#     # ... faire quelque chose
#     db.close()
