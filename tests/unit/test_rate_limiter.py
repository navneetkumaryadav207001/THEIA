import asyncio
import time
import unittest
from theia.core.networking.rate_limiter import RateLimiter


class TestRateLimiter(unittest.IsolatedAsyncioTestCase):
    async def test_burst_capacity(self):
        """Test that requests up to capacity C are served immediately without waiting."""
        limiter = RateLimiter(C=3, r=1)
        start = time.monotonic()

        for _ in range(3):
            await limiter.acquire()

        elapsed = time.monotonic() - start
        self.assertLess(elapsed, 0.05, "Burst capacity should be granted without delay")

    async def test_sustained_rate_limiting(self):
        """Test that sustained requests are paced at rate r."""
        limiter = RateLimiter(C=1, r=4)  # 1 token capacity, 4 tokens per second (0.25s per token)
        start = time.monotonic()

        for _ in range(5):
            await limiter.acquire()

        elapsed = time.monotonic() - start
        # 1 burst + 4 refills * 0.25s = ~1.0s total
        self.assertGreaterEqual(elapsed, 0.95, "Rate limiter should pace requests to ~1.0s")
        self.assertLess(elapsed, 1.25, "Rate limiter should not excessively overshoot")

    async def test_concurrent_workers(self):
        """Test concurrent tasks racing for tokens with asyncio.gather."""
        limiter = RateLimiter(C=2, r=2)  # 2 burst, 0.5s per token refill
        start = time.monotonic()
        timestamps = []

        async def worker():
            await limiter.acquire()
            timestamps.append(time.monotonic() - start)

        tasks = [worker() for _ in range(4)]
        await asyncio.gather(*tasks)

        self.assertEqual(len(timestamps), 4)
        # First 2 should be immediate
        self.assertLess(timestamps[0], 0.05)
        self.assertLess(timestamps[1], 0.05)
        # Next 2 should be spaced around 0.5s and 1.0s
        self.assertGreaterEqual(timestamps[2], 0.45)
        self.assertGreaterEqual(timestamps[3], 0.95)


if __name__ == "__main__":
    unittest.main()
