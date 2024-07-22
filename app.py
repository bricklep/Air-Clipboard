import sys
import qrcode
import boto3
import uuid
from PIL import ImageGrab, Image
from botocore.exceptions import NoCredentialsError
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

    # Usage
    # upload_file_to_s3('path/to/photo.jpg', 'your-bucket-name')
    # function to upload a file to S3 bucket
    def upload_file_to_s3(file_name, bucket, object_name=None):
        s3_client = boto3.client('s3')
        if object_name is None:
            object_name = file_name
        try:
            response = s3_client.upload_file(file_name, bucket, object_name)
            print(f"Upload Successful: {object_name}")
        except Exception as e:
            print(f"Error: {e}")

    def upload_test_file(bucket_name, file_path, object_name=None):
        # Create a test file
        if object_name is None:
            object_name = file_path.split('/')[-1]
        
        with open(file_path, 'w') as f:
            f.write("This is a test file.")

        # Upload to S3
        s3_client = boto3.client('s3')
        try:
            s3_client.upload_file(file_path, bucket_name, object_name)
            print(f"Upload Successful: {object_name}")
        except Exception as e:
            print(f"Error: {e}")

    # Usage
    upload_test_file('my-qr-air-clipboard', 'test_file.txt')

    def generate_signed_url(bucket_name, object_name, expiration=3600):
        s3_client = boto3.client('s3')
        try:
            response = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_name},
                ExpiresIn=120
            )
            return response
        except NoCredentialsError:
            return "Credentials not available"

     # Usage
    # bucket_name = 'my-qr-air-clipboard'
    # object_name = 'test_file.txt'
    # signed_url = generate_signed_url(bucket_name, object_name)
    # print("Signed URL:", signed_url)

    def upload_clipboard_image_to_s3(bucket_name):
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
                signed_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': object_name},
                    ExpiresIn=3600  # URL valid for 1 hour
                )
                return signed_url

            else:
                return "No image found in clipboard"

        except Exception as e:
            return f"Error: {str(e)}"

    bucket_name = 'my-qr-air-clipboard'
    signed_url = upload_clipboard_image_to_s3(bucket_name)
    print("Signed URL:", signed_url)
    


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QRApp()
    window.show()
    sys.exit(app.exec_())