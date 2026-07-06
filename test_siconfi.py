import asyncio
from app.services.siconfi.siconfi_service import SiconfiService

async def main():
    service = SiconfiService()
    print(await service.get_entes())

asyncio.run(main())
