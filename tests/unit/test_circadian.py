import math
import unittest
from theia.extractor.circadian import calculate_circular_mean


class TestCircadianCircularMean(unittest.TestCase):
    def test_single_timestamp(self):
        """Single timestamp at 14.5 should yield 14.5 with R = 1.0 (perfect concentration)."""
        mean_hour, r_val = calculate_circular_mean([14.5])
        self.assertAlmostEqual(mean_hour, 14.5, places=5)
        self.assertAlmostEqual(r_val, 1.0, places=5)

    def test_midnight_boundary_wrap(self):
        """
        The classic directional statistics test:
        Events at 23.5h (11:30 PM) and 0.5h (00:30 AM).
        Linear mean = 12.0 (Noon - completely wrong!).
        Circular mean = 0.0 (Midnight - correct!).
        """
        mean_hour, r_val = calculate_circular_mean([23.5, 0.5])
        # Either ~0.0 or ~24.0 represents midnight
        self.assertTrue(math.isclose(mean_hour, 0.0, abs_tol=1e-4) or math.isclose(mean_hour, 24.0, abs_tol=1e-4))
        self.assertGreater(r_val, 0.9)  # High concentration close to 1.0

    def test_uniform_distribution_dispersion(self):
        """
        Timestamps evenly spaced around the clock (0, 6, 12, 18).
        Resultant vector R should be 0.0 (completely dispersed, no preferred time).
        """
        mean_hour, r_val = calculate_circular_mean([0.0, 6.0, 12.0, 18.0])
        self.assertAlmostEqual(r_val, 0.0, places=5)

    def test_consistent_cluster(self):
        """A cluster of events around 9:00 AM (e.g. 8.5, 9.0, 9.5)."""
        mean_hour, r_val = calculate_circular_mean([8.5, 9.0, 9.5])
        self.assertAlmostEqual(mean_hour, 9.0, places=4)
        self.assertGreater(r_val, 0.95)

    def test_empty_list_fallback(self):
        """Empty list should safely return (0.0, 0.0) without raising ZeroDivisionError."""
        mean_hour, r_val = calculate_circular_mean([])
        self.assertEqual(mean_hour, 0.0)
        self.assertEqual(r_val, 0.0)

