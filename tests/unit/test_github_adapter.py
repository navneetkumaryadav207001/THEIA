from datetime import datetime, timezone
import json
import unittest
from unittest.mock import AsyncMock, MagicMock
import httpx
from theia.core.networking.rate_limiter import RateLimiter
from theia.core.schemas.platform_type import PlatformType
from theia.core.schemas.seed import InvestigationSeed
from theia.core.schemas.seed_type import SeedType
from theia.probe.adapters.github import GithubAdapter


class TestGithubAdapter(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_client = MagicMock(spec=httpx.AsyncClient)
        self.mock_limiter = AsyncMock(spec=RateLimiter)
        self.adapter = GithubAdapter(self.mock_client, self.mock_limiter)

    async def test_non_username_seed_ignored(self):
        """Adapter should ignore seeds that are not USERNAME."""
        email_seed = InvestigationSeed(
            id=1,
            seed_type=SeedType.EMAIL,
            value="target@example.com",
            created_at=datetime.now(timezone.utc)
        )
        result = await self.adapter.probe(email_seed)
        self.assertIsNone(result)
        self.mock_client.get.assert_not_called()

    async def test_probe_user_found_200(self):
        """Adapter correctly parses a 200 OK GitHub user response."""
        mock_payload = {
            "login": "octocat",
            "html_url": "https://github.com/octocat",
            "avatar_url": "https://avatars.githubusercontent.com/u/583231",
            "bio": "GitHub mascot",
            "location": "San Francisco"
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
            value="octocat",
            created_at=datetime.now(timezone.utc)
        )

        result = await self.adapter.probe(seed)
        self.assertIsNotNone(result)
        profile, snapshot = result

        # Verify rate limiter was acquired
        self.mock_limiter.acquire.assert_awaited_once()

        # Verify profile fields
        self.assertEqual(profile.id, "cand_github_octocat")
        self.assertEqual(profile.platform, PlatformType.Github)
        self.assertEqual(profile.username, "octocat")
        self.assertEqual(profile.profile_url, "https://github.com/octocat")
        self.assertEqual(profile.avatar_url, "https://avatars.githubusercontent.com/u/583231")
        self.assertEqual(profile.bio_raw, "GitHub mascot")
        self.assertEqual(profile.location_raw, "San Francisco")
        self.assertEqual(profile.raw_snapshot_hash, snapshot.sha_256)

        # Verify snapshot
        self.assertEqual(snapshot.platform, PlatformType.Github)
        self.assertEqual(snapshot.raw, raw_bytes)

    async def test_probe_user_not_found_404(self):
        """Adapter returns None when GitHub responds with 404 Not Found."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 404
        self.mock_client.get = AsyncMock(return_value=mock_response)

        seed = InvestigationSeed(
            id=3,
            seed_type=SeedType.USERNAME,
            value="nonexistent",
            created_at=datetime.now(timezone.utc)
        )

        result = await self.adapter.probe(seed)
        self.assertIsNone(result)
        self.mock_limiter.acquire.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
