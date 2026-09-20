from theia.probe.adapters.base import BasePlatformAdapter
from theia.core.networking.rate_limiter import RateLimiter
from theia.core.schemas.platform_type import PlatformType
from theia.core.schemas.seed import InvestigationSeed
from theia.core.schemas.seed_type import SeedType
from theia.core.schemas.profile import CandidateProfile, RawSnapshot
import httpx


class RedditAdapter(BasePlatformAdapter):
    def __init__(self, client: httpx.AsyncClient, rate_limiter: RateLimiter):
        super().__init__(client,rate_limiter,PlatformType.REDDIT)
    async def probe(self, seed:InvestigationSeed)-> tuple[CandidateProfile, RawSnapshot] | None:

        if seed.seed_type != SeedType.USERNAME: 
            return None
        await self.rate_limiter.acquire()
        url = f"https://www.reddit.com/user/{seed.value}/about.json"
        response = await self.client.get(
            url=url, 
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            }
        )

        if response.status_code != 200:
            return None

        raw = response.content
        try:
            payload = response.json()
        except Exception:
            return None

        data = payload.get("data")
        if not data or data.get("is_suspended"):
            return None

        snapshot = RawSnapshot(raw=raw, url=url, platform=self.platform_type)

        subreddit = data.get("subreddit") or {}
        bio = subreddit.get("public_description") or None
        avatar = data.get("icon_img") or None

        profile = CandidateProfile(
            id=f"cand_reddit_{seed.value}",
            username=data.get("name", seed.value),
            profile_url=f"https://www.reddit.com/user/{seed.value}",
            avatar_url=avatar,
            bio_raw=bio,
            platform=self.platform_type,
            location_raw=None,
            raw_snapshot_hash=snapshot.sha_256,
        )
        return profile, snapshot
