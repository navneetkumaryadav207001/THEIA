from datetime import datetime, timezone
import unittest
from pydantic import ValidationError
from theia.core.schemas.seed import InvestigationSeed
from theia.core.schemas.seed_type import SeedType


class TestSeedType(unittest.TestCase):
    def test_seed_type_values(self):
        self.assertEqual(SeedType.USERNAME.value, "username")
        self.assertEqual(SeedType.EMAIL.value, "email")
        self.assertEqual(SeedType.PHONE.value, "phone")
        self.assertEqual(SeedType.IMAGE_HASH.value, "image_hash")


class TestInvestigationSeedUsername(unittest.TestCase):
    def test_valid_usernames(self):
        valid_usernames = [
            "alex",
            "x_v01d",
            "neo-99",
            "neo_matrix",
            "usr123",
            "a_b-c",
            "maxlengthuser123"  # 16 chars
        ]
        for username in valid_usernames:
            with self.subTest(username=username):
                seed = InvestigationSeed(
                    id=1,
                    seed_type=SeedType.USERNAME,
                    value=username,
                    created_at=datetime.now(timezone.utc)
                )
                self.assertEqual(seed.value, username)
                self.assertEqual(seed.seed_type, SeedType.USERNAME)

    def test_invalid_usernames(self):
        invalid_usernames = [
            "al",                                      # Too short (< 3)
            "this_username_is_way_too_long_for_regex", # Too long (> 16)
            "alex smith",                              # Contains spaces
            "alex@matrix",                             # Invalid symbol @
            "user.name",                               # Dot not in username regex
            "user!#$",                                 # Special characters
            ""                                         # Empty
        ]
        for username in invalid_usernames:
            with self.subTest(username=username):
                with self.assertRaises(ValidationError):
                    InvestigationSeed(
                        id=1,
                        seed_type=SeedType.USERNAME,
                        value=username,
                        created_at=datetime.now(timezone.utc)
                    )


class TestInvestigationSeedEmail(unittest.TestCase):
    def test_valid_emails(self):
        valid_emails = [
            "target@example.com",
            "first.last@domain.co.uk",
            "user+tag@sub.domain.org",
            "investigator_01@sec-corp.io"
        ]
        for email in valid_emails:
            with self.subTest(email=email):
                seed = InvestigationSeed(
                    id=2,
                    seed_type=SeedType.EMAIL,
                    value=email,
                    created_at=datetime.now(timezone.utc)
                )
                self.assertEqual(seed.value, email)

    def test_invalid_emails(self):
        invalid_emails = [
            "not-an-email",
            "user@",
            "@domain.com",
            "user@domain",          # Missing TLD
            "user name@domain.com", # Contains space
            "user@.com"
        ]
        for email in invalid_emails:
            with self.subTest(email=email):
                with self.assertRaises(ValidationError):
                    InvestigationSeed(
                        id=2,
                        seed_type=SeedType.EMAIL,
                        value=email,
                        created_at=datetime.now(timezone.utc)
                    )


class TestInvestigationSeedPhone(unittest.TestCase):
    def test_valid_phones(self):
        valid_phones = [
            "+14155552671",
            "+447911123456",
            "+1-800-555-0199",
            "+1 (800) 555-0199",
            "4155552671"
        ]
        for phone in valid_phones:
            with self.subTest(phone=phone):
                seed = InvestigationSeed(
                    id=3,
                    seed_type=SeedType.PHONE,
                    value=phone,
                    created_at=datetime.now(timezone.utc)
                )
                self.assertEqual(seed.value, phone)

    def test_invalid_phones(self):
        invalid_phones = [
            "123",                                  # Too short
            "phone-number-abc",                     # Letters
            "+000000000000000000000000000000000",   # Too long
            ""
        ]
        for phone in invalid_phones:
            with self.subTest(phone=phone):
                with self.assertRaises(ValidationError):
                    InvestigationSeed(
                        id=3,
                        seed_type=SeedType.PHONE,
                        value=phone,
                        created_at=datetime.now(timezone.utc)
                    )


class TestInvestigationSeedImageHash(unittest.TestCase):
    def test_valid_hashes(self):
        valid_hashes = [
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
            "a" * 64,
            "0123456789abcdef0123456789ABCDEF0123456789abcdef0123456789ABCDEF"
        ]
        for h in valid_hashes:
            with self.subTest(h=h):
                seed = InvestigationSeed(
                    id=4,
                    seed_type=SeedType.IMAGE_HASH,
                    value=h,
                    created_at=datetime.now(timezone.utc)
                )
                self.assertEqual(seed.value, h)

    def test_invalid_hashes(self):
        invalid_hashes = [
            "e3b0c442",                                 # Too short (8 chars)
            "a" * 63,                                   # 63 chars (off by 1)
            "a" * 65,                                   # 65 chars (off by 1)
            "z" * 64,                                   # Non-hex characters
            "not_a_valid_sha256_hash_at_all_1234567890" # Invalid
        ]
        for h in invalid_hashes:
            with self.subTest(h=h):
                with self.assertRaises(ValidationError):
                    InvestigationSeed(
                        id=4,
                        seed_type=SeedType.IMAGE_HASH,
                        value=h,
                        created_at=datetime.now(timezone.utc)
                    )


class TestInvestigationSeedSerialization(unittest.TestCase):
    def test_json_roundtrip(self):
        original = InvestigationSeed(
            id=10,
            seed_type=SeedType.USERNAME,
            value="x_v01d",
            created_at=datetime.now(timezone.utc)
        )
        json_str = original.model_dump_json()
        restored = InvestigationSeed.model_validate_json(json_str)
        self.assertEqual(restored.id, original.id)
        self.assertEqual(restored.seed_type, original.seed_type)
        self.assertEqual(restored.value, original.value)


if __name__ == "__main__":
    unittest.main()
