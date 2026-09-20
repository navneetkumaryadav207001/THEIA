from abc import ABC, abstractmethod
import httpx
from theia.core.networking.rate_limiter import RateLimiter
from theia.core.schemas.seed import InvestigationSeed
from theia.core.schemas.profile import CandidateProfile, RawSnapshot
from theia.core.schemas.platform_type import PlatformType

class BasePlatformAdapter(ABC):

    def __init__(self, client: httpx.AsyncClient, rate_limiter:RateLimiter, platform_type: PlatformType):
        self.client = client
        self.rate_limiter = rate_limiter
        self.platform_type = platform_type
    @abstractmethod
    async def probe(self, seed:InvestigationSeed)-> tuple[CandidateProfile, RawSnapshot] | None:
        pass