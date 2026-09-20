from pydantic import BaseModel,model_validator
from datetime import datetime
from theia.core.utils.validators import validate_seed
from theia.core.schemas.seed_type import SeedType
from typing import Self

class InvestigationSeed(BaseModel):
    id: int
    seed_type: SeedType
    value:str
    created_at:datetime

    @model_validator(mode="after")
    def validate_value(self) -> Self:
        validate_seed(self.value,self.seed_type)
        return self
        