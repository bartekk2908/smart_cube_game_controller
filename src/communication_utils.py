from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


AES_KEY = bytes.fromhex("57b1f9abcd5ae8a79cb98ce7578c5108")

GLOBAL_CIPHER = Cipher(algorithms.AES(AES_KEY), modes.ECB(), backend=default_backend())


def crc16_modbus(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if (crc & 0x0001):
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc


def encrypt_data(payload: bytes) -> bytes:
    remainder = len(payload) % 16
    if remainder != 0:
        padding_len = 16 - remainder
        payload += (b'\x00' * padding_len)
    
    encryptor = GLOBAL_CIPHER.encryptor()
    return encryptor.update(payload) + encryptor.finalize()


def decrypt_data(encrypted_data: bytes) -> bytes:
    decryptor = GLOBAL_CIPHER.decryptor()
    return decryptor.update(encrypted_data) + decryptor.finalize()
