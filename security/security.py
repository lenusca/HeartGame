import random
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import os
import cryptography
from cryptography.hazmat.primitives import padding

class Security:
    def __init__(self):
        self.key = None
        self.privKey = None
        self.pubKey = None

    def generate_secret_key(self, key):
        self.key = base64.b64decode(key)
    
    # Chave simetrica AES e modo OFB
    def encrypt(self, originalText):
        algorithm = algorithms.AES
        mode = modes.OFB
        iv = os.urandom(algorithm.block_size//8)
        cipher = Cipher(algorithm(self.key), mode(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        padder = cryptography.hazmat.primitives.padding.PKCS7(algorithm.block_size).padder()
        # bytes
        if isinstance(originalText, bytes):
            return  base64.b64encode(iv+encryptor.update(padder.update(originalText)))
        # string
        else:
            return  base64.b64encode(iv+encryptor.update(padder.update(bytes(originalText,'utf-8')) + padder.finalize())+encryptor.finalize()).decode('utf-8')

    def decrypt(self, cipherText):
        algorithm = algorithms.AES
        mode = modes.OFB
        ciphertext = base64.b64decode(cipherText)
        iv = ciphertext[:algorithm.block_size//8]
        text = ciphertext[algorithm.block_size//8:]
        cipher = Cipher(algorithm(self.key), mode(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        unpadder = cryptography.hazmat.primitives.padding.PKCS7(algorithm.block_size).unpadder()
        originalText = (unpadder.update(decryptor.update(text)+decryptor.finalize()) + unpadder.finalize())
        # string 
        try:
            originalText = originalText.decode('utf-8')
        # bytes
        except:
            originalText = base64.b64encode(originalText).decode('utf-8') 
        return originalText
    
    # RSA
    # chave privada
    def generatePrivKey(self, key):
        self.privKey = rsa.generate_private(65537, 2048, default_backend())
        encoding_privkey = self.priv_key.private_bytes(serialization.Encoding.PEM, erialization.PrivateFormat.PKCS8, serialization.BestAvailableEncryption(key if isinstance(key, bytes) else bytes(key, "utf-8")))
        return base64.b64encode(encoding_privkey).decode('utf-8')
        
    # chave publica
    def generatePubKey(self, key):
        self.pubKey = self.privKey.public_key()
        encoding_pubKey = self.pub_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.PKCS1)
        return base64.b64encode(encoding_pubKey).decode('utf-8')