import time
import asyncio


class RateLimiter():

    def __init__(self, C:float=125, r:float=5):
        self.t_last = time.monotonic()
        self.r = r
        self.tokens = C
        self.C = C
        self.shared_lock = asyncio.Lock()

    async def acquire(self)->None:
        async with self.shared_lock:
            delta_t = time.monotonic() - self.t_last
            tokens_earned = delta_t * self.r
            self.tokens = min(self.C,self.tokens+tokens_earned)
            if(self.tokens < 1.0):
                await asyncio.sleep((1.0-self.tokens)/self.r)
                self.tokens += 1
            self.tokens -= 1
            self.t_last =  time.monotonic()
            return None