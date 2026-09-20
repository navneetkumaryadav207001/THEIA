from theia.core.schemas.seed_type import SeedType

# REGEXES
SEEDTYPEREGEX = {
    SeedType.EMAIL : r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    SeedType.USERNAME : r"^[a-zA-Z0-9_-]{3,16}$",
    SeedType.PHONE : r"^\+?[1-9][0-9\s\-().]{5,18}[0-9]$",
    SeedType.IMAGE_HASH : r"^[A-Fa-f0-9]{64}$"
}