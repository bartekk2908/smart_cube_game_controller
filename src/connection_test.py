import asyncio
from bleak import BleakScanner, BleakClient


async def run():
    
    # 1. Skanowanie urządzeń
    devices = await BleakScanner.discover()
    
    target_device = None
    
    # Szukamy kostki. Często mają w nazwie "QY", "Qiyi", "Smart" lub podobne.
    # Jeśli Twoja kostka nazywa się inaczej, skrypt wypisze wszystkie urządzenia.
    for d in devices:
        name = d.name or "Nieznane"
        print(f"Znaleziono: {name} | Adres: {d.address}")
        
        # Prosta heurystyka do znalezienia kostki
        if "QY" in name or "Smart" in name or "Cube" in name:
            target_device = d

    if not target_device:
        print("\nNie udało się automatycznie wykryć kostki po nazwie.")
        print("Skopiuj adres MAC swojej kostki z listy powyżej i wpisz go w kodzie ręcznie.")
        return

    print(f"\n--- PRÓBA POŁĄCZENIA Z: {target_device.name} ({target_device.address}) ---")

    # 2. Łączenie
    try:
        async with BleakClient(target_device.address) as client:
            print(f"POŁĄCZONO: {client.is_connected}")
            
            # 3. Pobieranie usług (Services)
            print("\nDostępne usługi i charakterystyki:")
            for service in client.services:
                print(f"[Service] {service.uuid}")
                for char in service.characteristics:
                    print(f"  - [Char] {char.uuid} ({', '.join(char.properties)})")
            
            print("\nTest zakończony sukcesem. Połączenie działa.")
            
    except Exception as e:
        print(f"BŁĄD POŁĄCZENIA: {e}")


if __name__ == "__main__":
    asyncio.run(run())
