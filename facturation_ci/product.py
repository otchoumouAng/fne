import sys
from PyQt6.QtWidgets import QWidget, QMessageBox, QDialog
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt

from page._product import Ui_ProductPage
from models.product import ProductModel
from crud_dialog import CrudDialog

class ProductModule(QWidget):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.model = ProductModel(self.db_manager)

        self.ui = Ui_ProductPage()
        self.ui.setupUi(self)

        self.fields_config = [
            {'name': 'name', 'label': 'Nom', 'type': 'QLineEdit', 'required': True},
            {'name': 'description', 'label': 'Description', 'type': 'QTextEdit'},
            {'name': 'unit_price', 'label': 'Prix Unitaire', 'type': 'QLineEdit'},
            {'name': 'tax_rate', 'label': 'Taux de Taxe (%)', 'type': 'QLineEdit'},
        ]

        self.connect_signals()
        self.load_products()

    def connect_signals(self):
        self.ui.new_button.clicked.connect(self.open_new_product_dialog)
        self.ui.edit_button.clicked.connect(self.open_edit_product_dialog)
        self.ui.delete_button.clicked.connect(self.delete_product)

    def load_products(self):
        products = self.model.get_all()
        self.set_products_in_view(products)

    def set_products_in_view(self, products):
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(['ID', 'Nom', 'Description', 'Prix Unitaire', 'Taux de Taxe'])
        self.ui.table_view.setModel(model)

        for product in products:
            row = [
                QStandardItem(str(product['id'])),
                QStandardItem(product['name']),
                QStandardItem(product['description']),
                QStandardItem(str(product['unit_price'])),
                QStandardItem(str(product['tax_rate']))
            ]
            for item in row:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            model.appendRow(row)

        self.ui.table_view.setColumnHidden(0, True)


    def get_selected_product_id(self):
        selected_indexes = self.ui.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            return None
        model = self.ui.table_view.model()
        id_index = model.index(selected_indexes[0].row(), 0)
        product_id = model.data(id_index)
        return int(product_id) if product_id else None

    def open_new_product_dialog(self):
        dialog = CrudDialog(
            mode='new',
            fields_config=self.fields_config,
            title="Nouveau Produit",
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            if not new_data.get('name'):
                QMessageBox.warning(self, "Champ Requis", "Le nom du produit ne peut pas être vide.")
                return

            try:
                # Validate numeric fields
                float(new_data.get('unit_price', 0))
                float(new_data.get('tax_rate', 0))
            except ValueError:
                QMessageBox.warning(self, "Format Invalide", "Le prix unitaire et le taux de taxe doivent être des nombres.")
                return

            product_id, error = self.model.create(new_data)
            if error:
                QMessageBox.critical(self, "Erreur", f"Impossible de créer le produit: {error}")
            else:
                QMessageBox.information(self, "Succès", "Produit créé avec succès.")
                self.load_products()


    def open_edit_product_dialog(self):
        product_id = self.get_selected_product_id()
        if product_id is None:
            QMessageBox.warning(self, "Aucune Sélection", "Veuillez sélectionner un produit à modifier.")
            return

        product_data = self.model.get_by_id(product_id)
        if not product_data:
            QMessageBox.critical(self, "Erreur", "Produit non trouvé.")
            return

        dialog = CrudDialog(
            mode='edit',
            fields_config=self.fields_config,
            title="Modifier le Produit",
            data=product_data,
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_data = dialog.get_data()
            if not updated_data.get('name'):
                QMessageBox.warning(self, "Champ Requis", "Le nom du produit ne peut pas être vide.")
                return

            try:
                # Validate numeric fields
                float(updated_data.get('unit_price', 0))
                float(updated_data.get('tax_rate', 0))
            except ValueError:
                QMessageBox.warning(self, "Format Invalide", "Le prix unitaire et le taux de taxe doivent être des nombres.")
                return

            success, error = self.model.update(product_id, updated_data)
            if error:
                QMessageBox.critical(self, "Erreur", f"Impossible de mettre à jour le produit: {error}")
            else:
                QMessageBox.information(self, "Succès", "Produit mis à jour avec succès.")
                self.load_products()


    def delete_product(self):
        product_id = self.get_selected_product_id()
        if product_id is None:
            QMessageBox.warning(self, "Aucune Sélection", "Veuillez sélectionner un produit à supprimer.")
            return

        product_data = self.model.get_by_id(product_id)
        if not product_data:
             QMessageBox.critical(self, "Erreur", "Produit non trouvé.")
             return

        reply = QMessageBox.question(
            self,
            "Confirmation de Suppression",
            f"Êtes-vous sûr de vouloir supprimer le produit '{product_data['name']}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, error = self.model.delete(product_id)
            if error:
                QMessageBox.critical(self, "Erreur", f"Impossible de supprimer le produit: {error}")
            else:
                QMessageBox.information(self, "Succès", "Produit supprimé avec succès.")
                self.load_products()
