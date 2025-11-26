import sys
import os
import webbrowser
from PyQt6.QtWidgets import QWidget, QMessageBox, QDialog, QMenu
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QAction
from PyQt6.QtCore import Qt, QThread

# Imports adaptés pour le nouveau module Facture
from page._invoice import Ui_FacturePage # Le nom de classe dans le .py généré
from models.facture import FactureModel
from models.client import ClientModel
from models.company import CompanyInfoModel
from models.bl import BordereauLivraisonModel
from models.avoir import FactureAvoirModel
import core.fne_client as fne_client
# L'éditeur de facture est maintenant un dialogue de recherche de commande
from new_invoice_dialog import NewInvoiceDialog
from commande_editor_dialog import CommandeEditorDialog
from bl_viewer_dialog import BLViewerDialog
from credit_note_editor import CreditNoteEditorDialog
from core.pdf_generator import PDFGenerator
# Le worker n'est plus utilisé ici directement, mais dans le générateur
from core.worker import Worker

class InvoiceModule(QWidget):
    def __init__(self, db_manager, user_data, main_window, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.user_data = user_data
        self.main_window = main_window
        self.model = FactureModel(self.db_manager)
        self.client_model = ClientModel(self.db_manager)
        self.company_model = CompanyInfoModel(self.db_manager)
        self.bl_model = BordereauLivraisonModel(self.db_manager)
        self.avoir_model = FactureAvoirModel(self.db_manager)
        self.thread = None
        self.worker = None
        self.is_task_running = False

        self.ui = Ui_FacturePage()
        self.ui.setupUi(self)

        self.setup_buttons()
        self.load_invoices()
        self.connect_signals()

    def setup_buttons(self):
        # Désactiver les boutons qui nécessitent une sélection
        self.ui.certify_button.setEnabled(False)
        self.ui.print_button.setEnabled(False)
        self.ui.bl_button.setEnabled(False)
        self.ui.create_credit_note_button.setEnabled(False)

        # Configurer le menu pour le bouton BL
        bl_menu = QMenu(self)
        self.view_bl_action = bl_menu.addAction("Voir le BL")
        self.certify_bl_action = bl_menu.addAction("Certifier BL (FNE)")
        self.print_bl_action = bl_menu.addAction("Imprimer le BL")
        self.ui.bl_button.setMenu(bl_menu)

    def connect_signals(self):
        self.ui.new_invoice_button.clicked.connect(self.open_new_invoice_dialog)
        self.ui.table_view.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.ui.table_view.doubleClicked.connect(self.handle_facture_double_click)

        # Connecter les actions des boutons
        self.ui.certify_button.clicked.connect(self.certify_invoice)
        self.ui.print_button.clicked.connect(self.print_invoice)

        # Connecter les actions du menu BL
        self.view_bl_action.triggered.connect(self.view_bl)
        self.certify_bl_action.triggered.connect(self.certify_bl)
        self.print_bl_action.triggered.connect(self.print_bl)

        # Connecter l'action du nouveau bouton
        self.ui.create_credit_note_button.clicked.connect(self.create_credit_note)

    def on_selection_changed(self, selected, deselected):
        is_selection = self.ui.table_view.selectionModel().hasSelection()
        self.ui.certify_button.setEnabled(is_selection)
        self.ui.print_button.setEnabled(is_selection)
        self.ui.bl_button.setEnabled(is_selection)
        self.ui.create_credit_note_button.setEnabled(is_selection)

    def load_invoices(self):
        invoices = self.model.get_all_with_details()
        self.set_invoices_in_view(invoices)

    def set_invoices_in_view(self, invoices):
        if self.ui.table_view.model():
            self.ui.table_view.model().clear()

        model = QStandardItemModel()
        header = ['ID', 'Code Facture', 'Code Commande', 'Client', 'Date Facturation', 'Total TTC', 'Statut FNE']
        model.setHorizontalHeaderLabels(header)
        self.ui.table_view.setModel(model)

        for inv in invoices:
            row = [
                QStandardItem(str(inv['id'])),
                QStandardItem(inv['code_facture']),
                QStandardItem(inv['code_commande']),
                QStandardItem(inv['client_name']),
                QStandardItem(inv['date_facturation'].strftime('%Y-%m-%d')),
                QStandardItem(f"{inv['total_ttc']:.2f}"),
                QStandardItem(inv['statut_fne'])
            ]
            model.appendRow(row)

        self.ui.table_view.setColumnHidden(0, True)
        self.ui.table_view.resizeColumnsToContents()

    def get_selected_invoice_id(self):
        selected_indexes = self.ui.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            return None
        model = self.ui.table_view.model()
        id_index = model.index(selected_indexes[0].row(), 0)
        return int(model.data(id_index)) if model.data(id_index) else None

    # --- MÉTHODES D'ACTION (STUBS POUR L'INSTANT) ---

    def open_new_invoice_dialog(self):
        dialog = NewInvoiceDialog(self.db_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            commande_id = dialog.get_selected_commande_id()
            if commande_id:
                facture_id, error = self.model.create_from_commande(commande_id)
                if error:
                    QMessageBox.critical(self, "Erreur de Création", f"Impossible de générer la facture : {error}")
                else:
                    QMessageBox.information(self, "Succès", f"Facture ID {facture_id} générée avec succès.")
                    self.load_invoices()

    def certify_invoice(self):
        if self.is_task_running:
            QMessageBox.warning(self, "Tâche en cours", "Une autre tâche est déjà en cours. Veuillez patienter.")
            return

        invoice_id = self.get_selected_invoice_id()
        if not invoice_id: return

        # Récupérer toutes les données nécessaires
        invoice_data = self.model.get_by_id_for_printing(invoice_id)
        if not invoice_data:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les données de la facture {invoice_id}.")
            return

        if invoice_data['details']['statut_fne'] == 'success':
            QMessageBox.information(self, "Déjà certifiée", "Cette facture a déjà été certifiée avec succès.")
            return

        company_info = self.company_model.get_first()
        if not company_info or not company_info.get('fne_api_key') or not company_info.get('ncc'):
            QMessageBox.critical(self, "Erreur de configuration",
                                 "Les informations de l'entreprise sont incomplètes.\n"
                                 "Veuillez renseigner le NCC et la clé d'API FNE dans les paramètres.")
            return

        # Le FNE client attend des infos spécifiques, on les prépare
        # Note: 'document_type' doit être dans les détails de la facture/commande
        # Pour l'exemple, on le met en dur.
        invoice_data['details']['document_type'] = 'sale'
        client_info = {
            "name": invoice_data['details'].get('client_name'),
            "address": invoice_data['details'].get('client_address'),
            "ncc": invoice_data['details'].get('client_ncc'),
            "phone": invoice_data['details'].get('client_phone'),
            "email": invoice_data['details'].get('client_email')
        }


        self.is_task_running = True
        self.thread = QThread()
        self.worker = Worker(
            fne_client.certify_document,
            invoice_full_data=invoice_data,
            company_info=company_info,
            client_info=client_info,
            user_info=self.user_data,
            api_key=company_info['fne_api_key']
        )
        self.worker.moveToThread(self.thread)

        # Connecter les signaux
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(lambda result: self.on_certification_finished(invoice_id, result))
        self.worker.error.connect(lambda error_msg: self.on_certification_error(invoice_id, error_msg))

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()
        self.ui.certify_button.setEnabled(False)
        self.main_window.statusBar().showMessage(f"Certification de la facture {invoice_data['details']['code_facture']} en cours...")

    def on_certification_finished(self, invoice_id, result_data):
        self.is_task_running = False
        self.main_window.statusBar().showMessage("Prêt", 3000)

        nim = result_data.get('nim')
        qr_code = result_data.get('qr_code')
        fne_invoice_id = result_data.get('fne_invoice_id')
        items_id_map = result_data.get('items_id_map', [])

        QMessageBox.information(self, "Succès", f"Facture certifiée avec succès.\nNIM: {nim}")

        # Sauvegarder tous les résultats de la certification de manière atomique
        success, error_msg = self.model.save_certification_results(
            facture_id=invoice_id,
            nim=nim,
            qr_code=qr_code,
            fne_invoice_id=fne_invoice_id,
            items_id_map=items_id_map
        )

        if not success:
            QMessageBox.critical(self, "Erreur de Sauvegarde",
                                 f"La certification a réussi mais les résultats n'ont pas pu être sauvegardés en base de données : {error_msg}")

        self.load_invoices()
        self.ui.certify_button.setEnabled(True)

    def on_certification_error(self, invoice_id, error_message):
        self.is_task_running = False
        self.main_window.statusBar().showMessage("Erreur de certification", 5000)
        QMessageBox.critical(self, "Erreur de Certification FNE", error_message)

        # Mettre à jour la base de données avec le statut d'échec
        self.model.save_certification_error(
            facture_id=invoice_id,
            error_message=error_message
        )
        self.load_invoices()
        self.ui.certify_button.setEnabled(True)

    def print_invoice(self):
        if self.is_task_running:
            QMessageBox.warning(self, "Tâche en cours", "Une autre tâche est déjà en cours. Veuillez patienter.")
            return

        invoice_id = self.get_selected_invoice_id()
        if not invoice_id: return

        invoice_data = self.model.get_by_id_for_printing(invoice_id)
        if not invoice_data:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les données de la facture {invoice_id} pour l'impression.")
            return

        self.is_task_running = True

        company_data = self.company_model.get_first()
        if not company_data:
            QMessageBox.critical(self, "Erreur", "Les informations de l'entreprise n'ont pas pu être chargées.")
            self.is_task_running = False
            return

        client_data = {
            "name": invoice_data['details']['client_name'],
            "address": invoice_data['details']['client_address'],
            "email": invoice_data['details']['client_email'],
            "phone": invoice_data['details']['client_phone'],
            "contact": f"{invoice_data['details']['client_email']} • {invoice_data['details']['client_phone']}"
        }

        # Déterminer le template à utiliser (Standard ou FNE)
        is_fne = invoice_data['details'].get('statut_fne') == 'success'
        template_name = "invoice_fne.html" if is_fne else "invoice.html"

        generator = PDFGenerator(template_file=template_name)

        context = {
            "company": company_data,
            "client": client_data,
            "invoice": invoice_data['details'],
            "details": invoice_data['items']
        }
        html_content = generator.render_html(**context)

        output_file = f"facture-{invoice_data['details']['code_facture']}.pdf"

        self.thread = QThread()
        # Note: le générateur et sa méthode generate_pdf sont passés au worker
        self.worker = Worker(generator.generate_pdf, html_content, output_file)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(lambda: self.on_printing_finished(output_file))
        self.worker.error.connect(self.on_printing_error)

        # Nettoyage
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

        self.ui.print_button.setEnabled(False)
        self.main_window.statusBar().showMessage(f"Génération du PDF pour la facture {invoice_data['details']['code_facture']}...")

    def on_printing_finished(self, output_file):
        self.is_task_running = False
        # Le nom du fichier est maintenant directement passé au slot.
        self.ui.print_button.setEnabled(True)
        self.ui.bl_button.setEnabled(True) # Réactiver aussi le bouton BL
        self.main_window.statusBar().showMessage("Prêt", 3000)

        reply = QMessageBox.information(
            self,
            "Impression terminée",
            f"La facture a été exportée avec succès:\n{output_file}\n\nVoulez-vous l'ouvrir maintenant ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                webbrowser.open(os.path.abspath(output_file))
            except Exception as e:
                QMessageBox.critical(self, "Erreur d'ouverture", f"Impossible d'ouvrir le fichier PDF:\n{e}")

    def on_printing_error(self, error_message):
        self.is_task_running = False
        QMessageBox.critical(self, "Erreur d'impression", f"Une erreur est survenue:\n{error_message}")
        self.ui.print_button.setEnabled(True)
        self.main_window.statusBar().showMessage("Erreur lors de la génération du PDF", 5000)

    def create_credit_note(self):
        invoice_id = self.get_selected_invoice_id()
        if not invoice_id: return

        # On pourrait ajouter une vérification pour ne pas créer plusieurs avoirs pour la même facture

        dialog = CreditNoteEditorDialog(self.db_manager, facture_id=invoice_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            avoir_data = dialog.get_data()
            if avoir_data:
                avoir_id, error = self.avoir_model.create(
                    original_facture_id=avoir_data['original_facture_id'],
                    code_facture_origine=avoir_data['code_facture_origine'],
                    avoir_items=avoir_data['avoir_items'],
                    totals=avoir_data['totals']
                )
                if error:
                    QMessageBox.critical(self, "Erreur de Création", f"Impossible de créer la facture d'avoir : {error}")
                else:
                    QMessageBox.information(self, "Succès", f"Facture d'avoir ID {avoir_id} créée avec succès.")
                    # Ici, on pourrait rafraîchir une liste d'avoirs si elle existait

    # --- Méthodes pour le menu BL ---

    def view_bl(self):
        invoice_id = self.get_selected_invoice_id()
        if not invoice_id: return

        dialog = BLViewerDialog(self.db_manager, facture_id=invoice_id, parent=self)
        dialog.exec()

    def certify_bl(self):
        if self.is_task_running:
            QMessageBox.warning(self, "Tâche en cours", "Une autre tâche est déjà en cours. Veuillez patienter.")
            return

        invoice_id = self.get_selected_invoice_id()
        if not invoice_id: return

        bl_data = self.bl_model.get_by_facture_id(invoice_id)
        if not bl_data:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les données du BL pour la facture {invoice_id}.")
            return

        if bl_data['details']['statut_fne'] == 'success':
            QMessageBox.information(self, "Déjà certifié", "Ce BL a déjà été certifié avec succès.")
            return

        company_info = self.company_model.get_first()
        if not company_info or not company_info.get('fne_api_key'):
            QMessageBox.critical(self, "Erreur de configuration", "La clé d'API FNE pour l'entreprise n'est pas configurée.")
            return

        self.is_task_running = True
        # Le document_type pour un BL est 'purchase'
        bl_data['details']['document_type'] = 'purchase'

        # Le client_info pour un 'purchase' n'est pas utilisé par le fne_client,
        # qui prendra les infos de company_info. On peut passer un dict vide.
        client_info = {}

        self.thread = QThread()
        self.worker = Worker(
            fne_client.certify_document,
            invoice_full_data=bl_data, # On passe les données du BL
            company_info=company_info,
            client_info=client_info, # Non utilisé pour 'purchase'
            user_info=self.user_data,
            api_key=company_info['fne_api_key']
        )
        self.worker.moveToThread(self.thread)

        bl_id = bl_data['details']['bl_id']
        self.worker.finished.connect(lambda result: self.on_bl_certification_finished(bl_id, result))
        self.worker.error.connect(lambda error_msg: self.on_bl_certification_error(bl_id, error_msg))
        self.thread.started.connect(self.worker.run)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()
        self.ui.bl_button.setEnabled(False)
        self.main_window.statusBar().showMessage(f"Certification du BL {bl_data['details']['code_bl']} en cours...")

    def on_bl_certification_finished(self, bl_id, result_data):
        self.is_task_running = False
        self.main_window.statusBar().showMessage("Prêt", 3000)

        nim = result_data.get('nim')
        qr_code = result_data.get('qr_code')

        QMessageBox.information(self, "Succès", f"BL certifié avec succès.\nNIM: {nim}")

        self.bl_model.update_fne_status(
            bl_id=bl_id,
            statut_fne='success',
            nim=nim,
            qr_code=qr_code
        )
        self.load_invoices() # Pour rafraîchir le statut dans la vue principale
        self.ui.bl_button.setEnabled(True)

    def on_bl_certification_error(self, bl_id, error_message):
        self.is_task_running = False
        self.main_window.statusBar().showMessage("Erreur de certification", 5000)
        QMessageBox.critical(self, "Erreur de Certification FNE", error_message)

        self.bl_model.update_fne_status(
            bl_id=bl_id,
            statut_fne='failed',
            error_message=error_message
        )
        self.load_invoices()
        self.ui.bl_button.setEnabled(True)

    def print_bl(self):
        if self.is_task_running:
            QMessageBox.warning(self, "Tâche en cours", "Une autre tâche est déjà en cours. Veuillez patienter.")
            return

        invoice_id = self.get_selected_invoice_id()
        if not invoice_id: return

        invoice_data = self.model.get_by_id_for_printing(invoice_id)
        if not invoice_data:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les données de la facture {invoice_id} pour l'impression du BL.")
            return

        self.is_task_running = True

        company_data = self.company_model.get_first()
        if not company_data:
            QMessageBox.critical(self, "Erreur", "Les informations de l'entreprise n'ont pas pu être chargées.")
            self.is_task_running = False
            return

        client_data = {
            "name": invoice_data['details']['client_name'],
            "address": invoice_data['details']['client_address'],
            "contact": f"{invoice_data['details']['client_email']} • {invoice_data['details']['client_phone']}"
        }

        # Déterminer le template BL à utiliser (Standard ou FNE)
        # Note: On regarde le statut FNE du BL, qui est aussi stocké dans invoice_data['details']['statut_fne'] ?
        # Attention: 'statut_fne' dans invoice_data['details'] (qui vient de FactureModel) est celui de la facture.
        # Pour le BL, il faudrait vérifier le statut du BL.
        # Cependant, le code actuel récupère tout via `get_by_id_for_printing`.
        # FactureModel.get_by_id_for_printing ne joint pas 'statut_fne' du BL.
        # Il faut donc vérifier comment savoir si le BL est certifié.
        # Dans 'certify_bl', on update le BL.
        # Il faudrait idéalement que 'get_by_id_for_printing' retourne aussi le statut FNE du BL s'il est différent.
        # Mais pour l'instant, supposons que si la facture a un BL certifié, on le sait.
        #
        # CORRECTION: On doit récupérer le statut du BL.
        # On va faire un appel rapide pour vérifier le statut du BL si ce n'est pas dans 'invoice_data'.
        # invoice_data['details'] contient les champs de la facture + des champs joints du BL (code_bl, bl_date_creation).
        # Vérifions si 'statut_fne' du BL est dispo. Sinon on le récupère.

        # Récupération explicite des infos du BL pour être sûr (notamment le statut FNE)
        bl_info = self.bl_model.get_by_facture_id(invoice_id)
        is_bl_fne = False
        if bl_info and bl_info['details'].get('statut_fne') == 'success':
            is_bl_fne = True
            # On s'assure que les infos FNE du BL sont dans 'invoice' pour le template
            invoice_data['details']['fne_nim'] = bl_info['details'].get('fne_nim')
            invoice_data['details']['fne_qr_code'] = bl_info['details'].get('fne_qr_code')

        template_name = "bl_fne.html" if is_bl_fne else "bl.html"

        # Utilisation du template déterminé
        generator = PDFGenerator(template_file=template_name)

        context = {
            "company": company_data,
            "client": client_data,
            "invoice": invoice_data['details'], # Le template bl.html utilise aussi la variable 'invoice'
            "details": invoice_data['items']
        }
        html_content = generator.render_html(**context)

        output_file = f"BL-{invoice_data['details']['code_facture']}.pdf"

        self.thread = QThread()
        self.worker = Worker(generator.generate_pdf, html_content, output_file)
        self.worker.moveToThread(self.thread)

        # On peut réutiliser les mêmes slots que pour l'impression de facture
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(lambda: self.on_printing_finished(output_file)) # On passe le nom du fichier
        self.worker.error.connect(self.on_printing_error)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

        self.ui.bl_button.setEnabled(False) # On désactive le bouton BL pendant l'opération
        self.main_window.statusBar().showMessage(f"Génération du PDF pour le BL de la facture {invoice_data['details']['code_facture']}...")

    def handle_facture_double_click(self, index):
        facture_id = self.get_selected_invoice_id()
        if facture_id is None:
            return

        commande_id = self.model.get_commande_id_from_facture(facture_id)
        if commande_id is None:
            QMessageBox.warning(self, "Erreur", f"Impossible de trouver la commande associée à la facture {facture_id}.")
            return

        # Ouvre le dialogue de la commande en mode lecture seule
        dialog = CommandeEditorDialog(self.db_manager, commande_id=commande_id, read_only=True)
        dialog.exec()
