import re
from theia.core.schemas.seed_type import SeedType
from theia.core.utils.variables import SEEDTYPEREGEX


def validate_seed(value:str, seed_type:SeedType)-> None:
    if not re.match(SEEDTYPEREGEX[seed_type],value):
            raise ValueError("",value)


