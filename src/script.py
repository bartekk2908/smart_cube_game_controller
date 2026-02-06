import asyncio
import struct
from bleak import BleakClient
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# --- KONFIGURACJA ---
CUBE_MAC = "CC:A3:00:00:F6:CF" # Twój adres MAC

CHAR_UUID = "0000fff6-0000-1000-8000-00805f9b34fb"
AES_KEY = bytes.fromhex("57b1f9abcd5ae8a79cb98ce7578c5108")

MOVES_MAP = {
    0x1: "L'", 0x2: "L", 0x3: "R'", 0x4: "R",
    0x5: "D'", 0x6: "D", 0x7: "U'", 0x8: "U",
    0x9: "F'", 0x0a: "F", 0x0b: "B'", 0x0c: "B"
}

# --- KRYPTOGRAFIA I CRC ---

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
    
    cipher = Cipher(algorithms.AES(AES_KEY), modes.ECB(), backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(payload) + encryptor.finalize()

def decrypt_data(encrypted_data: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(AES_KEY), modes.ECB(), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(encrypted_data) + decryptor.finalize()

# --- GŁÓWNA PĘTLA ---

async def main():
    print(f"Łączenie z {CUBE_MAC}...")
    
    async with BleakClient(CUBE_MAC) as client:
        print(f"Połączono: {client.is_connected}")

        # Funkcja pomocnicza do wysyłania ACK (Potwierdzenia)
        async def send_ack(original_msg_decrypted):
            # ACK składa się z: fe 09 [Opcode + Timestamp z oryginału] [CRC]
            # Bajty 2-7 (indeksowanie od 0) to Opcode (1b) + Timestamp (4b) = 5 bajtów
            # README mówi "bytes 3-7", co przy indeksowaniu od 1 daje to samo.
            content_to_ack = original_msg_decrypted[2:7]
            
            payload = bytearray([0xfe, 0x09])
            payload.extend(content_to_ack)
            
            crc = crc16_modbus(payload)
            payload.extend(struct.pack("<H", crc))
            
            # Szyfrujemy i wysyłamy
            encrypted_ack = encrypt_data(payload)
            # print(f"  -> Wysyłanie ACK dla wiadomości typu {hex(content_to_ack[0])}")
            await client.write_gatt_char(CHAR_UUID, encrypted_ack)

        # Handler jest teraz zdefiniowany wewnątrz main, aby widział 'client' i 'send_ack'
        async def notification_handler(sender, data):
            try:
                decrypted = decrypt_data(data)
                if decrypted[0] != 0xfe: return

                opcode = decrypted[2]

                # --- 0x02: CUBE HELLO ---
                if opcode == 0x02:
                    battery = decrypted[35]
                    print(f"✅ OTRZYMANO CUBE HELLO! Bateria: {battery}%")
                    # Tutaj był problem - brakowało ACK!
                    await send_ack(decrypted) 

                # --- 0x03: STATE CHANGE (RUCH) ---
                elif opcode == 0x03:
                    move_byte = decrypted[34]
                    move_name = MOVES_MAP.get(move_byte, f"? ({hex(move_byte)})")
                    
                    # Sprawdź czy wymaga ACK (gdy kostka ułożona lub glitch)
                    # Bajt 91 (indeks 91) to "needs ACK"
                    needs_ack = decrypted[91] == 1
                    
                    status = ""
                    if needs_ack:
                        status = " (SOLVED/SYNC!)"
                        # Jeśli kostka prosi o potwierdzenie stanu, też wysyłamy ACK
                        await send_ack(decrypted)
                    
                    print(f"➡️ RUCH: {move_name}{status}")
                    
            except Exception as e:
                print(f"Błąd w handlerze: {e}")

        # 1. Start nasłuchiwania
        await client.start_notify(CHAR_UUID, notification_handler)

        # 2. Wysyłanie App Hello (Twoje dane)
        mac_bytes = bytes.fromhex(CUBE_MAC.replace(":", ""))
        reversed_mac = mac_bytes[::-1]
        
        payload = bytearray([0xfe, 0x15])
        payload.extend(b'\x00' * 11)
        payload.extend(reversed_mac)
        
        crc = crc16_modbus(payload)
        payload.extend(struct.pack("<H", crc))
        
        print("Wysyłanie App Hello...")
        await client.write_gatt_char(CHAR_UUID, encrypt_data(payload))

        print("--- Oczekiwanie na ruchy (Ctrl+C aby zakończyć) ---")
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nRozłączono.")