from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config


@dataclass_json
@dataclass(init=True)
class Category:
    name: str = ''
    id: str = ''
    url: str = ''
    type: int = 0

    description: str = ''
