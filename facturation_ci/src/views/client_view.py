from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableView, QAbstractItemView, QHeaderView
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem

class ClientView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        # Layout principal
        main_layout = QVBoxLayout(self)

        # Layout pour les boutons d'action
        button_layout = QHBoxLayout()
        self.new_button = QPushButton("Nouveau Client")
        self.edit_button = QPushButton("Modifier Client")
        self.delete_button = QPushButton("Supprimer Client")
        button_layout.addWidget(self.new_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch() # Pousse les boutons à gauche
        main_layout.addLayout(button_layout)

        # Tableau pour afficher les clients
        self.table_view = QTableView()
        self.table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # Lecture seule
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) # Sélection par ligne
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection) # Sélection unique
        self.table_view.verticalHeader().setVisible(False) # Cacher les numéros de ligne verticaux

        # Ajuster la taille des colonnes
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setStretchLastSection(True)

        main_layout.addWidget(self.table_view)

        # Modèle de données pour le tableau
        self.model = QStandardItemModel()
        self.table_view.setModel(self.model)

    def set_clients(self, clients):
        """Remplit le tableau avec la liste des clients."""
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['ID', 'Nom', 'Adresse', 'Email', 'Téléphone'])

        for client in clients:
            row = [
                QStandardItem(str(client['id'])),
                QStandardItem(client['name']),
                QStandardItem(client['address']),
                QStandardItem(client['email']),
                QStandardItem(client['phone'])
            ]
            self.model.appendRow(row)

        # Cacher la colonne ID
        self.table_view.setColumnHidden(0, True)

    def get_selected_client_id(self):
        """Retourne l'ID du client sélectionné dans le tableau."""
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            return None

        # L'ID est dans la première colonne (index 0)
        id_index = selected_indexes[0].sibling(selected_indexes[0].row(), 0)
        client_id = self.model.data(id_index)
        return int(client_id) if client_id else None
