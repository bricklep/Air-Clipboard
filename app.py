import sys
import qrcode
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer
from io import BytesIO
import pyperclip

class QRApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QR Code Generator from Clipboard")
        layout = QVBoxLayout()
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)  # Center the text
        self.qr_label = QLabel(self)
        layout.addWidget(self.label)
        layout.addWidget(self.qr_label)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Timer to refresh every 1 second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_qr)
        self.timer.start(1000)

    def update_qr(self):
        text = pyperclip.paste()  # Get text from clipboard
        if text != self.label.text():  # Only update if text changes
            truncated_text = f"{text[:4]}******"  # Truncate and add stars
            self.label.setText(truncated_text)
            qr_img = qrcode.make(text)
            buf = BytesIO()
            qr_img.save(buf)
            buf.seek(0)
            pixmap = QPixmap()
            pixmap.loadFromData(buf.getvalue())
            self.qr_label.setPixmap(pixmap)
            self.resize(pixmap.width() + 20, pixmap.height() + 100)  # Resize window

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QRApp()
    window.show()
    sys.exit(app.exec_())