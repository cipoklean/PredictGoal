import asyncio
from server import calculate_odds

class C:
    async def info(self, msg: str) -> None:
        pass

c = C()

r = asyncio.run(calculate_odds("WC2026-M1", c))
print(r[:300])
