import asyncio
from theia.probe.adapters.base import BasePlatformAdapter


class ProbeEngine:
    def __init__(self, adapters: list[BasePlatformAdapter]):
        self.adapters = adapters
    async def run(self, seed):
        tasks = [x.probe(seed) for x in self.adapters]
        data = await asyncio.gather(*tasks, return_exceptions=True)
        clean_data = []
        for i in data:
            if type(i) == tuple:
                clean_data.append(i)
        return clean_data