from mysql.connector import Error

class BordereauLivraisonModel:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_by_facture_id(self, facture_id):
        """
        Récupère les détails d'un BL et les informations associées (facture, commande, client, items)
        à partir d'un ID de facture.
        """
        connection = self.db_manager.get_connection()
        if not connection:
            return None

        data = {}
        cursor = connection.cursor(dictionary=True)
        try:
            # Cette requête complexe joint toutes les tables nécessaires
            query = """
                SELECT
                    bl.id as bl_id, bl.code_bl, bl.date_creation as bl_date_creation,
                    f.id as facture_id, f.code_facture, f.date_facturation,
                    cmd.id as commande_id, cmd.code_commande, cmd.date_commande,
                    c.id as client_id, c.name as client_name, c.address as client_address,
                    c.email as client_email, c.phone as client_phone
                FROM bordereaux_livraison bl
                JOIN factures f ON bl.facture_id = f.id
                JOIN commandes cmd ON f.commande_id = cmd.id
                JOIN clients c ON cmd.client_id = c.id
                WHERE f.id = %s
            """
            cursor.execute(query, (facture_id,))
            data['details'] = cursor.fetchone()

            if not data['details']:
                return None

            # Récupérer les lignes d'articles depuis la commande
            commande_id = data['details']['commande_id']
            cursor.execute("SELECT * FROM commande_items WHERE commande_id = %s", (commande_id,))
            data['items'] = cursor.fetchall()

            return data
        except Error as e:
            print(f"Erreur lors de la récupération du BL pour la facture {facture_id}: {e}")
            return None
        finally:
            cursor.close()
