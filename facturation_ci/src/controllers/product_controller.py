from PyQt6.QtWidgets import QMessageBox, QDialog
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtGui import QValidator
from models.product import ProductModel
from views.product_view import ProductView
from views.crud_dialog import CrudDialog

class ProductController:
    def __init__(self, db_manager, main_window):
        self.db_manager = db_manager
        self.main_window = main_window.ui

        self.model = ProductModel(self.db_manager)
        self.view = ProductView()

        # Remplacer le widget placeholder dans la MainWindow
        # L'index 3 correspond à "Produits"
        product_widget_index = 3
        old_widget = self.main_window.stacked_widget.widget(product_widget_index)
        self.main_window.stacked_widget.removeWidget(old_widget)
        self.main_window.stacked_widget.insertWidget(product_widget_index, self.view)

        self.fields_config = [
            {'name': 'name', 'label': 'Nom', 'type': 'QLineEdit', 'required': True},
            {'name': 'description', 'label': 'Description', 'type': 'QTextEdit'},
            {'name': 'unit_price', 'label': 'Prix Unitaire', 'type': 'QLineEdit', 'required': True, 'validator': QDoubleValidator(0, 999999.99, 2)},
            {'name': 'tax_rate', 'label': 'Taux de TVA (%)', 'type': 'QLineEdit', 'required': True, 'validator': QDoubleValidator(0, 100.00, 2)},
        ]

        self.connect_signals()
        self.load_products()

    def connect_signals(self):
        self.view.new_button.clicked.connect(self.open_new_product_dialog)
        self.view.edit_button.clicked.connect(self.open_edit_product_dialog)
        self.view.delete_button.clicked.connect(self.delete_product)

    def load_products(self):
        products = self.model.get_all()
        self.view.set_products(products)

    def _get_configured_dialog(self, mode, data=None):
        """Helper to create and configure the CrudDialog."""
        title = "Nouveau Produit/Service" if mode == 'new' else "Modifier le Produit/Service"
        dialog = CrudDialog(
            mode=mode,
            fields_config=self.fields_config,
            title=title,
            data=data,
            parent=self.main_window
        )
        # Add validators
        for field in self.fields_config:
            if 'validator' in field:
                dialog.widgets[field['name']].setValidator(field['validator'])
        return dialog

    def open_new_product_dialog(self):
        dialog = self._get_configured_dialog(mode='new')
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            _, error = self.model.create(new_data)
            if error:
                QMessageBox.critical(self.main_window, "Erreur", f"Impossible de créer le produit : {error}")
            else:
                QMessageBox.information(self.main_window, "Succès", "Produit créé avec succès.")
                self.load_products()

    def open_edit_product_dialog(self):
        product_id = self.view.get_selected_product_id()
        if product_id is None:
            QMessageBox.warning(self.main_window, "Aucune Sélection", "Veuillez sélectionner un produit à modifier.")
            return

        product_data = self.model.get_by_id(product_id)
        if not product_data:
            QMessageBox.critical(self.main_window, "Erreur", "Produit non trouvé.")
            return

        dialog = self._get_configured_dialog(mode='edit', data=product_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_data = dialog.get_data()
            success, error = self.model.update(product_id, updated_data)
            if not success:
                QMessageBox.critical(self.main_window, "Erreur", f"Impossible de mettre à jour le produit : {error}")
            else:
                QMessageBox.information(self.main_window, "Succès", "Produit mis à jour avec succès.")
                self.load_products()

    def delete_product(self):
        product_id = self.view.get_selected_product_id()
        if product_id is None:
            QMessageBox.warning(self.main_window, "Aucune Sélection", "Veuillez sélectionner un produit à supprimer.")
            return

        product_data = self.model.get_by_id(product_id)
        if not product_data:
             QMessageBox.critical(self.main_window, "Erreur", "Produit non trouvé.")
             return

        reply = QMessageBox.question(
            self.main_window,
            "Confirmation de Suppression",
            f"Êtes-vous sûr de vouloir supprimer le produit '{product_data['name']}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, error = self.model.delete(product_id)
            if not success:
                QMessageBox.critical(self.main_window, "Erreur", f"Impossible de supprimer le produit : {error}")
            else:
                QMessageBox.information(self.main_window, "Succès", "Produit supprimé avec succès.")
                self.load_products()
