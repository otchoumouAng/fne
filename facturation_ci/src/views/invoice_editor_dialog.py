from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QDateEdit, QTableView, QPushButton, QLabel,
    QMessageBox, QAbstractItemView, QHeaderView
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import QDate, Qt

class InvoiceEditorDialog(QDialog):
    def __init__(self, client_model, product_model, mode='new', invoice_data=None, parent=None):
        super().__init__(parent)

        self.client_model = client_model
        self.product_model = product_model
        self.mode = mode
        self.invoice_data = invoice_data

        self.setWindowTitle("Nouvelle Facture" if mode == 'new' else "Détails de la Facture")
        self.setMinimumSize(800, 600)

        self.line_items = [] # Liste de dictionnaires pour les lignes d'articles

        self.setup_ui()
        self.populate_combos()

        if self.mode != 'new' and self.invoice_data:
            self.load_invoice_data()

        if self.mode == 'read':
            self.set_read_only()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Section Client et Dates ---
        details_group = QGroupBox("Détails de la facture")
        details_layout = QFormLayout(details_group)
        self.client_combo = QComboBox()
        self.issue_date_edit = QDateEdit(QDate.currentDate())
        self.issue_date_edit.setCalendarPopup(True)
        self.due_date_edit = QDateEdit(QDate.currentDate().addDays(30))
        self.due_date_edit.setCalendarPopup(True)
        details_layout.addRow("Client:", self.client_combo)
        details_layout.addRow("Date d'émission:", self.issue_date_edit)
        details_layout.addRow("Date d'échéance:", self.due_date_edit)
        main_layout.addWidget(details_group)

        # --- Section Lignes d'articles ---
        items_group = QGroupBox("Articles")
        items_layout = QVBoxLayout(items_group)
        self.items_table = QTableView()
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.items_model = QStandardItemModel()
        self.items_model.setHorizontalHeaderLabels(['Produit/Service', 'Quantité', 'Prix Unitaire', 'Total HT'])
        self.items_table.setModel(self.items_model)
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        items_layout.addWidget(self.items_table)

        # Boutons pour gérer les lignes
        items_button_layout = QHBoxLayout()
        self.add_item_button = QPushButton("Ajouter un article")
        self.remove_item_button = QPushButton("Supprimer la ligne")
        self.add_item_button.clicked.connect(self.add_item)
        self.remove_item_button.clicked.connect(self.remove_item)
        items_button_layout.addWidget(self.add_item_button)
        items_button_layout.addWidget(self.remove_item_button)
        items_button_layout.addStretch()
        items_layout.addLayout(items_button_layout)
        main_layout.addWidget(items_group)

        # --- Section Totaux ---
        totals_layout = QFormLayout()
        self.subtotal_label = QLabel("0.00 €")
        self.vat_label = QLabel("0.00 €")
        self.total_label = QLabel("0.00 €")
        totals_layout.addRow("Total HT:", self.subtotal_label)
        totals_layout.addRow("Montant TVA:", self.vat_label)
        totals_layout.addRow("Total TTC:", self.total_label)
        main_layout.addLayout(totals_layout)

        # --- Boutons de la boîte de dialogue ---
        self.save_button = QPushButton("Enregistrer")
        self.cancel_button = QPushButton("Annuler")
        self.save_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        button_box_layout = QHBoxLayout()
        button_box_layout.addStretch()
        button_box_layout.addWidget(self.save_button)
        button_box_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_box_layout)

    def populate_combos(self):
        """Remplit les QComboBox avec les données de la BDD."""
        clients = self.client_model.get_all()
        for client in clients:
            self.client_combo.addItem(client['name'], userData=client['id'])

    def add_item(self):
        # Dans une application plus complexe, on ouvrirait un dialogue de sélection de produit.
        # Pour simplifier, on ajoute un produit par défaut ou une ligne vide à éditer.
        # Ici, on va juste ajouter une ligne vide conceptuellement.

        # NOTE: This is a simplified approach. A real app would have a product selection dialog.
        # For now, we'll assume a placeholder item is added.
        # This part requires more UI to be fully functional (e.g., a product selection dialog).
        # We will simulate adding an item for now.
        from PyQt6.QtWidgets import QInputDialog

        products = self.product_model.get_all()
        product_names = [p['name'] for p in products]
        item_name, ok = QInputDialog.getItem(self, "Ajouter un article", "Choisir un produit:", product_names, 0, False)
        if ok and item_name:
            product = next((p for p in products if p['name'] == item_name), None)
            if product:
                quantity, ok = QInputDialog.getDouble(self, "Quantité", "Entrez la quantité:", 1.0, 1, 10000, 2)
                if ok:
                    item_data = {
                        'product_id': product['id'],
                        'description': product['name'],
                        'quantity': quantity,
                        'unit_price': product['unit_price'],
                        'tax_rate': product['tax_rate']
                    }
                    self.line_items.append(item_data)
                    self.update_table_and_totals()

    def remove_item(self):
        selected_rows = self.items_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Aucune sélection", "Veuillez sélectionner une ligne à supprimer.")
            return

        row_to_remove = selected_rows[0].row()
        del self.line_items[row_to_remove]
        self.update_table_and_totals()

    def update_table_and_totals(self):
        """Met à jour le tableau des articles et les totaux."""
        self.items_model.setRowCount(0) # Vide le tableau
        subtotal = 0
        total_vat = 0

        for item in self.line_items:
            total_ht = item['quantity'] * item['unit_price']
            subtotal += total_ht
            total_vat += total_ht * (item['tax_rate'] / 100.0)

            row = [
                QStandardItem(item['description']),
                QStandardItem(str(item['quantity'])),
                QStandardItem(f"{item['unit_price']:.2f}"),
                QStandardItem(f"{total_ht:.2f}")
            ]
            self.items_model.appendRow(row)

        grand_total = subtotal + total_vat
        self.subtotal_label.setText(f"{subtotal:.2f} €")
        self.vat_label.setText(f"{total_vat:.2f} €")
        self.total_label.setText(f"{grand_total:.2f} €")

    def load_invoice_data(self):
        """Charge les données d'une facture existante dans le formulaire."""
        details = self.invoice_data['details']
        items = self.invoice_data['items']

        # Client
        client_id = details['client_id']
        client_index = self.client_combo.findData(client_id)
        if client_index != -1:
            self.client_combo.setCurrentIndex(client_index)

        # Dates
        self.issue_date_edit.setDate(QDate.fromString(str(details['issue_date']), "yyyy-MM-dd"))
        self.due_date_edit.setDate(QDate.fromString(str(details['due_date']), "yyyy-MM-dd"))

        # Lignes d'articles
        self.line_items = items
        self.update_table_and_totals()

    def set_read_only(self):
        """Passe tous les contrôles en mode lecture seule."""
        self.client_combo.setEnabled(False)
        self.issue_date_edit.setReadOnly(True)
        self.due_date_edit.setReadOnly(True)
        self.add_item_button.setEnabled(False)
        self.remove_item_button.setEnabled(False)
        self.save_button.hide()
        self.cancel_button.setText("Fermer")
        # Rendre le tableau non éditable (déjà le cas, mais pour être explicite)
        self.items_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def get_data(self):
        """Retourne les données de la facture sous forme de dictionnaire structuré."""
        if not self.line_items:
            return None # Ne peut pas créer une facture sans articles

        client_id = self.client_combo.currentData()
        if not client_id:
            return None

        # Recalculer les totaux une dernière fois pour s'assurer qu'ils sont corrects
        subtotal = sum(item['quantity'] * item['unit_price'] for item in self.line_items)
        total_vat = sum((item['quantity'] * item['unit_price']) * (item['tax_rate'] / 100.0) for item in self.line_items)
        grand_total = subtotal + total_vat

        return {
            "details": {
                "client_id": client_id,
                "issue_date": self.issue_date_edit.date().toString("yyyy-MM-dd"),
                "due_date": self.due_date_edit.date().toString("yyyy-MM-dd"),
                "total_amount": grand_total,
                # user_id sera ajouté par le contrôleur
            },
            "items": self.line_items
        }

    def accept(self):
        if self.client_combo.currentIndex() == -1:
            QMessageBox.warning(self, "Client manquant", "Veuillez sélectionner un client.")
            return
        if not self.line_items:
            QMessageBox.warning(self, "Articles manquants", "Veuillez ajouter au moins un article à la facture.")
            return
        super().accept()
