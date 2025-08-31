from PyQt6.QtWidgets import (
    QDialog, QLineEdit, QPushButton, QVBoxLayout,
    QFormLayout, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connexion")
        self.setModal(True) # Bloque la fenêtre parent
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nom d'utilisateur")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Mot de passe")

        form_layout.addRow(QLabel("Utilisateur:"), self.username_input)
        form_layout.addRow(QLabel("Mot de passe:"), self.password_input)

        layout.addLayout(form_layout)

        self.login_button = QPushButton("Connexion")
        self.cancel_button = QPushButton("Annuler")

        # Connecter les signaux aux slots
        self.login_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # Ajouter les boutons au layout
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # Rendre le bouton de connexion par défaut
        self.login_button.setDefault(True)

    def get_credentials(self):
        """Retourne le nom d'utilisateur et le mot de passe saisis."""
        return self.username_input.text().strip(), self.password_input.text()

# Pour tester ce dialogue seul
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    dialog = LoginDialog()

    # exec() retourne QDialog.DialogCode.Accepted ou QDialog.DialogCode.Rejected
    if dialog.exec():
        username, password = dialog.get_credentials()
        QMessageBox.information(None, "Succès", f"Utilisateur: {username}\nMot de passe: {'*' * len(password)}")
        print("Connexion acceptée")
    else:
        QMessageBox.warning(None, "Annulé", "La connexion a été annulée.")
        print("Connexion refusée")

    sys.exit(0)
