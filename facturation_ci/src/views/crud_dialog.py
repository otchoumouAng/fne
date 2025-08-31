from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QMessageBox, QDialogButtonBox, QTextEdit
)

class CrudDialog(QDialog):
    def __init__(self, mode, fields_config, title, data=None, parent=None):
        """
        Boîte de dialogue générique pour les opérations CRUD.
        :param mode: 'new' ou 'edit'.
        :param fields_config: Liste de dictionnaires décrivant les champs du formulaire.
        :param title: Titre de la fenêtre.
        :param data: Dictionnaire de données pour peupler le formulaire en mode 'edit'.
        """
        super().__init__(parent)

        self.mode = mode
        self.fields_config = fields_config
        self.widgets = {}

        self.setWindowTitle(title)
        self.setMinimumWidth(400)

        self.setup_ui()

        if self.mode == 'edit' and data:
            self.set_data(data)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        for field in self.fields_config:
            field_name = field['name']
            field_label = field['label']
            field_type = field.get('type', 'QLineEdit') # QLineEdit par défaut

            if field_type == 'QTextEdit':
                widget = QTextEdit()
            else: # 'QLineEdit'
                widget = QLineEdit()

            self.widgets[field_name] = widget
            form_layout.addRow(f"{field_label}:", widget)

        main_layout.addLayout(form_layout)

        # Boutons OK et Annuler
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def set_data(self, data):
        """Peuple les champs du formulaire avec les données fournies."""
        for field_name, widget in self.widgets.items():
            value = data.get(field_name)
            if isinstance(value, (int, float)):
                value = str(value)

            if value is not None:
                if isinstance(widget, QTextEdit):
                    widget.setPlainText(value)
                else:
                    widget.setText(value)

    def get_data(self):
        """Récupère les données des champs du formulaire sous forme de dictionnaire."""
        data = {}
        for field_name, widget in self.widgets.items():
            if isinstance(widget, QTextEdit):
                data[field_name] = widget.toPlainText().strip()
            else:
                data[field_name] = widget.text().strip()
        return data

    def accept(self):
        """Surcharge de la méthode accept pour ajouter une validation."""
        # Validation simple : vérifier que les champs requis ne sont pas vides
        for field in self.fields_config:
            if field.get('required', False):
                field_name = field['name']
                data = self.get_data()
                if not data.get(field_name):
                    QMessageBox.warning(self, "Champ Requis", f"Le champ '{field['label']}' ne peut pas être vide.")
                    return # Empêche la fermeture de la boîte de dialogue

        super().accept() # Si la validation passe, on accepte et on ferme.
