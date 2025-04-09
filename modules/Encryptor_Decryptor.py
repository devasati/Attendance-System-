import base64

def simple_encrypt(text, key):
    """
    Simple encryption using XOR operation
    """
    encrypted = []
    for i in range(len(text)):
        key_c = key[i % len(key)]
        encrypted_c = chr(ord(text[i]) ^ ord(key_c))
        encrypted.append(encrypted_c)
    encrypted_text = ''.join(encrypted)
    return base64.b64encode(encrypted_text.encode()).decode()

def simple_decrypt(encrypted_text, key):
    """
    Simple decryption using XOR operation
    """
    encrypted_text = base64.b64decode(encrypted_text).decode()
    decrypted = []
    for i in range(len(encrypted_text)):
        key_c = key[i % len(key)]
        decrypted_c = chr(ord(encrypted_text[i]) ^ ord(key_c))
        decrypted.append(decrypted_c)
    return ''.join(decrypted)

