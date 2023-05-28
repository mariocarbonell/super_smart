from dataclasses import dataclass, field
from dataclasses_json import dataclass_json

from src.bdai.domain.model.NutritionalValue import NutritionalValue


@dataclass_json
@dataclass(init=True)
class NutritionalDefinition:
    quantity: str
    values: list[NutritionalValue]
