from pydantic import BaseModel, model_validator
from theia.core.schemas.platform_type import PlatformType
from theia.core.utils.handlers import handle_empty_sha
from datetime import datetime

class RawSnapshot(BaseModel):
    raw:bytes
    url:str
    platform:PlatformType
    sha_256:str = ""

    @model_validator(mode="after")
    def handle_empty_sha(self):
        self.sha_256 = handle_empty_sha(self.sha_256, self.raw)
        return self

class CandidateProfile(BaseModel):
    id:str
    platform:PlatformType
    username:str
    profile_url:str
    avatar_url:str | None = None
    bio_raw:str | None = None
    location_raw:str | None = None
    observed_timestamps:dict[datetime, str | None ] | None = None # optional activity log
    raw_snapshot_hash:str