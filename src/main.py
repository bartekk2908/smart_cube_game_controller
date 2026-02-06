import asyncio
import struct
from bleak import BleakClient, BleakScanner

from communication_utils import crc16_modbus, decrypt_data, encrypt_data
import input_mapper


CHAR_UUID = "0000fff6-0000-1000-8000-00805f9b34fb"

MOVES_MAP = {
    0x1: "L'", 0x2: "L", 0x3: "R'", 0x4: "R",
    0x5: "D'", 0x6: "D", 0x7: "U'", 0x8: "U",
    0x9: "F'", 0x0a: "F", 0x0b: "B'", 0x0c: "B"
}


async def main():
    target_device = None

    while target_device is None:
        print("Scanning for devices starting with QY-...")
        devices = await BleakScanner.discover(timeout=3.0)
        candidates = [d for d in devices if d.name and d.name.startswith("QY-")]

        if not candidates:
            print("No QY- devices found. Retrying...")
            await asyncio.sleep(1)
            continue

        for device in candidates:
            user_input = input(f"Found: {device.name} ({device.address}). Connect? (y/n): ")
            if user_input.lower() == 'y':
                target_device = device
                break
        
        if target_device is None:
            print("Rescanning...")

    cube_mac = target_device.address
    print(f"Connecting to {target_device.name} ({cube_mac})...")
    
    async with BleakClient(target_device) as client:
        print(f"Connected: {client.is_connected}")

        async def send_ack(original_msg_decrypted):
            content_to_ack = original_msg_decrypted[2:7]
            payload = bytearray([0xfe, 0x09])
            payload.extend(content_to_ack)
            crc = crc16_modbus(payload)
            payload.extend(struct.pack("<H", crc))
            encrypted_ack = encrypt_data(payload)
            await client.write_gatt_char(CHAR_UUID, encrypted_ack)

        async def notification_handler(sender, data):
            try:
                decrypted = decrypt_data(data)
                
                if decrypted[0] != 0xfe: return

                opcode = decrypted[2]

                if opcode == 0x03:
                    move_byte = decrypted[34]
                    
                    if move_byte in MOVES_MAP:
                        input_mapper.handle_cube_move(MOVES_MAP[move_byte])
                    
                    # move_name = MOVES_MAP.get(move_byte, f"? ({hex(move_byte)})")
                    # print(f"Move: {move_name}")

                    if decrypted[91] == 1:
                        await send_ack(decrypted)

                elif opcode == 0x02:
                    battery = decrypted[35]
                    print(f"✅ CUBE HELLO! Battery: {battery}%")
                    await send_ack(decrypted) 
                    
            except Exception:
                pass

        await client.start_notify(CHAR_UUID, notification_handler)

        mac_bytes = bytes.fromhex(cube_mac.replace(":", "").replace("-", ""))
        reversed_mac = mac_bytes[::-1]
        
        payload = bytearray([0xfe, 0x15])
        payload.extend(b'\x00' * 11)
        payload.extend(reversed_mac)
        
        crc = crc16_modbus(payload)
        payload.extend(struct.pack("<H", crc))
        
        print("Sending App Hello...")
        await client.write_gatt_char(CHAR_UUID, encrypt_data(payload))

        print("--- Waiting for moves (Silent Mode for Speed) ---")
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDisconnected.")
