from PyQt6.QtWidgets import QWidget, QMessageBox
from page._settings import Ui_SettingsPage
from models.company import CompanyInfoModel

class SettingsModule(QWidget):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.company_model = CompanyInfoModel(self.db_manager)

        self.ui = Ui_SettingsPage()
        self.ui.setupUi(self)

        self.load_company_info()
        self.setup_connections()

    def setup_connections(self):
        """Connecte les signaux aux slots."""
        self.ui.save_button.clicked.connect(self.save_company_info)

    def load_company_info(self):
        """Charge les informations de l'entreprise et remplit le formulaire."""
        company_info = self.company_model.get_first()
        if company_info:
            self.ui.name_edit.setText(company_info.get('name', ''))
            self.ui.address_edit.setPlainText(company_info.get('address', ''))
            self.ui.phone_edit.setText(company_info.get('phone', ''))
            self.ui.email_edit.setText(company_info.get('email', ''))
            self.ui.tax_id_edit.setText(company_info.get('ncc', ''))
            self.ui.pos_edit.setText(company_info.get('point_of_sale', ''))
            self.ui.fne_api_key_edit.setText(company_info.get('fne_api_key', ''))
            
            # --- DÉBUT DES AJOUTS ---
            self.ui.tax_regime_edit.setText(company_info.get('tax_regime', ''))
            self.ui.tax_office_edit.setText(company_info.get('tax_office', ''))
            self.ui.rccm_edit.setText(company_info.get('rccm', ''))
            self.ui.bank_details_edit.setText(company_info.get('bank_details', ''))
            self.ui.establishment_edit.setText(company_info.get('establishment', ''))
            # --- FIN DES AJOUTS ---
            
        else:
            print("Aucune information d'entreprise trouvée dans la base de données.")

    def get_form_data(self):
        """Récupère les données du formulaire sous forme de dictionnaire."""
        company_data = {
            'name': self.ui.name_edit.text(),
            'address': self.ui.address_edit.toPlainText(),
            'phone': self.ui.phone_edit.text(),
            'email': self.ui.email_edit.text(),
            'ncc': self.ui.tax_id_edit.text(),
            'point_of_sale': self.ui.pos_edit.text(),
            'fne_api_key': self.ui.fne_api_key_edit.text(),
            
            # --- DÉBUT DES AJOUTS ---
            'tax_regime': self.ui.tax_regime_edit.text(),
            'tax_office': self.ui.tax_office_edit.text(),
            'rccm': self.ui.rccm_edit.text(),
            'bank_details': self.ui.bank_details_edit.text(),
            'establishment': self.ui.establishment_edit.text()
            # --- FIN DES AJOUTS ---
        }
        return company_data

    def save_company_info(self):
        """Récupère les données du formulaire et les sauvegarde dans la base de données."""
        data = self.get_form_data()

        # Validation simple (inchangée, sauf si les nouveaux champs sont requis)
        if not data['name'] or not data['fne_api_key']:
            QMessageBox.warning(self, "Champs requis", "Le nom de l'entreprise et la clé d'API FNE sont requis.")
            return

        success, message = self.company_model.update_or_create(data)

        if success:
            QMessageBox.information(self, "Succès", "Les informations de l'entreprise ont été enregistrées avec succès.")
        else:
            QMessageBox.critical(self, "Erreur de Sauvegarde", f"Impossible d'enregistrer les informations : {message}")