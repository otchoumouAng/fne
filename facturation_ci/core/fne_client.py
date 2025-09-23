import requests
import json

# L'URL de base de l'API FNE. À mettre dans un fichier de configuration dans une app réelle.
FNE_API_BASE_URL = "http://54.247.95.108/ws/external"

class FNEClientError(Exception):
    """Exception personnalisée pour les erreurs du client FNE."""
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code

def certify_document(invoice_full_data: dict, company_info: dict, client_info: dict, user_info: dict, api_key: str):
    """
    Appelle l'API FNE pour certifier un document de vente ou d'achat.

    :param invoice_full_data: Dictionnaire contenant les détails de la facture et les lignes d'articles ('details' et 'items').
    :param company_info: Dictionnaire avec les informations de l'entreprise (tax_id).
    :param client_info: Dictionnaire avec les informations du client.
    :param user_info: Dictionnaire avec les informations de l'opérateur.
    :param api_key: La clé d'API de l'entreprise pour l'authentification.
    :return: Dictionnaire avec les données de certification FNE ('nim' et 'qrCode').
    :raises FNEClientError: En cas d'échec de la communication ou d'erreur de l'API.
    """
    invoice_details = invoice_full_data['details']
    doc_type = invoice_details['document_type'] # 'sale', 'purchase'

    if doc_type not in ["sale", "purchase"]:
        raise FNEClientError(f"Le type de document '{doc_type}' n'est pas supporté pour la signature.")

    endpoint = f"{FNE_API_BASE_URL}/invoices/sign"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Construire le payload JSON en fonction du type de document.
    if doc_type == "purchase":
        # Payload spécifique pour les Bordereaux d'Achat (nos BLs)
        payload = {
            "invoiceType": "purchase",
            "paymentMethod": "mobile-money", # Valeur par défaut, pourrait être configurable
            "template": "B2B", # Valeur par défaut
            "clientCompanyName": company_info.get("name"),
            "clientPhone": company_info.get("phone"),
            "clientEmail": company_info.get("email"),
            "items": [
                {
                    "description": item['description'],
                    "quantity": float(item['quantity']),
                    "amount": float(item['unit_price']) # 'amount' est le prix unitaire ici
                }
                for item in invoice_full_data.get('items', [])
            ]
        }
    else: # 'sale'
        # Payload pour les factures de vente
        payload = {
            "type": doc_type,
            "ifuid": company_info.get("tax_id"),
            "operator": {
                "id": user_info.get("id"),
                "name": user_info.get("full_name", "Opérateur")
            },
            "items": [
                {
                    "name": item['description'],
                    "price": float(item['unit_price']),
                    "quantity": float(item['quantity'])
                }
                for item in invoice_full_data.get('items', [])
            ],
            "client": {
                "name": client_info.get("name"),
                "address": client_info.get("address")
            },
            # ... autres champs requis par la DGI (ex: `payment`, `invoice`)
        }

    try:
        response = requests.post(endpoint, headers=headers, data=json.dumps(payload), timeout=20)
        response.raise_for_status()

        response_data = response.json()

        if response_data.get("status") == "success" and "data" in response_data:
            fne_data = response_data["data"]
            fne_invoice_data = fne_data.get("invoice", {})
            fne_items = fne_invoice_data.get("items", [])

            # On suppose que l'ordre des articles est conservé entre la requête et la réponse.
            # On récupère les IDs locaux des articles qu'on a envoyés.
            local_item_ids = [item['id'] for item in invoice_full_data.get('items', [])]

            # On crée une map entre les IDs FNE et les IDs locaux.
            items_id_map = []
            if len(fne_items) == len(local_item_ids):
                items_id_map = [
                    (fne_item['id'], local_item_id)
                    for fne_item, local_item_id in zip(fne_items, local_item_ids)
                ]

            # On retourne toutes les données nécessaires au contrôleur.
            return {
                "fne_invoice_data": fne_invoice_data,
                "items_id_map": items_id_map
            }

        error_msg = response_data.get('message', json.dumps(response_data))
        raise FNEClientError(f"Réponse invalide de l'API FNE: {error_msg}", response.status_code)

    except requests.exceptions.HTTPError as e:
        error_details = "Détail de l'erreur non disponible."
        try:
            error_details = e.response.json().get('message', e.response.text)
        except json.JSONDecodeError:
            pass
        raise FNEClientError(f"Erreur API FNE ({e.response.status_code}): {error_details}", e.response.status_code)

    except requests.exceptions.RequestException as e:
        raise FNEClientError(f"Erreur de communication avec l'API FNE: {e}")
    except Exception as e:
        raise FNEClientError(f"Erreur inattendue lors de la certification: {e}")


def refund_invoice(api_key: str, original_fne_invoice_id: str, items_to_refund: list):
    """
    Appelle l'API FNE pour créer un avoir (refund) sur une facture existante.

    :param api_key: La clé d'API de l'entreprise.
    :param original_fne_invoice_id: L'ID FNE unique de la facture de vente d'origine.
    :param items_to_refund: Une liste de dictionnaires, chacun avec 'id' (FNE item id) et 'quantity'.
    :return: Dictionnaire avec les données de l'avoir certifié.
    :raises FNEClientError: En cas d'échec.
    """
    endpoint = f"{FNE_API_BASE_URL}/external/invoices/{original_fne_invoice_id}/refund"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "items": items_to_refund
    }

    try:
        response = requests.post(endpoint, headers=headers, data=json.dumps(payload), timeout=20)
        response.raise_for_status()

        response_data = response.json()

        if response_data.get("status") == "success" and "data" in response_data:
            return response_data["data"]

        error_msg = response_data.get('message', json.dumps(response_data))
        raise FNEClientError(f"Réponse invalide de l'API FNE pour l'avoir: {error_msg}", response.status_code)

    except requests.exceptions.HTTPError as e:
        error_details = "Détail de l'erreur non disponible."
        try:
            error_details = e.response.json().get('message', e.response.text)
        except json.JSONDecodeError:
            pass
        raise FNEClientError(f"Erreur API FNE ({e.response.status_code}) lors de la création de l'avoir: {error_details}", e.response.status_code)

    except requests.exceptions.RequestException as e:
        raise FNEClientError(f"Erreur de communication avec l'API FNE: {e}")
    except Exception as e:
        raise FNEClientError(f"Erreur inattendue lors de la création de l'avoir: {e}")
