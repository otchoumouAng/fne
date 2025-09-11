import json
from mysql.connector import Error
from datetime import datetime

class FactureAvoirModel:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def create(self, original_facture_id, code_facture_origine, avoir_items, totals):
        """
        Crée une nouvelle facture d'avoir dans la base de données.

        :param original_facture_id: ID de la facture d'origine.
        :param code_facture_origine: Code de la facture d'origine pour le code de l'avoir.
        :param avoir_items: Liste des dictionnaires d'articles pour l'avoir.
        :param totals: Dictionnaire contenant total_ht, total_tva, total_ttc.
        """
        connection = self.db_manager.get_connection()
        if not connection:
            return None, "Erreur de connexion à la BDD."

        cursor = connection.cursor()
        try:
            # Générer un code d'avoir unique
            # Pourrait être plus robuste en vérifiant l'unicité dans une boucle
            code_avoir = f"AV-{code_facture_origine}"

            query = """
                INSERT INTO factures_avoir
                (code_avoir, facture_origine_id, date_creation, lignes_avoir, total_ht, total_tva, total_ttc)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            today = datetime.now().date()
            items_json = json.dumps(avoir_items) # Convertir la liste d'items en chaîne JSON

            values = (
                code_avoir,
                original_facture_id,
                today,
                items_json,
                totals['total_ht'],
                totals['total_tva'],
                totals['total_ttc']
            )

            cursor.execute(query, values)
            avoir_id = cursor.lastrowid
            connection.commit()

            print(f"Facture d'avoir ID {avoir_id} ({code_avoir}) créée avec succès.")
            return avoir_id, None

        except Error as e:
            connection.rollback()
            error_message = f"Erreur lors de la création de la facture d'avoir: {e}"
            print(error_message)
            return None, error_message
        finally:
            cursor.close()
