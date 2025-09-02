import sys
from PyQt6.QtWidgets import QWidget, QMessageBox, QDialog
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt

from page._invoice import Ui_InvoicePage
from models.invoice import InvoiceModel
from invoice_editor_dialog import InvoiceEditorDialog

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
        self.ui.table_view.doubleClicked.connect(self.handle_invoice_double_click)

    def load_invoices(self):
        invoices = self.model.get_all_with_client_info()
        self.set_invoices_in_view(invoices)

    def set_invoices_in_view(self, invoices):
        self.ui.table_view.model().clear() if self.ui.table_view.model() else None
        model = QStandardItemModel()
        header = ['ID', 'Client', 'Date Émission', 'Date Échéance', 'Total', 'Statut', 'Statut FNE']
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
                QStandardItem(inv.get('fne_status', 'N/A'))
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

    def handle_invoice_double_click(self, index):
        invoice_id = self.get_selected_invoice_id()
        if invoice_id is None:
            return

        dialog = InvoiceEditorDialog(self.db_manager, invoice_id=invoice_id, read_only=True)
        dialog.exec()

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

        invoice_data = self.model.get_by_id(invoice_id)
        if not invoice_data or 'details' not in invoice_data:
             QMessageBox.critical(self, "Erreur", "Impossible de charger les données de la facture.")
             return

        if invoice_data['details']['status'] != 'draft':
            QMessageBox.warning(self, "Modification impossible", "Seules les factures en mode 'brouillon' peuvent être modifiées.")
            return

        dialog = InvoiceEditorDialog(self.db_manager, invoice_id=invoice_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_invoice_data = dialog.get_data()
            if new_invoice_data:
                success, error = self.model.update(invoice_id, new_invoice_data)
                if error:
                     QMessageBox.critical(self, "Erreur de mise à jour", f"Impossible de mettre à jour la facture: {error}")
                else:
                    QMessageBox.information(self, "Succès", "Facture mise à jour avec succès.")
                    self.load_invoices()


    def delete_invoice(self):
        invoice_id = self.get_selected_invoice_id()
        if invoice_id is None:
            QMessageBox.warning(self, "Aucune Sélection", "Veuillez sélectionner une facture à supprimer.")
            return

        QMessageBox.warning(self, "Action Interdite", "La suppression des factures n'est pas autorisée. Pensez à l'annuler ou à créer un avoir.")
