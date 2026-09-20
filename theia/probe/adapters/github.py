from theia.probe.adapters.base import BasePlatformAdapter
from theia.core.networking.rate_limiter import RateLimiter
from theia.core.schemas.platform_type import PlatformType
from theia.core.schemas.seed import InvestigationSeed
from theia.core.schemas.seed_type import SeedType
from theia.core.schemas.profile import CandidateProfile, RawSnapshot
import httpx


class GithubAdapter(BasePlatformAdapter):
    def __init__(self, client: httpx.AsyncClient, rate_limiter: RateLimiter):
        super().__init__(client,rate_limiter,PlatformType.Github)
    async def probe(self, seed:InvestigationSeed)-> tuple[CandidateProfile, RawSnapshot] | None:

        if seed.seed_type != SeedType.USERNAME: 
            return None
        await self.rate_limiter.acquire()
        url = f"https://api.github.com/users/{seed.value}"
        response = await self.client.get(
            url = url, 
            headers={
                "User-Agent": "THEIA-OSINT-Engine/1.0",
                "Accept": "application/vnd.github.v3+json"
            }
        )

        if response.status_code == 404:
            return None
        if response.status_code == 200:
            raw = response.content
            json = response.json()
            snapshot = RawSnapshot(raw=raw, url = url, platform=self.platform_type)
            profile = CandidateProfile(
                id = f"cand_github_{seed.value}",
                username = json.get("login", seed.value),
                profile_url = json.get("html_url"),
                avatar_url = json.get("avatar_url"),
                bio_raw = json.get("bio"),
                platform = self.platform_type,
                location_raw = json.get("location"),
                raw_snapshot_hash = snapshot.sha_256,
            )
            return profile,snapshot
