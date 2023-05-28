from dataclasses import dataclass, field
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Price:
    type: str = 'PRICE'
    unit_value: str = ''
    ref_unit_value: str = ''
