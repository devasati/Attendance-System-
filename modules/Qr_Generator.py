import qrcode
from PIL import Image
import io
import base64
from modules.Encryptor_Decryptor import simple_encrypt

def generate_qr(qr_id, registration_number, lecture_id, date, random_no):

    final_info = f"{qr_id}\n{registration_number}\n{lecture_id}\n{date}\n{random_no}"
    qr_data = simple_encrypt(final_info, "abcd1234")

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )  #QR Code Configuration
    qr.add_data(qr_data) # Adds the data to the QR code
    qr.make(fit=True) #  Automatically adjusts the QR code size

    # Create PIL Image
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return qr_base64
