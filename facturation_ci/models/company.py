from mysql.connector import Error

class CompanyInfoModel:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_first(self):
        """
        Récupère les informations de la première entreprise trouvée.
        Dans une application réelle, on pourrait vouloir un ID spécifique.
        """
        connection = self.db_manager.get_connection()
        if not connection:
            return None

        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM company_info ORDER BY id LIMIT 1"
        try:
            cursor.execute(query)
            company_info = cursor.fetchone()
            return company_info
        except Error as e:
            print(f"Erreur lors de la récupération des informations de l'entreprise: {e}")
            return None
        finally:
            cursor.close()
