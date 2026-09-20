from datetime import datetime, timezone
import math
import unittest

from theia.core.schemas.platform_type import PlatformType
from theia.core.schemas.profile import CandidateProfile
from theia.extractor.circadian import CircadianExtractor


class TestCircadianCircularMean(unittest.TestCase):
    def test_single_timestamp(self):
        """Single timestamp at 14.5 should yield 14.5 with R = 1.0 (perfect concentration)."""
        mean_hour, r_val = CircadianExtractor.calculate_circular_mean([14.5])
        self.assertAlmostEqual(mean_hour, 14.5, places=5)
        self.assertAlmostEqual(r_val, 1.0, places=5)

    def test_midnight_boundary_wrap(self):
        """
        The classic directional statistics test:
        Events at 23.5h (11:30 PM) and 0.5h (00:30 AM).
        Linear mean = 12.0 (Noon - completely wrong!).
        Circular mean = 0.0 (Midnight - correct!).
        """
        mean_hour, r_val = CircadianExtractor.calculate_circular_mean([23.5, 0.5])
        # Either ~0.0 or ~24.0 represents midnight
        self.assertTrue(math.isclose(mean_hour, 0.0, abs_tol=1e-4) or math.isclose(mean_hour, 24.0, abs_tol=1e-4))
        self.assertGreater(r_val, 0.9)  # High concentration close to 1.0

    def test_uniform_distribution_dispersion(self):
        """
        Timestamps evenly spaced around the clock (0, 6, 12, 18).
        Resultant vector R should be 0.0 (completely dispersed, no preferred time).
        """
        mean_hour, r_val = CircadianExtractor.calculate_circular_mean([0.0, 6.0, 12.0, 18.0])
        self.assertAlmostEqual(r_val, 0.0, places=5)

    def test_consistent_cluster(self):
        """A cluster of events around 9:00 AM (e.g. 8.5, 9.0, 9.5)."""
        mean_hour, r_val = CircadianExtractor.calculate_circular_mean([8.5, 9.0, 9.5])
        self.assertAlmostEqual(mean_hour, 9.0, places=4)
        self.assertGreater(r_val, 0.95)

    def test_empty_list_fallback(self):
        """Empty list should safely return (0.0, 0.0) without raising ZeroDivisionError."""
        mean_hour, r_val = CircadianExtractor.calculate_circular_mean([])
        self.assertEqual(mean_hour, 0.0)
        self.assertEqual(r_val, 0.0)


class TestCircadianExtractor(unittest.TestCase):
    def _create_mock_profile(self, timestamps: list[datetime]) -> CandidateProfile:
        ts_dict = {ts: "event" for ts in timestamps}
        return CandidateProfile(
            id="test-123",
            platform=PlatformType.Github,
            username="testuser",
            profile_url="https://github.com/testuser",
            observed_timestamps=ts_dict,
            raw_snapshot_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )

    def test_insufficient_timestamps_returns_none(self):
        """Less than 3 timestamps should return None due to sample scarcity."""
        profile_empty = self._create_mock_profile([])
        profile_two = self._create_mock_profile([
            datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
            datetime(2026, 1, 2, 11, 0, tzinfo=timezone.utc),
        ])
        self.assertIsNone(CircadianExtractor.extract(profile_empty))
        self.assertIsNone(CircadianExtractor.extract(profile_two))

    def test_utc_developer_sleep_and_timezone(self):
        """
        Simulate an active London/UTC developer:
        Active from 09:00 to 22:00 UTC (zero activity from 00:00 to 07:00 UTC).
        Expected:
        - Sleep window: 0.0 to 7.0 UTC
        - Inferred timezone: UTC+0
        """
        timestamps = []
        # Populate activity across multiple days during daytime (09:00 - 22:00)
        for day in range(1, 10):
            for hour in range(9, 22):
                timestamps.append(datetime(2026, 1, day, hour, 15, tzinfo=timezone.utc))

        profile = self._create_mock_profile(timestamps)
        signal = CircadianExtractor.extract(profile)

        self.assertIsNotNone(signal)
        self.assertEqual(signal.data_points_count, len(timestamps))
        self.assertEqual(signal.sleep_window_start_utc, 0.0)
        self.assertEqual(signal.sleep_window_end_utc, 7.0)
        self.assertEqual(signal.inferred_timezone, "UTC+0")
        self.assertGreater(signal.confidence, 0.5)

    def test_tokyo_developer_timezone(self):
        """
        Simulate a Tokyo (UTC+9) developer:
        Local sleep 00:00 to 07:00 JST -> In UTC this corresponds to 15:00 to 22:00 UTC.
        Active during local daytime (07:00 to 24:00 JST -> 22:00 to 15:00 UTC).
        Expected:
        - Sleep window: 15.0 to 22.0 UTC
        - Inferred timezone: UTC+9
        """
        timestamps = []
        for day in range(1, 10):
            # Active from 22:00 UTC to 14:00 UTC next day (07:00 to 23:00 JST)
            for hour in list(range(0, 15)) + [22, 23]:
                timestamps.append(datetime(2026, 1, day, hour, 30, tzinfo=timezone.utc))

        profile = self._create_mock_profile(timestamps)
        signal = CircadianExtractor.extract(profile)

        self.assertIsNotNone(signal)
        self.assertEqual(signal.sleep_window_start_utc, 15.0)
        self.assertEqual(signal.sleep_window_end_utc, 22.0)
        self.assertEqual(signal.inferred_timezone, "UTC+9")

    def test_bhattacharyya_coefficient(self):
        """
        Verify distribution overlap:
        - Identical distributions must yield BC = 1.0
        - Completely disjoint distributions must yield BC = 0.0
        """
        p = [1.0 / 24.0] * 24
        q = [1.0 / 24.0] * 24
        self.assertAlmostEqual(CircadianExtractor.calculate_bhattacharyya_coefficient(p, q), 1.0, places=5)

        # Disjoint: P active only in first 12 hours, Q active only in last 12 hours
        p_disjoint = [1.0 / 12.0 if i < 12 else 0.0 for i in range(24)]
        q_disjoint = [1.0 / 12.0 if i >= 12 else 0.0 for i in range(24)]
        self.assertAlmostEqual(CircadianExtractor.calculate_bhattacharyya_coefficient(p_disjoint, q_disjoint), 0.0, places=5)
