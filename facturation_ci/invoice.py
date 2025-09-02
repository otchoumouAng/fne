import sys
from PyQt6.QtWidgets import QWidget, QMessageBox, QDialog
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt

from page._invoice import Ui_InvoicePage
from models.invoice import InvoiceModel
from invoice_editor_dialog import InvoiceEditorDialog
# from core.invoice_generator import InvoiceGenerator # Will be used for printing

class InvoiceModule(QWidget):
    def __init__(self, db_manager, user_data, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.user_data = user_data
        self.model = InvoiceModel(self.db_manager)

        self.ui = Ui_InvoicePage()
        self.ui.setupUi(self)

        self.connect_signals()
        self.load_invoices()

    def connect_signals(self):
        self.ui.new_button.clicked.connect(self.open_new_invoice_dialog)
        self.ui.edit_button.clicked.connect(self.open_edit_invoice_dialog)
        self.ui.delete_button.clicked.connect(self.delete_invoice)
        # self.ui.print_button.clicked.connect(self.print_invoice)
        # self.ui.certify_button.clicked.connect(self.certify_invoice)

    def load_invoices(self):
        invoices = self.model.get_all_with_client_info()
        self.set_invoices_in_view(invoices)

    def set_invoices_in_view(self, invoices):
        model = QStandardItemModel()
        header = ['ID', 'Client', 'Date Émission', 'Date Échéance', 'Total', 'Statut', 'Statut FNE', 'NIM FNE']
        model.setHorizontalHeaderLabels(header)
        self.ui.table_view.setModel(model)

        for inv in invoices:
            row = [
                QStandardItem(str(inv['id'])),
                QStandardItem(inv['client_name']),
                QStandardItem(inv['issue_date'].strftime('%Y-%m-%d')),
                QStandardItem(inv['due_date'].strftime('%Y-%m-%d')),
                QStandardItem(f"{inv['total_amount']:.2f}"),
                QStandardItem(inv['status']),
                QStandardItem(inv.get('fne_status', 'N/A')),
                QStandardItem(inv.get('fne_nim', 'N/A'))
            ]
            for item in row:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            model.appendRow(row)

        self.ui.table_view.setColumnHidden(0, True)
        self.ui.table_view.resizeColumnsToContents()

    def get_selected_invoice_id(self):
        selected_indexes = self.ui.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            return None
        model = self.ui.table_view.model()
        id_index = model.index(selected_indexes[0].row(), 0)
        invoice_id = model.data(id_index)
        return int(invoice_id) if invoice_id else None

    def open_new_invoice_dialog(self):
        dialog = InvoiceEditorDialog(self.db_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            invoice_data = dialog.get_data()
            if invoice_data:
                invoice_data['details']['user_id'] = self.user_data['id']
                invoice_id, error = self.model.create(invoice_data)
                if error:
                    QMessageBox.critical(self, "Erreur", f"Impossible de créer la facture: {error}")
                else:
                    QMessageBox.information(self, "Succès", f"Facture ID {invoice_id} créée avec succès.")
                    self.load_invoices()

    def open_edit_invoice_dialog(self):
        invoice_id = self.get_selected_invoice_id()
        if invoice_id is None:
            QMessageBox.warning(self, "Aucune Sélection", "Veuillez sélectionner une facture à modifier.")
            return

        QMessageBox.information(self, "Non implémenté", "La modification des factures n'est pas encore implémentée.")

    def delete_invoice(self):
        invoice_id = self.get_selected_invoice_id()
        if invoice_id is None:
            QMessageBox.warning(self, "Aucune Sélection", "Veuillez sélectionner une facture à supprimer.")
            return

        QMessageBox.warning(self, "Action Interdite", "La suppression des factures n'est pas autorisée. Pensez à l'annuler.")

    # def print_invoice(self):
    #     invoice_id = self.get_selected_invoice_id()
    #     if not invoice_id:
    #         QMessageBox.warning(self, "Sélection requise", "Veuillez sélectionner une facture à imprimer.")
    #         return
    #
    #     # This is a simplified example. A real implementation needs more details.
    #     invoice_data = self.model.get_by_id(invoice_id)
    #     client_data = ClientModel(self.db_manager).get_by_id(invoice_data['details']['client_id'])
    #
    #     generator = InvoiceGenerator()
    #     html = generator.render_html(company={}, client=client_data, invoice=invoice_data['details'], details=invoice_data['items'])
    #     generator.generate_pdf(html, output_file=f"facture-{invoice_id}.pdf")
    #     QMessageBox.information(self, "Impression", f"La facture {invoice_id} a été exportée en PDF.")

    # def certify_invoice(self): ...
