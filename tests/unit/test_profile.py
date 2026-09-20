from datetime import datetime, timezone
import hashlib
import unittest
from theia.core.schemas.platform_type import PlatformType
from theia.core.schemas.profile import CandidateProfile, RawSnapshot


class TestPlatformType(unittest.TestCase):
    def test_platform_values(self):
        self.assertEqual(PlatformType.Github.value, "github")
        self.assertEqual(PlatformType.REDDIT.value, "reddit")
        self.assertEqual(PlatformType.MASTODON.value, "mastodon")
        self.assertEqual(PlatformType.KEYBASE.value, "keybase")
        self.assertEqual(PlatformType.HACKERNEWS.value, "hackernews")
        self.assertEqual(PlatformType.DEVTO.value, "devto")
        self.assertEqual(PlatformType.GITLAB.value, "gitlab")


class TestRawSnapshot(unittest.TestCase):
    def test_auto_hash_computation(self):
        raw_content = b"<html><head><title>Test User</title></head><body>Hello OSINT</body></html>"
        expected_sha = hashlib.sha256(raw_content).hexdigest()

        snapshot = RawSnapshot(
            raw=raw_content,
            url="https://github.com/alice",
            platform=PlatformType.Github
        )

        self.assertEqual(snapshot.sha_256, expected_sha)
        self.assertEqual(len(snapshot.sha_256), 64)

    def test_preserve_existing_hash(self):
        custom_hash = "f" * 64
        snapshot = RawSnapshot(
            raw=b"some bytes",
            url="https://reddit.com/user/bob",
            platform=PlatformType.REDDIT,
            sha_256=custom_hash
        )
        self.assertEqual(snapshot.sha_256, custom_hash)

    def test_empty_bytes_hash(self):
        empty_snapshot = RawSnapshot(
            raw=b"",
            url="https://mastodon.social/@carol",
            platform=PlatformType.MASTODON
        )
        empty_hash = hashlib.sha256(b"").hexdigest()
        self.assertEqual(empty_snapshot.sha_256, empty_hash)


class TestCandidateProfile(unittest.TestCase):
    def test_minimal_candidate_profile(self):
        snapshot = RawSnapshot(
            raw=b"minimal payload",
            url="https://github.com/x_v01d",
            platform=PlatformType.Github
        )

        profile = CandidateProfile(
            id="cand_gh_01",
            platform=PlatformType.Github,
            username="x_v01d",
            profile_url="https://github.com/x_v01d",
            raw_snapshot_hash=snapshot.sha_256
        )

        self.assertEqual(profile.id, "cand_gh_01")
        self.assertEqual(profile.platform, PlatformType.Github)
        self.assertEqual(profile.username, "x_v01d")
        self.assertEqual(profile.profile_url, "https://github.com/x_v01d")
        self.assertIsNone(profile.avatar_url)
        self.assertIsNone(profile.bio_raw)
        self.assertIsNone(profile.location_raw)
        self.assertIsNone(profile.observed_timestamps)
        self.assertEqual(profile.raw_snapshot_hash, snapshot.sha_256)

    def test_full_candidate_profile(self):
        now = datetime.now(timezone.utc)
        timestamps = {now: "commit: initial commit"}

        profile = CandidateProfile(
            id="cand_gh_02",
            platform=PlatformType.Github,
            username="alice_dev",
            profile_url="https://github.com/alice_dev",
            avatar_url="https://avatars.githubusercontent.com/u/123456",
            bio_raw="Distributed systems & cryptography engineer.",
            location_raw="Berlin, Germany",
            observed_timestamps=timestamps,
            raw_snapshot_hash="a" * 64
        )

        self.assertEqual(profile.username, "alice_dev")
        self.assertEqual(profile.avatar_url, "https://avatars.githubusercontent.com/u/123456")
        self.assertEqual(profile.bio_raw, "Distributed systems & cryptography engineer.")
        self.assertEqual(profile.location_raw, "Berlin, Germany")
        self.assertIn(now, profile.observed_timestamps)

    def test_json_roundtrip(self):
        profile = CandidateProfile(
            id="cand_reddit_01",
            platform=PlatformType.REDDIT,
            username="bob_sec",
            profile_url="https://reddit.com/user/bob_sec",
            avatar_url="https://reddit.com/avatar.png",
            bio_raw="Security researcher.",
            location_raw=None,
            raw_snapshot_hash="b" * 64
        )

        json_data = profile.model_dump_json()
        restored = CandidateProfile.model_validate_json(json_data)

        self.assertEqual(restored.id, profile.id)
        self.assertEqual(restored.platform, profile.platform)
        self.assertEqual(restored.username, profile.username)
        self.assertEqual(restored.bio_raw, profile.bio_raw)
        self.assertEqual(restored.raw_snapshot_hash, profile.raw_snapshot_hash)


if __name__ == "__main__":
    unittest.main()
