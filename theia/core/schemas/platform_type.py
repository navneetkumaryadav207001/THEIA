from enum import Enum

class PlatformType(str,Enum):
    FaceBook = "facebook"
    Instagram = "instagram"
    Github = "github"
    REDDIT = "reddit"
    MASTODON = "mastodon"
    KEYBASE = "keybase"
    HACKERNEWS = "hackernews"
    DEVTO = "devto"
    GITLAB = "gitlab"