from dataclasses import dataclass, field
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Brand:
    id: str = ''
    name: str = ''
    factory: str = ''
    factory_extra: list[str] = field(default_factory=list)

    def add_factory_extra(self,text) -> None :
        if not self.factory_extra :
            self.factory_extra = []
        self.factory_extra.append(text)

