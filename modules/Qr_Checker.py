from modules.Encryptor_Decryptor import simple_decrypt

def checker_qr_code(qr_data, qr_id, registration_number, lecture_id, date, random_no):
    try:
        # Decrypt the data
        decrypted_data = simple_decrypt(qr_data, "abcd1234")

        # Prepare final info to compare with decrypted data
        final_info = f"{qr_id}\n{registration_number}\n{lecture_id}\n{date}\n{random_no}"

        if decrypted_data == final_info:
            return 1  # Decrypted data matches final info

        else:
            return 0  # Decrypted data does not match

    except Exception as e:
        print(f"Error: {e}")
        return None  # Return None
