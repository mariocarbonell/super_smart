from dataclasses import dataclass, field
from dataclasses_json import dataclass_json

from src.bdai.domain.model.NutritionalDefinition import NutritionalDefinition


@dataclass_json
@dataclass(init=True)
class NutritionalData:
    description: str = ''
    ingredients: str = ''
    conservation: str = ''
    use: str = ''
    allergens: str = ''
    nutritional_definitions: list[NutritionalDefinition] = field(default_factory=list)
    extra: dict = field(default_factory=dict)

    def add_extra(self, values: dict) -> None:
        if not self.extra:
            self.extra = {}
        self.extra = {**self.extra, **values}
