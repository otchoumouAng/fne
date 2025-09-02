from PyQt6.QtWidgets import QDialog, QCompleter, QLineEdit, QMessageBox
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, QDate

from page._invoice_editor import Ui_InvoiceEditorDialog
from models.client import ClientModel
from models.product import ProductModel

class InvoiceEditorDialog(QDialog):
    def __init__(self, db_manager, invoice_id=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.invoice_id = invoice_id
        self.client_model = ClientModel(self.db_manager)
        self.product_model = ProductModel(self.db_manager)

        self.ui = Ui_InvoiceEditorDialog()
        self.ui.setupUi(self)

        self.setup_models()
        self.setup_connections()
        self.load_data()

    def setup_models(self):
        # Items table model
        self.items_model = QStandardItemModel()
        self.items_model.setHorizontalHeaderLabels(
            ['Product ID', 'Produit', 'Description', 'Quantité', 'Prix U.', 'Taux TVA', 'Total HT']
        )
        self.ui.items_table_view.setModel(self.items_model)
        self.ui.items_table_view.setColumnHidden(0, True)

    def setup_connections(self):
        self.ui.button_box.accepted.connect(self.accept)
        self.ui.button_box.rejected.connect(self.reject)
        self.ui.add_item_button.clicked.connect(self.add_item)
        self.ui.remove_item_button.clicked.connect(self.remove_item)
        self.items_model.dataChanged.connect(self.update_totals)

    def load_data(self):
        # Load clients into combobox
        clients = self.client_model.get_all()
        for client in clients:
            self.ui.client_combobox.addItem(client['name'], userData=client['id'])

        # Set dates
        self.ui.issue_date_edit.setDate(QDate.currentDate())
        self.ui.due_date_edit.setDate(QDate.currentDate().addDays(30))

        if self.invoice_id:
            # TODO: Load existing invoice data for editing
            pass

    def add_item(self):
        # In a real app, this would open a product search dialog
        # For simplicity, we add a blank row to be edited
        row = [
            QStandardItem(""), # Product ID
            QStandardItem(""), # Product Name
            QStandardItem(""), # Description
            QStandardItem("1"), # Quantity
            QStandardItem("0.00"), # Unit Price
            QStandardItem("18.00"), # Tax Rate
            QStandardItem("0.00") # Total HT
        ]
        self.items_model.appendRow(row)

    def remove_item(self):
        selected_rows = self.ui.items_table_view.selectionModel().selectedRows()
        for index in sorted(selected_rows, reverse=True):
            self.items_model.removeRow(index.row())
        self.update_totals()

    def update_totals(self):
        total_ht = 0
        total_tax = 0
        for row in range(self.items_model.rowCount()):
            try:
                quantity = float(self.items_model.item(row, 3).text())
                price = float(self.items_model.item(row, 4).text())
                tax_rate = float(self.items_model.item(row, 5).text())

                row_total_ht = quantity * price
                row_total_tax = row_total_ht * (tax_rate / 100)

                self.items_model.item(row, 6).setText(f"{row_total_ht:.2f}")
                total_ht += row_total_ht
                total_tax += row_total_tax
            except (ValueError, TypeError):
                continue # Ignore non-numeric values for now

        total_ttc = total_ht + total_tax
        self.ui.total_ht_value.setText(f"{total_ht:.2f}")
        self.ui.total_tax_value.setText(f"{total_tax:.2f}")
        self.ui.total_ttc_value.setText(f"{total_ttc:.2f}")

    def get_data(self):
        client_id = self.ui.client_combobox.currentData()
        if not client_id:
            QMessageBox.warning(self, "Client manquant", "Veuillez sélectionner un client.")
            return None

        invoice_details = {
            'client_id': client_id,
            'issue_date': self.ui.issue_date_edit.date().toString(Qt.DateFormat.ISODate),
            'due_date': self.ui.due_date_edit.date().toString(Qt.DateFormat.ISODate),
            'total_amount': float(self.ui.total_ttc_value.text())
        }

        invoice_items = []
        for row in range(self.items_model.rowCount()):
            # A real implementation needs to get product_id correctly
            # This is a simplification
            if not self.items_model.item(row, 0) or not self.items_model.item(row, 0).text():
                 QMessageBox.warning(self, "Produit manquant", f"Veuillez sélectionner un produit pour la ligne {row + 1}.")
                 return None

            item = {
                'product_id': int(self.items_model.item(row, 0).text()),
                'description': self.items_model.item(row, 2).text(),
                'quantity': float(self.items_model.item(row, 3).text()),
                'unit_price': float(self.items_model.item(row, 4).text()),
                'tax_rate': float(self.items_model.item(row, 5).text())
            }
            invoice_items.append(item)

        if not invoice_items:
            QMessageBox.warning(self, "Lignes manquantes", "Une facture doit contenir au moins une ligne.")
            return None

        return {'details': invoice_details, 'items': invoice_items}
