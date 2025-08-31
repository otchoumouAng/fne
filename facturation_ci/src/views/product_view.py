from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableView, QAbstractItemView, QHeaderView
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem

class ProductView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        # Layout principal
        main_layout = QVBoxLayout(self)

        # Layout pour les boutons d'action
        button_layout = QHBoxLayout()
        self.new_button = QPushButton("Nouveau Produit/Service")
        self.edit_button = QPushButton("Modifier Produit/Service")
        self.delete_button = QPushButton("Supprimer Produit/Service")
        button_layout.addWidget(self.new_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # Tableau pour afficher les produits
        self.table_view = QTableView()
        self.table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_view.verticalHeader().setVisible(False)

        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setStretchLastSection(True)

        main_layout.addWidget(self.table_view)

        self.model = QStandardItemModel()
        self.table_view.setModel(self.model)

    def set_products(self, products):
        """Remplit le tableau avec la liste des produits."""
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['ID', 'Nom', 'Description', 'Prix Unitaire (€)', 'TVA (%)'])

        for product in products:
            row = [
                QStandardItem(str(product['id'])),
                QStandardItem(product['name']),
                QStandardItem(product.get('description', '')),
                QStandardItem(f"{product['unit_price']:.2f}"),
                QStandardItem(f"{product['tax_rate']:.2f}")
            ]
            self.model.appendRow(row)

        self.table_view.setColumnHidden(0, True)

    def get_selected_product_id(self):
        """Retourne l'ID du produit sélectionné dans le tableau."""
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            return None

        id_index = selected_indexes[0].sibling(selected_indexes[0].row(), 0)
        product_id = self.model.data(id_index)
        return int(product_id) if product_id else None
