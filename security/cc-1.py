#encoding=utf8

from PyKCS11 import *
import platform
import sys
from os import listdir 
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from OpenSSL.crypto import load_certificate, load_crl, FILETYPE_ASN1, FILETYPE_PEM, Error, X509Store, X509StoreContext, X509StoreFlags, X509StoreContextError
from cryptography.x509.oid import NameOID    
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.asymmetric import padding, padding
from cryptography.exceptions import *
from OpenSSL.crypto import *
from getpass import getpass
import base64
import unicodedata

class CitizenCard:
    def __init__(self):
        self.pkcs11 = PyKCS11.PyKCS11Lib()
        self.lib = '/usr/local/lib/libpteidpkcs11.so'
        self.pkcs11.load(self.lib)
        self.certificate = None
        self.store = self.load_store_certificates()
        self.session = self.readInit()
        self.getCCinfo = self.getCCinfo()
   
 ##############################################################################################################   
    def load_store_certificates(self): 
        rootCerts = ()
        trustedCerts = ()
        crlList = ()
        dirname = ["CCCerts/","CRL/"]
        store = X509Store()

        for name in listdir(dirname[0]):
            try:
                cert_info = open(dirname[0] + name, 'rb').read()
            except IOError:
                print("IO Exception while reading file : {:s} {:s}".format(dirname[0], name))
                exit(10)
            else:
                if ".cer" in name:
                    try:
                        if "0012" in name or "0013" in name or "0015" in name:
                            certAuth = load_certificate(FILETYPE_PEM, cert_info)
                            store.add_cert(certAuth)
                        elif "Raiz" in name:
                            root = load_certificate(FILETYPE_ASN1,cert_info)
                            store.add_cert(root)
                        else:
                            certAuth = load_certificate(FILETYPE_ASN1, cert_info)
                            store.add_cert(certAuth)
                    except:
                        print("Exception while loading certificate from file : {:s}{:s}".format(dirname[0], name))
                        exit(10)
                    else:
                        trustedCerts = trustedCerts + (certAuth,)
                elif ".crt" in name:
                    try:
                        root = load_certificate(FILETYPE_PEM, cert_info)
                        store.add_cert(root)
                    except:
                        print("Exception while loading certificate from file : {:s}{:s}".format(dirname[0], name))
                        exit(10)
                    else:
                        rootCerts = rootCerts + (root,)
                        
        print("Loaded Root certificates : {:d} out of {:d} ".format(len(rootCerts), len(listdir(dirname[0]))))
        print("Loaded Authentication certificates: {:d} out of {:d} ".format(len(trustedCerts), len(listdir(dirname[0]))))
        
        for name in listdir(dirname[1]):
            try:
                crl_info = open(dirname[1] + "/" + name, 'rb').read()
            except IOError:
                print("IO Exception while reading file : {:s}{:s}".format(dirname[0], name))
            else:
                if ".crl" in name:
                    crls = load_crl(FILETYPE_ASN1, crl_info)
                    store.add_crl(crls)
            crlList = crlList + (crls,)
        print("Certificate revocation lists loaded: {:d} out of {:d} ".format(len(crlList), len(listdir(dirname[1]))))

        return store
    
##########################################################################################################################################
    def readInit(self):
        AUTHENTICATION_CERT = "CITIZEN AUTHENTICATION CERTIFICATE"
        AUTHENTICATION_KEY  = "CITIZEN AUTHENTICATION KEY"
        SIGNATURE_CERT = "CITIZEN SIGNATURE CERTIFICATE"
        SIGNATURE_KEY  = "CITIZEN SIGNATURE KEY"
        
        try:
            pkcs11 = PyKCS11Lib()
            pkcs11.load(self.lib)
        except PyKCS11Error:
            print("We couldn't load the PyKCS11 Lib")    
        else:
            try:
                print("################")
                self.slots = pkcs11.getSlotList(tokenPresent=True)
                print(str(len(self.slots)) + " slots found")
                print("################")

                if len(self.slots) < 1:
                    exit(-1)
                lst = []
                for x in range(0, len(self.slots)):
                    lst.append(pkcs11.openSession(self.slots[x]))
                return lst    
            except:
                print("No Citizen Card detected, please insert one!")
                exit(11)
###################################################################################################
    def getCertificates(self, sessionId):
        AUTHENTICATION_CERT = "CITIZEN AUTHENTICATION CERTIFICATE"
  
        get_info = self.session[sessionId].findObjects(template=([(PyKCS11.CKA_CLASS, PyKCS11.CKO_CERTIFICATE), (PyKCS11.CKA_LABEL, AUTHENTICATION_CERT)]))
       
        try:
         der = bytes([x.to_dict()['CKA_VALUE']for x in get_info][0])
        except(IndexError):
            print(" Certificate \"{:15s}\" not found in PyKCSS session with the id :{:2d}".format(AUTHENTICATION_CERT))
            return None
        else:
            try:
                certificate = x509.load_der_x509_certificate(der, default_backend()).public_bytes(Encoding.PEM)

            except:
                print("Error while loading certificate")        
                return None
            else:
                print("Certifiate from de smartcard loaded")
                certificate = x509.load_pem_x509_certificate(certificate, default_backend())
                
                return certificate
########################################################################################################
    def getCCinfo(self, certificate=None):
        if not certificate:
            certificate = self.getCertificates(0)

         
        name = certificate.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
        serial_number = certificate.subject.get_attributes_for_oid(NameOID.SERIAL_NUMBER)[0].value
        serial_number = int(serial_number[2:10])

        return name, serial_number
##########################################################################################################        
    def ver_cert_chain(self, trustedCert):
        storeContext = None
        storeContext = X509StoreContext(self.store, trustedCert).verify_certificate()

        if storeContext is None:
            print("The smartcard was sucessfully verified")
            return True
        else:
            return False    

###############################################################################################################
    def signature(self, sessionId, message):
        data = bytes(message, 'utf-8')
        session = self.pkcs11.openSession(sessionId)
        private_key = session.findObjects([(PyKCS11.CKA_CLASS, PyKCS11.CKO_PRIVATE_KEY), (PyKCS11.CKA_LABEL, 'CITIZEN AUTHENTICATION KEY')])[0]
        signature = bytes(session.sign(private_key,data, Mechanism(CKM_SHA256_RSA_PKCS, None)))
        session.closeSession()
        return signature     
####################################################################################################################
    def verify_signature(self, cert, data, signature):
        public_key = cert.public_key()

        if isinstance(public_key, rsa.RSAPublicKey):
            print("Certificate has a RSA public key")
        else:
            print("Certificate has not a RSA public key")    
        
        try:
            public_key.verify(signature, data, padding.PKCS1v15(), hashes.SHA256())
            print("Verification succeeded")
            return True
        except:
            print("Verification failed")
            return False
######################################################################################################################
    def login(self,sessionIdx):
        session = self.session[sessionIdx]
        
        pin = None
        while True:
            pin = input('Insert PIN: ') 
            try:
                session.login(pin)
            except PyKCS11Error:
                raise PinError()
                return False
            else:
                return True
    def logout(self, sessionIdx):
        session = self.session[slot]
        session.logout()
        session.closeSession()            

######################################################################################################################
if __name__ == '__main__':
    try:
        pteid = CitizenCard()
        info = pteid.getCCinfo
        slot = -1
        if len(pteid.session) > 0:
            temp = ''.join('Slot{:3d}-> Fullname: {:10s}, Serial Number: {:3d}\n'.format(i, info[0], info[1]) for i in range(0, len(pteid.slots)))

            while slot < 0 or slot > len(pteid.session):
                slot = input("Available Slots: \n{:40s} \n\nWhich Slot do you wish to use? ".format(temp))
                if slot.isdigit():
                    slot = int(slot)
                else:
                    slot = -1
        for i in range(0, len(pteid.session)):
            if slot != i:
                pteid.session[i].closeSession()

        st1r = pteid.getCertificates(slot)
        print("\nIs this certificate valid: ", pteid.ver_cert_chain(st1r))

        pteid.login(slot)

        datatobeSigned = "Random Randomly String"
        signedData = pteid.signature(slot, datatobeSigned)

        print(datatobeSigned + "\n")
        if (pteid.verify_signature(pteid.getCertificates(slot), bytes(datatobeSigned, "utf-8"), signedData)):
            print("Verified")

    except KeyboardInterrupt:
        pteid.logout(slot)
        pteid.session[slot].closeSession()   