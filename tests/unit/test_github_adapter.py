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

    async def test_probe_user_found_with_events(self):
        """Adapter parses user profile and public activity timestamps."""
        user_payload = {
            "login": "torvalds",
            "html_url": "https://github.com/torvalds",
            "avatar_url": "https://avatars.githubusercontent.com/u/1024025",
            "bio": "Linux creator",
            "location": "Portland, OR"
        }
        events_payload = [
            {"type": "PushEvent", "created_at": "2026-09-19T20:00:00Z"},
            {"type": "PullRequestEvent", "created_at": "2026-09-19T22:30:00Z"}
        ]

        resp_user = MagicMock(spec=httpx.Response)
        resp_user.status_code = 200
        resp_user.content = json.dumps(user_payload).encode("utf-8")
        resp_user.json.return_value = user_payload

        resp_events = MagicMock(spec=httpx.Response)
        resp_events.status_code = 200
        resp_events.json.return_value = events_payload

        # Mock client.get to return user on 1st call, events on 2nd call
        self.mock_client.get = AsyncMock(side_effect=[resp_user, resp_events])

        seed = InvestigationSeed(
            id=2,
            seed_type=SeedType.USERNAME,
            value="torvalds",
            created_at=datetime.now(timezone.utc)
        )

        result = await self.adapter.probe(seed)
        self.assertIsNotNone(result)
        profile, snapshot = result

        # Verify profile fields
        self.assertEqual(profile.username, "torvalds")
        self.assertEqual(profile.bio_raw, "Linux creator")
        self.assertEqual(profile.location_raw, "Portland, OR")
        self.assertEqual(profile.raw_snapshot_hash, snapshot.sha_256)

        # Verify timestamps parsed
        self.assertIsNotNone(profile.observed_timestamps)
        self.assertEqual(len(profile.observed_timestamps), 2)
        expected_dt = datetime.fromisoformat("2026-09-19T20:00:00+00:00")
        self.assertIn(expected_dt, profile.observed_timestamps)
        self.assertEqual(profile.observed_timestamps[expected_dt], "PushEvent")

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


if __name__ == "__main__":
    unittest.main()
