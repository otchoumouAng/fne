from PyQt6.QtWidgets import QMessageBox, QDialog
from models.client import ClientModel
from views.client_view import ClientView
from views.crud_dialog import CrudDialog

class ClientController:
    def __init__(self, db_manager, main_window):
        self.db_manager = db_manager
        self.main_window = main_window.ui

        self.model = ClientModel(self.db_manager)
        self.view = ClientView()

        # Remplacer le widget placeholder dans la MainWindow
        # L'index 2 correspond à "Clients" dans l'ordre d'ajout dans main_window.py
        client_widget_index = 2
        old_widget = self.main_window.stacked_widget.widget(client_widget_index)
        self.main_window.stacked_widget.removeWidget(old_widget)
        self.main_window.stacked_widget.insertWidget(client_widget_index, self.view)

        self.fields_config = [
            {'name': 'name', 'label': 'Nom', 'type': 'QLineEdit', 'required': True},
            {'name': 'address', 'label': 'Adresse', 'type': 'QTextEdit'},
            {'name': 'email', 'label': 'Email', 'type': 'QLineEdit'},
            {'name': 'phone', 'label': 'Téléphone', 'type': 'QLineEdit'},
        ]

        self.connect_signals()
        self.load_clients()

    def connect_signals(self):
        """Connecte les signaux de la vue aux slots du contrôleur."""
        self.view.new_button.clicked.connect(self.open_new_client_dialog)
        self.view.edit_button.clicked.connect(self.open_edit_client_dialog)
        self.view.delete_button.clicked.connect(self.delete_client)

    def load_clients(self):
        """Charge les clients depuis le modèle et les affiche dans la vue."""
        clients = self.model.get_all()
        self.view.set_clients(clients)

    def open_new_client_dialog(self):
        """Ouvre la boîte de dialogue pour créer un nouveau client."""
        dialog = CrudDialog(
            mode='new',
            fields_config=self.fields_config,
            title="Nouveau Client",
            parent=self.main_window
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            if self.model.create(new_data):
                QMessageBox.information(self.main_window, "Succès", "Client créé avec succès.")
                self.load_clients()
            else:
                QMessageBox.critical(self.main_window, "Erreur", "Impossible de créer le client.")

    def open_edit_client_dialog(self):
        """Ouvre la boîte de dialogue pour modifier un client existant."""
        client_id = self.view.get_selected_client_id()
        if client_id is None:
            QMessageBox.warning(self.main_window, "Aucune Sélection", "Veuillez sélectionner un client à modifier.")
            return

        client_data = self.model.get_by_id(client_id)
        if not client_data:
            QMessageBox.critical(self.main_window, "Erreur", "Client non trouvé.")
            return

        dialog = CrudDialog(
            mode='edit',
            fields_config=self.fields_config,
            title="Modifier le Client",
            data=client_data,
            parent=self.main_window
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_data = dialog.get_data()
            if self.model.update(client_id, updated_data):
                QMessageBox.information(self.main_window, "Succès", "Client mis à jour avec succès.")
                self.load_clients()
            else:
                QMessageBox.critical(self.main_window, "Erreur", "Impossible de mettre à jour le client.")

    def delete_client(self):
        """Supprime le client sélectionné après confirmation."""
        client_id = self.view.get_selected_client_id()
        if client_id is None:
            QMessageBox.warning(self.main_window, "Aucune Sélection", "Veuillez sélectionner un client à supprimer.")
            return

        client_data = self.model.get_by_id(client_id)
        if not client_data:
             QMessageBox.critical(self.main_window, "Erreur", "Client non trouvé.")
             return

        reply = QMessageBox.question(
            self.main_window,
            "Confirmation de Suppression",
            f"Êtes-vous sûr de vouloir supprimer le client '{client_data['name']}' ?\n"
            "Cette action ne peut pas être annulée.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.model.delete(client_id):
                QMessageBox.information(self.main_window, "Succès", "Client supprimé avec succès.")
                self.load_clients()
            else:
                QMessageBox.critical(self.main_window, "Erreur",
                                     "Impossible de supprimer le client. Il est probablement lié à des factures existantes.")
