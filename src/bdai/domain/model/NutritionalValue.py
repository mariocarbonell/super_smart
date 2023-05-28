from dataclasses import dataclass, field
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass(init=True)
class NutritionalValue:
    title: str
    value: str
