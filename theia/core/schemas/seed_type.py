from enum import Enum

class SeedType(str, Enum):
    USERNAME="username"
    EMAIL="email"
    PHONE="phone"
    IMAGE_HASH="image_hash"