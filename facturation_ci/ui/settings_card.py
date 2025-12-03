from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor, QFont, QIcon, QCursor
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from ui.theme import BG_CARD, TEXT_MAIN, TEXT_SEC, PRIMARY, BORDER

class SettingsCard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, title, description, icon_path=None, parent=None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        # Style
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            QFrame:hover {{
                border: 1px solid {PRIMARY};
                background-color: rgba(255, 158, 29, 0.05);
            }}
        """)

        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # Icon
        if icon_path:
            # We can use a QLabel with Pixmap or Icon
            # For now, just a placeholder label if no icon, or specific icon logic
            pass

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {TEXT_MAIN}; font-weight: bold; font-size: 16px; border: none; background: transparent;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Description
        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet(f"color: {TEXT_SEC}; font-size: 13px; border: none; background: transparent;")
            desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
