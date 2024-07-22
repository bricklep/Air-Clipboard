import sys
import qrcode
import boto3
import uuid
from PIL import ImageGrab, Image
from botocore.exceptions import NoCredentialsError
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer
from io import BytesIO
import pyperclip

class QRApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QR Code Generator from Clipboard")
        
        self.layout = QVBoxLayout()
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.qr_label = QLabel(self)
        self.upload_button = QPushButton("Upload Clipboard Image to S3", self)
        self.upload_button.clicked.connect(self.upload_clipboard_image)
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.qr_label)
        self.layout.addWidget(self.upload_button)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        # Timer to refresh the label every 1 second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_qr)
        self.timer.start(1000)

    def update_qr(self):
        text = pyperclip.paste()  # Get text from clipboard
        if text != self.label.text():  # Update only if text changes
            self.label.setText(text)
            qr_img = qrcode.make(text)
            buf = BytesIO()
            qr_img.save(buf)
            buf.seek(0)
            pixmap = QPixmap()
            pixmap.loadFromData(buf.getvalue())
            self.qr_label.setPixmap(pixmap)
            self.resize(pixmap.width() + 20, pixmap.height() + 100)

     # Automatically upload any image found in clipboard
    img = ImageGrab.grabclipboard()  # Capture clipboard content
    if isinstance(img, Image.Image):
        bucket_name = 'my-qr-air-clipboard'
        object_name = f"images/{uuid.uuid4()}.png"

        # Save the image to a BytesIO object
        img_byte_array = BytesIO()
        img.save(img_byte_array, format="PNG")
        img_byte_array.seek(0)

        # Upload to S3
        s3_client = boto3.client('s3')
        s3_client.upload_fileobj(img_byte_array, bucket_name, object_name)

        # Generate signed URL
        signed_url = self.generate_signed_url(bucket_name, object_name)

        # Generate QR code for the signed URL
        qr_img = qrcode.make(signed_url)
        buf = BytesIO()
        qr_img.save(buf)
        buf.seek(0)
        pixmap = QPixmap()
        pixmap.loadFromData(buf.getvalue())
        self.qr_label.setPixmap(pixmap)  # Update the QR label with the new QR code
        self.label.setText("Image uploaded! QR code updated.")

    def generate_signed_url(self, bucket_name, object_name, expiration=3600):
        s3_client = boto3.client('s3')
        try:
            response = s3_client
            response = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_name},
                ExpiresIn=expiration
            )
            return response
        except NoCredentialsError:
            return "Credentials not available"

    def upload_clipboard_image(self):
        bucket_name = 'my-qr-air-clipboard'
        try:
            # Get image from clipboard
            img = ImageGrab.grabclipboard()

            if isinstance(img, Image.Image):
                # Create a unique file name
                object_name = f"images/{uuid.uuid4()}.png"
                
                # Save the image to a BytesIO object
                img_byte_array = BytesIO()
                img.save(img_byte_array, format="PNG")
                img_byte_array.seek(0)

                # Upload to S3
                s3_client = boto3.client('s3')
                s3_client.upload_fileobj(img_byte_array, bucket_name, object_name)

                # Generate signed URL
                signed_url = self.generate_signed_url(bucket_name, object_name)
                print("Signed URL:", signed_url)

                # Optionally display the signed URL in the UI or handle as needed
                self.label.setText(f"Uploaded! Signed URL: {signed_url}")

            else:
                self.label.setText("No image found in clipboard")

        except Exception as e:
            self.label.setText(f"Error: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QRApp()
    window.show()
    sys.exit(app.exec_())