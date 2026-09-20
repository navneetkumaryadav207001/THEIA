from datetime import datetime, timezone
import numpy as np

from theia.core.schemas.profile import CandidateProfile
from theia.core.schemas.signals import CircadianSignal


class CircadianExtractor:

    @staticmethod
    def calculate_circular_mean(utc_hours: list[float]) -> tuple[float, float]:
        """Returns (mean_hour_utc, R_bar_concentration) using directional statistics."""
        if len(utc_hours) == 0:
            return (0.0, 0.0)
        two_pi = 2 * np.pi
        hours_array = np.array(utc_hours)
        theta_array = two_pi * hours_array / 24
        x_array = np.cos(theta_array)
        y_array = np.sin(theta_array)
        c_bar = np.mean(x_array)
        s_bar = np.mean(y_array)
        theta = np.arctan2(s_bar, c_bar) % two_pi
        circular_mean = theta * 24 / two_pi
        R = np.sqrt(c_bar**2 + s_bar**2)

        return float(circular_mean), float(R)

    @staticmethod
    def calculate_bhattacharyya_coefficient(dist_p: list[float], dist_q: list[float]) -> float:
        """
        Computes the Bhattacharyya Coefficient BC(P, Q) = sum(sqrt(P_k * Q_k)) in [0, 1].
        Measures the statistical overlap between two 24-bin circadian distributions.
        - BC > 0.85: Strong temporal alignment.
        - BC < 0.30: Strong temporal divergence (probable distinct actors).
        """
        p = np.array(dist_p)
        q = np.array(dist_q)
        return float(np.sum(np.sqrt(p * q)))

    @staticmethod
    def extract(profile: CandidateProfile, k_half: float = 15.0) -> CircadianSignal | None:
        """
        Extracts chronolocation and circadian rhythm signals from a CandidateProfile.
        Returns None if timestamps are missing or insufficient (N < 3).
        """
        if not profile.observed_timestamps or len(profile.observed_timestamps) < 3:
            return None

        timestamps = list(profile.observed_timestamps.keys())
        n_points = len(timestamps)

        utc_hours: list[float] = []
        histogram = [0.0] * 24

        for dt in timestamps:
            if dt.tzinfo is not None:
                dt_utc = dt.astimezone(timezone.utc)
            else:
                dt_utc = dt
            h_frac = dt_utc.hour + (dt_utc.minute / 60.0) + (dt_utc.second / 3600.0)
            utc_hours.append(h_frac)
            histogram[dt_utc.hour] += 1.0

        circular_mean_hour, r_val = CircadianExtractor.calculate_circular_mean(utc_hours)

        # Normalized 24-bin PMF distribution
        hourly_distribution = [count / n_points for count in histogram]

        # 7-hour sliding sleep window using doubled array trick (O(24))
        h_doubled = hourly_distribution + hourly_distribution
        current_sum = sum(h_doubled[0:7])
        min_activity = current_sum
        sleep_start = 0

        for k in range(1, 24):
            current_sum = current_sum - h_doubled[k - 1] + h_doubled[k + 6]
            if current_sum < min_activity:
                min_activity = current_sum
                sleep_start = k

        sleep_start_utc = float(sleep_start)
        sleep_end_utc = float((sleep_start + 7) % 24)
        sleep_midpoint_utc = (sleep_start + 3.5) % 24.0

        # Biological sleep center is roughly 03:30 local time
        offset = round(3.5 - sleep_midpoint_utc)
        if offset > 12:
            offset -= 24
        elif offset < -12:
            offset += 24

        tz_str = f"UTC{'+' if offset >= 0 else ''}{offset}"

        # Michaelis-Menten / Hill saturation curve for confidence
        confidence = round(float(r_val * (n_points / (n_points + k_half))), 4)

        return CircadianSignal(
            data_points_count=n_points,
            hourly_distribution=hourly_distribution,
            circular_mean_hour_utc=round(float(circular_mean_hour), 2),
            inferred_timezone=tz_str,
            sleep_window_start_utc=sleep_start_utc,
            sleep_window_end_utc=sleep_end_utc,
            confidence=confidence,
        )