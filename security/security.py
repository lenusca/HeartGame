import random
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import os
import cryptography
from cryptography.hazmat.primitives.asymmetric import rsa, padding, ec
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives import serialization
import Crypto.PublicKey.RSA
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography import x509
from OpenSSL.crypto import *
from cryptography.x509.oid import *
import datetime
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
    
    # ECC e em comentario a RSA
    # chaves e certificado client
    def generateCertClient(self, client_id):
        password = "kikoeluna"
        #self.privKey = rsa.generate_private_key(65537, 2048, default_backend())
        self.privKey = ec.generate_private_key(ec.SECP384R1(), default_backend())

        self.pubKey = self.privKey.public_key()

        #encoding_privKey = self.privKey.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.BestAvailableEncryption(bytes(password, "utf-8")))
        
        encoding_privKey = self.privKey.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())

        #encoding_pubKey = self.pubKey.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        
        encoding_pubKey = self.pubKey.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)

        # Guardar chaves
        file = open("security/KEYS/privKeyClient"+str(client_id)+".PEM", "wb")
        file.write(encoding_privKey)
        file.close()
        # Guardar certificados num ficheiro (publico)
        file = open("security/KEYS/pubKeyClient"+str(client_id)+".PEM", "wb")
        file.write(encoding_pubKey)
        file.close()

        key = { 'pubKey': encoding_pubKey,'privKey': encoding_privKey}
        return key
    
        
    # chaves e certificado servidor com ECCipher e em comentario a RSA
    def generateCertServer(self, client_id):
        password = "kikoeluna"
        # SUBSTITUIR COM O DIFFIE HEL... e ECC
        #self.privKey = rsa.generate_private_key(65537, 2048, default_backend())
        self.privKey = ec.generate_private_key(ec.SECP384R1(), default_backend())

        self.pubKey = self.privKey.public_key()

        #encoding_privKey = self.privKey.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.BestAvailableEncryption(bytes(password, "utf-8")))

        encoding_privKey = self.privKey.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
        
        #encoding_pubKey = self.pubKey.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)

        encoding_pubKey = self.pubKey.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        
        # Não necessário
        # Guardar chaves
        file = open("security/KEYS/privKeyServer"+str(client_id)+".PEM", "wb")
        file.write(encoding_privKey)
        file.close()
        # Guardar certificados num ficheiro (publico)
        file = open("security/KEYS/pubKeyServer"+str(client_id)+".PEM", "wb")
        file.write(encoding_pubKey)
        file.close()  
        key = { 'pubKey': encoding_pubKey,'privKey': encoding_privKey}
        return key
        
    def getpubKey(self, key):
        self.pubKey = serialization.load_pem_public_key(key, default_backend())
        return self.pubKey

    def getprivKey(self, key):
        key = base64.b64decode(key.encode("utf-8"))
        self.privKey = serialization.load_pem_private_key(key, bytes("kikoeluna","utf -8"), default_backend())
        return self.privKey

    # gera certificado auto-assinado
    def generateCert(self, key):
        print(key)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"PT"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Aveiro"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, u"Aveiro"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"UA"),
            x509.NameAttribute(NameOID.COMMON_NAME, u"cert.ua.pt"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key
        ).serial_number(
        x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=1)
        ).add_extension(
            x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
            critical=False,
        ).sign(key, hashes.SHA256(), default_backend())
        # file = open("security/KEYS/certificado"+str(client_id)+".PEM", "wb")
        # file.write(encoding_privKey)
        # file.close()
        return cert

    def sign(self, message):
        if not self.privKey:
            raise Exception('KEY not valid')
        originalmessage = message.encode('utf-8')
        #padding=cryptography.hazmat.primitives.asymmetric.padding.PSS(mgf=cryptography.hazmat.primitives.asymmetric.padding.MGF1(hashes.SHA256()), salt_length=cryptography.hazmat.primitives.asymmetric.padding.PSS.MAX_LENGTH)
        #algorithm = hashes.SHA256()
        #return base64.b64encode(self.privKey.sign(originalmessage, padding, algorithm)).decode("utf-8")
        return base64.b64encode(self.privKey.sign(originalmessage, ec.ECDSA(hashes.SHA256()))).decode("utf-8")

    def verifySign(self, message, signature, pubKey):
        if not pubKey:
            raise Exception('KEY not valid')
        try:
            signature = base64.b64decode(signature.encode("utf-8"))
            originalmessage = message.encode('utf-8')
            #padding = cryptography.hazmat.primitives.asymmetric.padding.PSS(mgf=cryptography.hazmat.primitives.asymmetric.padding.MGF1(hashes.SHA256()), salt_length=cryptography.hazmat.primitives.asymmetric.padding.PSS.MAX_LENGTH)
            #signature = pubKey.verify(signature, originalmessage, padding, hashes.SHA256())
            signature = pubKey.verify(signature, originalmessage, ec.ECDSA(hashes.SHA256()))
            return True
        except InvalidSignature:
            return False

# s = Security()

# keys = s.generateCertClient(0)

# pubk = s.getpubKey(keys["pubKey"])


# cert = s.generateCert(pubk)

# print(cert)






