from datetime import datetime, timezone
import unittest
from unittest.mock import AsyncMock, MagicMock
from theia.core.schemas.platform_type import PlatformType
from theia.core.schemas.profile import CandidateProfile, RawSnapshot
from theia.core.schemas.seed import InvestigationSeed
from theia.core.schemas.seed_type import SeedType
from theia.probe.adapters.base import BasePlatformAdapter
from theia.probe.engine import ProbeEngine


class TestProbeEngine(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.seed = InvestigationSeed(
            id=1,
            seed_type=SeedType.USERNAME,
            value="alice",
            created_at=datetime.now(timezone.utc)
        )
        self.dummy_profile = CandidateProfile(
            id="cand_gh_alice",
            platform=PlatformType.Github,
            username="alice",
            profile_url="https://github.com/alice",
            raw_snapshot_hash="a" * 64
        )
        self.dummy_snapshot = RawSnapshot(
            raw=b"data",
            url="https://github.com/alice",
            platform=PlatformType.Github,
            sha_256="a" * 64
        )

    async def test_empty_adapters(self):
        """Engine returns an empty list when no adapters are registered."""
        engine = ProbeEngine(adapters=[])
        results = await engine.run(self.seed)
        self.assertEqual(results, [])

    async def test_all_adapters_succeed(self):
        """Engine aggregates candidates from all successful adapters."""
        adapter1 = MagicMock(spec=BasePlatformAdapter)
        adapter1.probe = AsyncMock(return_value=(self.dummy_profile, self.dummy_snapshot))

        adapter2 = MagicMock(spec=BasePlatformAdapter)
        adapter2.probe = AsyncMock(return_value=(self.dummy_profile, self.dummy_snapshot))

        engine = ProbeEngine(adapters=[adapter1, adapter2])
        results = await engine.run(self.seed)

        self.assertEqual(len(results), 2)
        adapter1.probe.assert_awaited_once_with(self.seed)
        adapter2.probe.assert_awaited_once_with(self.seed)

    async def test_fault_isolation_with_exceptions_and_nones(self):
        """Engine safely isolates exceptions and filters None results without crashing."""
        # Adapter 1: Success
        adapter_success = MagicMock(spec=BasePlatformAdapter)
        adapter_success.probe = AsyncMock(return_value=(self.dummy_profile, self.dummy_snapshot))

        # Adapter 2: Target not found (returns None)
        adapter_none = MagicMock(spec=BasePlatformAdapter)
        adapter_none.probe = AsyncMock(return_value=None)

        # Adapter 3: Crashes with network exception
        adapter_crash = MagicMock(spec=BasePlatformAdapter)
        adapter_crash.probe = AsyncMock(side_effect=ConnectionResetError("Socket reset by peer"))

        engine = ProbeEngine(adapters=[adapter_success, adapter_none, adapter_crash])
        results = await engine.run(self.seed)

        # Only the successful adapter's result should survive
        self.assertEqual(len(results), 1)
        profile, snapshot = results[0]
        self.assertEqual(profile.username, "alice")
        self.assertEqual(snapshot.sha_256, "a" * 64)


if __name__ == "__main__":
    unittest.main()
