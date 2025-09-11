from PyQt6.QtWidgets import QDialog
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt

from page._credit_note_list_dialog import Ui_CreditNoteListDialog
from models.avoir import FactureAvoirModel
from avoir_viewer_dialog import AvoirViewerDialog

class CreditNoteListDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.avoir_model = FactureAvoirModel(self.db_manager)

        self.ui = Ui_CreditNoteListDialog()
        self.ui.setupUi(self)

        self.setup_table()
        self.setup_connections()
        self.load_data()

    def setup_table(self):
        self.table_model = QStandardItemModel()
        self.table_model.setHorizontalHeaderLabels([
            'ID', 'Code Avoir', 'Date Création', 'Facture d\'Origine', 'Total TTC', 'Statut FNE'
        ])
        self.ui.avoirs_table_view.setModel(self.table_model)
        self.ui.avoirs_table_view.setColumnHidden(0, True)

        # Désactiver le bouton de certification par défaut
        self.ui.certify_button.setEnabled(False)

    def setup_connections(self):
        self.ui.button_box.rejected.connect(self.reject) # Close button
        self.ui.avoirs_table_view.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.ui.avoirs_table_view.doubleClicked.connect(self.open_avoir_details)
        # self.ui.certify_button.clicked.connect(self.certify_avoir)

    def load_data(self):
        avoirs = self.avoir_model.get_all()
        self.table_model.removeRows(0, self.table_model.rowCount())

        for avoir in avoirs:
            row = [
                QStandardItem(str(avoir['id'])),
                QStandardItem(avoir['code_avoir']),
                QStandardItem(avoir['date_creation'].strftime('%Y-%m-%d')),
                QStandardItem(avoir['code_facture_origine']),
                QStandardItem(f"{avoir['total_ttc']:.2f}"),
                QStandardItem(avoir['statut_fne'])
            ]
            self.table_model.appendRow(row)

        self.ui.avoirs_table_view.resizeColumnsToContents()

    def on_selection_changed(self, selected, deselected):
        is_selection = self.ui.avoirs_table_view.selectionModel().hasSelection()
        self.ui.certify_button.setEnabled(is_selection)

    def get_selected_avoir_id(self):
        selected_indexes = self.ui.avoirs_table_view.selectionModel().selectedRows()
        if not selected_indexes:
            return None
        model = self.ui.avoirs_table_view.model()
        id_index = model.index(selected_indexes[0].row(), 0)
        return int(model.data(id_index)) if model.data(id_index) else None

    def open_avoir_details(self, index):
        avoir_id = self.get_selected_avoir_id()
        if avoir_id is None:
            return

        dialog = AvoirViewerDialog(self.db_manager, avoir_id=avoir_id, parent=self)
        dialog.exec()

    # def certify_avoir(self):
    #     pass
