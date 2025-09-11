from PyQt6.QtWidgets import QDialog, QDialogButtonBox
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt

from page._new_invoice_dialog import Ui_NewInvoiceDialog
from models.commande import CommandeModel
from models.client import ClientModel

class NewInvoiceDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.commande_model = CommandeModel(self.db_manager)
        self.client_model = ClientModel(self.db_manager)
        
        self.ui = Ui_NewInvoiceDialog()
        self.ui.setupUi(self)

        self.master_commandes = []
        self.selected_commande_id = None

        self.setup_ui_elements()
        self.load_and_populate_initial_data()
        self.connect_signals()

    def setup_ui_elements(self):
        # Configure la table
        self.table_model = QStandardItemModel()
        self.table_model.setHorizontalHeaderLabels(['ID', 'Code Commande', 'Client', 'Date', 'Total TTC'])
        self.ui.commandes_table_view.setModel(self.table_model)
        self.ui.commandes_table_view.setColumnHidden(0, True)
        
        # Ajoute et configure le bouton Générer
        self.generate_button = self.ui.button_box.addButton("Générer la facture", QDialogButtonBox.ButtonRole.AcceptRole)
        self.generate_button.setEnabled(False)

    def load_and_populate_initial_data(self):
        # Charge la liste principale une seule fois depuis la base de données
        self.master_commandes = self.commande_model.get_all_unvoiced()
        
        # Remplit le filtre des clients, qui ne change pas
        self.ui.client_filter_combo.blockSignals(True)
        self.ui.client_filter_combo.addItem("Tous les clients", userData=None)
        clients = self.client_model.get_all()
        for client in clients:
            self.ui.client_filter_combo.addItem(client['name'], userData=client['id'])
        self.ui.client_filter_combo.blockSignals(False)
        
        # Déclenche la première mise à jour des filtres dépendants et de la table
        self.update_filters_and_table()

    def connect_signals(self):
        # Chaque filtre déclenche la mise à jour
        self.ui.client_filter_combo.currentIndexChanged.connect(self.update_filters_and_table)
        self.ui.date_filter_combo.currentIndexChanged.connect(self.update_filters_and_table)
        self.ui.commande_code_filter_combo.currentIndexChanged.connect(self.update_filters_and_table)
        
        # La sélection dans la table active le bouton Générer
        self.ui.commandes_table_view.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.generate_button.clicked.connect(self.accept)

    def update_filters_and_table(self):
        # Bloque les signaux pour éviter les mises à jour en cascade infinies
        self.ui.date_filter_combo.blockSignals(True)
        self.ui.commande_code_filter_combo.blockSignals(True)

        # 1. Détermine la liste de commandes à considérer en fonction du client
        client_id = self.ui.client_filter_combo.currentData()
        potential_commandes = self.master_commandes
        if client_id:
            potential_commandes = [cmd for cmd in self.master_commandes if cmd['client_id'] == client_id]

        # 2. Met à jour les options du filtre de date
        self.update_date_filter_options(potential_commandes)
        
        # 3. Affine la liste en fonction de la date sélectionnée
        date_selection = self.ui.date_filter_combo.currentData()
        if date_selection:
            potential_commandes = [cmd for cmd in potential_commandes if cmd['date_commande'] == date_selection]

        # 4. Met à jour les options du filtre de code
        self.update_code_filter_options(potential_commandes)

        # 5. Affine la liste en fonction du code sélectionné
        code_selection = self.ui.commande_code_filter_combo.currentData()
        if code_selection:
            potential_commandes = [cmd for cmd in potential_commandes if cmd['code_commande'] == code_selection]
        
        # 6. Met à jour la table avec le résultat final
        self.populate_table(potential_commandes)

        # Réactive les signaux
        self.ui.date_filter_combo.blockSignals(False)
        self.ui.commande_code_filter_combo.blockSignals(False)

    def update_date_filter_options(self, commandes):
        # Sauvegarde la sélection actuelle
        current_selection = self.ui.date_filter_combo.currentData()
        
        self.ui.date_filter_combo.clear()
        self.ui.date_filter_combo.addItem("Toutes les dates", userData=None)
        
        unique_dates = sorted(list(set(cmd['date_commande'] for cmd in commandes)), reverse=True)
        for date in unique_dates:
            self.ui.date_filter_combo.addItem(date.strftime('%Y-%m-%d'), userData=date)
        
        # Essaie de restaurer la sélection
        if current_selection in unique_dates:
            self.ui.date_filter_combo.setCurrentText(current_selection.strftime('%Y-%m-%d'))

    def update_code_filter_options(self, commandes):
        # Sauvegarde la sélection actuelle
        current_selection = self.ui.commande_code_filter_combo.currentData()

        self.ui.commande_code_filter_combo.clear()
        self.ui.commande_code_filter_combo.addItem("Tous les codes", userData=None)
        
        unique_codes = sorted(list(set(cmd['code_commande'] for cmd in commandes)))
        for code in unique_codes:
            self.ui.commande_code_filter_combo.addItem(code, userData=code)
            
        # Essaie de restaurer la sélection
        if current_selection in unique_codes:
            self.ui.commande_code_filter_combo.setCurrentText(current_selection)

    def populate_table(self, commandes):
        self.table_model.removeRows(0, self.table_model.rowCount())
        for cmd in commandes:
            row = [
                QStandardItem(str(cmd['id'])),
                QStandardItem(cmd['code_commande']),
                QStandardItem(cmd['client_name']),
                QStandardItem(cmd['date_commande'].strftime('%Y-%m-%d')),
                QStandardItem(f"{cmd['total_ttc']:.2f}")
            ]
            self.table_model.appendRow(row)
        self.ui.commandes_table_view.resizeColumnsToContents()

    def on_selection_changed(self, selected, deselected):
        is_selection = self.ui.commandes_table_view.selectionModel().hasSelection()
        self.generate_button.setEnabled(is_selection)
        if is_selection:
            selected_row = self.ui.commandes_table_view.selectionModel().selectedRows()[0]
            self.selected_commande_id = self.table_model.item(selected_row.row(), 0).text()
        else:
            self.selected_commande_id = None

    def get_selected_commande_id(self):
        return int(self.selected_commande_id) if self.selected_commande_id else None