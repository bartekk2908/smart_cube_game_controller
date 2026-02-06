import asyncio
from bleak import BleakScanner, BleakClient


async def run():
    
    devices = await BleakScanner.discover()
    target_device = None
    
    for d in devices:
        name = d.name or "unknown"
        print(f"Found: {name} | Address: {d.address}")
        
        if "QY" in name or "Smart" in name or "Cube" in name:
            target_device = d

    if not target_device:
        print("QiYi smart cube not found.")
        return

    print(f"\n CONNECTING TO: {target_device.name} ({target_device.address})")

    try:
        async with BleakClient(target_device.address) as client:
            print(f"CONNECTED: {client.is_connected}")
            
            print("\nAvailable services and characteristics:")
            for service in client.services:
                print(f"[Service] {service.uuid}")
                for char in service.characteristics:
                    print(f"  - [Char] {char.uuid} ({', '.join(char.properties)})")
            
            print("\nTest ended successfully.")
            
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(run())
