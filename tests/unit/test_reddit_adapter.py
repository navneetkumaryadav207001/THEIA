from datetime import datetime, timezone
import json
import unittest
from unittest.mock import AsyncMock, MagicMock
import httpx
from theia.core.networking.rate_limiter import RateLimiter
from theia.core.schemas.platform_type import PlatformType
from theia.core.schemas.seed import InvestigationSeed
from theia.core.schemas.seed_type import SeedType
from theia.probe.adapters.reddit import RedditAdapter


class TestRedditAdapter(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_client = MagicMock(spec=httpx.AsyncClient)
        self.mock_limiter = AsyncMock(spec=RateLimiter)
        self.adapter = RedditAdapter(self.mock_client, self.mock_limiter)

    async def test_non_username_seed_ignored(self):
        """Adapter should ignore seeds that are not USERNAME."""
        phone_seed = InvestigationSeed(
            id=1,
            seed_type=SeedType.PHONE,
            value="+14155552671",
            created_at=datetime.now(timezone.utc)
        )
        result = await self.adapter.probe(phone_seed)
        self.assertIsNone(result)
        self.mock_client.get.assert_not_called()

    async def test_probe_user_found_200(self):
        """Adapter correctly parses a nested Reddit profile response."""
        mock_payload = {
            "kind": "t2",
            "data": {
                "name": "spez",
                "id": "1w72",
                "icon_img": "https://styles.redditmedia.com/avatar_123.png?width=256",
                "subreddit": {
                    "title": "Steve Huffman",
                    "public_description": "CEO of Reddit"
                },
                "is_suspended": False
            }
        }
        raw_bytes = json.dumps(mock_payload).encode("utf-8")

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = raw_bytes
        mock_response.json.return_value = mock_payload

        self.mock_client.get = AsyncMock(return_value=mock_response)

        seed = InvestigationSeed(
            id=2,
            seed_type=SeedType.USERNAME,
            value="spez",
            created_at=datetime.now(timezone.utc)
        )

        result = await self.adapter.probe(seed)
        self.assertIsNotNone(result)
        profile, snapshot = result

        # Verify rate limiter was acquired
        self.mock_limiter.acquire.assert_awaited_once()

        # Verify profile fields
        self.assertEqual(profile.id, "cand_reddit_spez")
        self.assertEqual(profile.platform, PlatformType.REDDIT)
        self.assertEqual(profile.username, "spez")
        self.assertEqual(profile.profile_url, "https://www.reddit.com/user/spez")
        self.assertEqual(profile.avatar_url, "https://styles.redditmedia.com/avatar_123.png?width=256")
        self.assertEqual(profile.bio_raw, "CEO of Reddit")
        self.assertIsNone(profile.location_raw)
        self.assertEqual(profile.raw_snapshot_hash, snapshot.sha_256)

        # Verify snapshot
        self.assertEqual(snapshot.platform, PlatformType.REDDIT)
        self.assertEqual(snapshot.raw, raw_bytes)

    async def test_probe_user_suspended_returns_none(self):
        """Adapter returns None if the account is suspended."""
        mock_payload = {
            "kind": "t2",
            "data": {
                "name": "banned_user",
                "is_suspended": True
            }
        }
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = json.dumps(mock_payload).encode("utf-8")
        mock_response.json.return_value = mock_payload

        self.mock_client.get = AsyncMock(return_value=mock_response)

        seed = InvestigationSeed(
            id=3,
            seed_type=SeedType.USERNAME,
            value="banned_user",
            created_at=datetime.now(timezone.utc)
        )

        result = await self.adapter.probe(seed)
        self.assertIsNone(result)

    async def test_probe_user_not_found_404(self):
        """Adapter returns None when Reddit responds with 404."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 404
        self.mock_client.get = AsyncMock(return_value=mock_response)

        seed = InvestigationSeed(
            id=4,
            seed_type=SeedType.USERNAME,
            value="nonexistent",
            created_at=datetime.now(timezone.utc)
        )

        result = await self.adapter.probe(seed)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
