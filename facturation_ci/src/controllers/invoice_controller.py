from PyQt6.QtWidgets import QMessageBox, QDialog, QFileDialog
from models.invoice import InvoiceModel
from models.client import ClientModel
from models.product import ProductModel
from views.invoice_view import InvoiceView
from views.invoice_editor_dialog import InvoiceEditorDialog
from core.fne_client import certify_document, FNEClientError
from core.pdf_generator import generate_invoice_pdf
import os
# Need to import QApplication for processEvents
from PyQt6.QtWidgets import QApplication

class InvoiceController:
    def __init__(self, db_manager, main_window, user_data):
        self.db_manager = db_manager
        self.main_window = main_window.ui
        self.user_data = user_data

        # Models
        self.invoice_model = InvoiceModel(self.db_manager)
        self.client_model = ClientModel(self.db_manager)
        self.product_model = ProductModel(self.db_manager)
        # TODO: Add a CompanyModel to get company_info and api_key
        self.company_data = {
            'name': 'Mon Entreprise SARL',
            'address': '123 Rue de la Facture, Abidjan',
            'phone': '+225 01 02 03 04 05',
            'email': 'contact@monentreprise.ci',
            'tax_id': 'CI-ABJ-2023-A-12345'
        }
        self.api_key = 'VOTRE_CLE_API_FNE_ICI'

        self.view = InvoiceView()

        # Replace placeholder in MainWindow
        invoice_widget_index = 1 # 'Factures' is at index 1
        old_widget = self.main_window.stacked_widget.widget(invoice_widget_index)
        self.main_window.stacked_widget.removeWidget(old_widget)
        self.main_window.stacked_widget.insertWidget(invoice_widget_index, self.view)

        self.connect_signals()
        self.load_invoices()

    def connect_signals(self):
        self.view.new_button.clicked.connect(self.open_new_invoice)
        self.view.view_button.clicked.connect(self.view_invoice)
        self.view.certify_button.clicked.connect(self.certify_invoice)
        self.view.pdf_button.clicked.connect(self.generate_pdf)

    def load_invoices(self):
        invoices = self.invoice_model.get_all_with_client_info()
        self.view.set_invoices(invoices)

    def open_new_invoice(self):
        dialog = InvoiceEditorDialog(
            client_model=self.client_model,
            product_model=self.product_model,
            mode='new',
            parent=self.main_window
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_invoice_data = dialog.get_data()
            if new_invoice_data:
                # Add user_id to the invoice details
                new_invoice_data['details']['user_id'] = self.user_data['id']

                invoice_id, error = self.invoice_model.create(new_invoice_data)
                if error:
                    QMessageBox.critical(self.main_window, "Erreur de Création", f"Impossible de créer la facture : {error}")
                else:
                    QMessageBox.information(self.main_window, "Succès", f"Facture #{invoice_id} créée avec succès en tant que brouillon.")
                    self.load_invoices()

    def view_invoice(self):
        invoice_id = self.view.get_selected_invoice_id()
        if invoice_id is None:
            QMessageBox.warning(self.main_window, "Aucune Sélection", "Veuillez sélectionner une facture à consulter.")
            return

        invoice_data = self.invoice_model.get_by_id(invoice_id)
        if not invoice_data:
            QMessageBox.critical(self.main_window, "Erreur", "Facture non trouvée.")
            return

        dialog = InvoiceEditorDialog(
            client_model=self.client_model,
            product_model=self.product_model,
            mode='read',
            invoice_data=invoice_data,
            parent=self.main_window
        )
        dialog.exec()

    def certify_invoice(self):
        invoice_id = self.view.get_selected_invoice_id()
        if invoice_id is None:
            QMessageBox.warning(self.main_window, "Aucune Sélection", "Veuillez sélectionner une facture à certifier.")
            return

        invoice_data = self.invoice_model.get_by_id(invoice_id)
        if not invoice_data:
            QMessageBox.critical(self.main_window, "Erreur", "Facture non trouvée.")
            return

        if invoice_data['details']['status'] != 'draft':
            QMessageBox.warning(self.main_window, "Action Impossible", f"Cette facture ne peut pas être certifiée (statut: {invoice_data['details']['status']}).")
            return

        # --- Données nécessaires pour l'API ---
        client_info = self.client_model.get_by_id(invoice_data['details']['client_id'])

        try:
            # Afficher un message d'attente
            self.main_window.statusBar().showMessage("Certification en cours auprès de la FNE...")
            QApplication.processEvents()

            fne_response = certify_document(invoice_data, self.company_data, client_info, self.user_data, self.api_key)

            # Mettre à jour la BDD avec la réponse FNE
            success = self.invoice_model.update_fne_data(
                invoice_id, 'success',
                nim=fne_response['nim'],
                qr_code=fne_response['qr_code']
            )
            if success:
                QMessageBox.information(self.main_window, "Succès", f"Facture #{invoice_id} certifiée avec succès.\nNIM: {fne_response['nim']}")
            else:
                raise FNEClientError("Impossible de sauvegarder la réponse FNE dans la base de données.")

        except FNEClientError as e:
            # En cas d'erreur de l'API, on met à jour la BDD pour tracer l'erreur
            self.invoice_model.update_fne_data(invoice_id, 'failed', error_message=str(e))
            QMessageBox.critical(self.main_window, "Erreur de Certification FNE", f"La certification a échoué:\n{e}")
        finally:
            self.load_invoices()
            self.main_window.statusBar().showMessage("Prêt")
            QApplication.processEvents()



    def generate_pdf(self):
        """Génère un PDF pour la facture sélectionnée."""
        invoice_id = self.view.get_selected_invoice_id()
        if invoice_id is None:
            QMessageBox.warning(self.main_window, "Aucune Sélection", "Veuillez sélectionner une facture à imprimer.")
            return

        invoice_data = self.invoice_model.get_by_id(invoice_id)
        if not invoice_data:
            QMessageBox.critical(self.main_window, "Erreur", "Facture non trouvée.")
            return

        if invoice_data['details']['status'] == 'draft':
            reply = QMessageBox.question(
                self.main_window, "Facture non certifiée",
                "Cette facture est un brouillon. Voulez-vous quand même générer un PDF (marqué comme 'PRO FORMA') ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        client_data = self.client_model.get_by_id(invoice_data['details']['client_id'])

        # Proposer un nom de fichier par défaut
        default_filename = f"FACTURE_{invoice_id}_{client_data['name']}.pdf".replace(' ', '_')
        filepath, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Enregistrer le PDF de la facture",
            os.path.join(os.path.expanduser("~"), "Documents", default_filename),
            "PDF Files (*.pdf)"
        )

        if not filepath:
            return # L'utilisateur a annulé

        try:
            self.main_window.statusBar().showMessage("Génération du PDF en cours...")
            generate_invoice_pdf(filepath, invoice_data, client_data, self.company_data)
            self.main_window.statusBar().showMessage("Prêt")
            QMessageBox.information(self.main_window, "Succès", f"Le fichier PDF a été enregistré avec succès:\n{filepath}")
        except Exception as e:
            self.main_window.statusBar().showMessage("Prêt")
            QMessageBox.critical(self.main_window, "Erreur de Génération PDF", f"Une erreur est survenue:\n{e}")
