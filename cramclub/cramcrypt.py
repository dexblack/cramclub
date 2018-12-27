"""
Cryptographic operations.
"""
from base64 import b64encode, b64decode
from getpass import getpass
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

from cramlog import CramLog



class CramCrypt():
    """
    Wrapper for cryptographic engine.
    """
    passphrase = None
    iv = None
    crypter = None

    def __init__(self, initial_value, salt):
        """
        `initial_value` base64 encoded bytes[16].
        `salt` base64 encoded bytes[16].
        """
        self.logger = CramLog.instance()  # pylint: disable-msg=E1102
        self.passphrase = getpass(
            'Please type the encryption pass phrase and press Enter: ')
        self.iv = initial_value or get_random_bytes(16)
        self.salt = salt or get_random_bytes(16)

        try:
            self.secure_key = PBKDF2(password=self.passphrase, salt=self.salt, dkLen=32)
        except ValueError as err:
            self.logger.critical(err)
            raise RuntimeError('Failed to create cryptographic engine.')

    def build_engine(self):
        """
        Cryptographic engine type and mode.
        """
        return AES.new(key=self.secure_key, mode=AES.MODE_CBC, iv=self.iv)


    def encrypt(self, value):
        """
        Use AES CBC mode to encrypt the value.
        `value` is a UTF-8 string.
        Returns base64 encoded ascii string.
        """
        crypter = self.build_engine()

        seq = value.encode()
        padded = pad(seq, 16)
        encrypted = crypter.encrypt(padded)
        b64 = b64encode(encrypted)
        return b64.decode('ascii')


    def decrypt(self, value):
        """
        Use AES CBC mode to decrypt the value.
        `value` is a base64 encoded string or byte sequence.
        Returns decrypted value as UTF-8 string.
        """
        crypter = self.build_engine()

        encrypted = b64decode(value.encode())
        padded = crypter.decrypt(encrypted)
        seq = unpad(padded, 16)
        return seq.decode('utf-8')
