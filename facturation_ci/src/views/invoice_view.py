from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableView, QAbstractItemView, QHeaderView
)
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QColor
from PyQt.QtCore import Qt

class InvoiceView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        button_layout = QHBoxLayout()
        self.new_button = QPushButton("Nouvelle Facture")
        self.view_button = QPushButton("Consulter / Détailler")
        self.certify_button = QPushButton("Certifier FNE")
        self.pdf_button = QPushButton("Imprimer en PDF")

        button_layout.addWidget(self.new_button)
        button_layout.addWidget(self.view_button)
        button_layout.addWidget(self.certify_button)
        button_layout.addWidget(self.pdf_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.table_view = QTableView()
        self.table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_view.verticalHeader().setVisible(False)

        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)

        main_layout.addWidget(self.table_view)

        self.model = QStandardItemModel()
        self.table_view.setModel(self.model)

    def set_invoices(self, invoices):
        """Remplit le tableau avec la liste des factures."""
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['ID', 'Date', 'Client', 'Montant Total', 'Statut', 'Statut FNE', 'NIM FNE'])

        status_colors = {
            'draft': QColor('gray'),
            'certified': QColor('orange'),
            'paid': QColor('lightgreen'),
            'cancelled': QColor('lightcoral')
        }

        for invoice in invoices:
            row = [
                QStandardItem(str(invoice['id'])),
                QStandardItem(invoice['issue_date'].strftime('%d-%m-%Y')),
                QStandardItem(invoice['client_name']),
                QStandardItem(f"{invoice['total_amount']:.2f} €"),
                QStandardItem(invoice['status']),
                QStandardItem(invoice.get('fne_status', 'N/A')),
                QStandardItem(invoice.get('fne_nim', ''))
            ]

            # Colorier la ligne en fonction du statut
            status = invoice['status']
            if status in status_colors:
                for item in row:
                    item.setBackground(status_colors[status])

            self.model.appendRow(row)

        self.table_view.resizeColumnsToContents()
        self.table_view.setColumnHidden(0, True) # Cacher l'ID

    def get_selected_invoice_id(self):
        """Retourne l'ID de la facture sélectionnée."""
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            return None

        id_index = selected_indexes[0].sibling(selected_indexes[0].row(), 0)
        invoice_id = self.model.data(id_index)
        return int(invoice_id) if invoice_id else None
