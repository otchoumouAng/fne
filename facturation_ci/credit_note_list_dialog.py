import os
import webbrowser
from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, QThread

from page._credit_note_list_dialog import Ui_CreditNoteListDialog
from models.avoir import FactureAvoirModel
from models.company import CompanyInfoModel
from models.client import ClientModel # On en aura besoin pour les détails client
from avoir_viewer_dialog import AvoirViewerDialog
from core.pdf_generator import PDFGenerator
from core.worker import Worker

class CreditNoteListDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.avoir_model = FactureAvoirModel(self.db_manager)
        self.company_model = CompanyInfoModel(self.db_manager)
        self.client_model = ClientModel(self.db_manager)
        self.thread = None
        self.worker = None

        self.ui = Ui_CreditNoteListDialog()
        self.ui.setupUi(self)

        self.setup_table()
        self.setup_connections()
        self.load_data()

    def setup_table(self):
        self.table_model = QStandardItemModel()
        self.table_model.setHorizontalHeaderLabels([
            'ID', 'Code Avoir', 'Date Création', 'Facture d\'Origine', 'Total TTC', 'Statut FNE'
        ])
        self.ui.avoirs_table_view.setModel(self.table_model)
        self.ui.avoirs_table_view.setColumnHidden(0, True)

        self.ui.certify_button.setEnabled(False)
        self.ui.print_button.setEnabled(False)

    def setup_connections(self):
        self.ui.button_box.rejected.connect(self.reject)
        self.ui.avoirs_table_view.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.ui.avoirs_table_view.doubleClicked.connect(self.open_avoir_details)
        self.ui.print_button.clicked.connect(self.print_avoir)
        # self.ui.certify_button.clicked.connect(self.certify_avoir)

    def load_data(self):
        avoirs = self.avoir_model.get_all()
        self.table_model.removeRows(0, self.table_model.rowCount())
        for avoir in avoirs:
            row = [
                QStandardItem(str(avoir['id'])),
                QStandardItem(avoir['code_avoir']),
                QStandardItem(avoir['date_creation'].strftime('%Y-%m-%d')),
                QStandardItem(avoir['code_facture_origine']),
                QStandardItem(f"{avoir['total_ttc']:.2f}"),
                QStandardItem(avoir['statut_fne'])
            ]
            self.table_model.appendRow(row)
        self.ui.avoirs_table_view.resizeColumnsToContents()

    def on_selection_changed(self, selected, deselected):
        is_selection = self.ui.avoirs_table_view.selectionModel().hasSelection()
        self.ui.certify_button.setEnabled(is_selection)
        self.ui.print_button.setEnabled(is_selection)

    def get_selected_avoir_id(self):
        selected_indexes = self.ui.avoirs_table_view.selectionModel().selectedRows()
        if not selected_indexes:
            return None
        return int(self.table_model.item(selected_indexes[0].row(), 0).text())

    def open_avoir_details(self, index):
        avoir_id = self.get_selected_avoir_id()
        if avoir_id is None: return
        dialog = AvoirViewerDialog(self.db_manager, avoir_id=avoir_id, parent=self)
        dialog.exec()

    def print_avoir(self):
        avoir_id = self.get_selected_avoir_id()
        if not avoir_id: return

        avoir_data = self.avoir_model.get_by_id(avoir_id)
        if not avoir_data:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger l'avoir ID {avoir_id}.")
            return

        # Pour imprimer, on a besoin des infos de l'entreprise et du client.
        company_info = self.company_model.get_first()
        client_info = {
            "name": avoir_data.get('client_name', 'N/A'),
            "address": avoir_data.get('client_address', 'N/A'),
            "contact": avoir_data.get('client_contact', 'N/A')
        }

        generator = PDFGenerator(template_file="avoir.html")
        context = {
            "company": company_info,
            "client": client_info,
            "invoice": avoir_data,  # Le template s'attend à 'invoice'
            "details": avoir_data['lignes_avoir']
        }
        html_content = generator.render_html(**context)
        output_file = f"Avoir-{avoir_data['code_avoir']}.pdf"

        self.thread = QThread()
        self.worker = Worker(generator.generate_pdf, html_content, output_file)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(lambda: self.on_printing_finished(output_file))
        self.worker.error.connect(self.on_printing_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()
        self.ui.print_button.setEnabled(False)

    def on_printing_finished(self, output_file):
        self.ui.print_button.setEnabled(True)
        reply = QMessageBox.information(self, "Impression terminée",
            f"Le document a été exporté : {output_file}\n\nVoulez-vous l'ouvrir ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes)
        if reply == QMessageBox.StandardButton.Yes:
            webbrowser.open(os.path.abspath(output_file))

    def on_printing_error(self, error_message):
        self.ui.print_button.setEnabled(True)
        QMessageBox.critical(self, "Erreur d'impression", f"Une erreur est survenue:\n{error_message}")

    # def certify_avoir(self):
    #     pass
