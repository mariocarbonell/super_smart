from dataclasses import dataclass, field
from datetime import datetime

from dataclasses_json import dataclass_json, config
from marshmallow import fields


@dataclass_json
@dataclass
class Execution:
    id: str
    end_datetime: datetime = field(default_factory=datetime.now,
                                   metadata=config(field_name='end_datetime', encoder=datetime.isoformat,
                                                   decoder=datetime.fromisoformat,
                                                   mm_field=fields.DateTime(format='iso')))
    init_datetime: datetime = field(default_factory=datetime.now,
                                    metadata=config(field_name='init_datetime', encoder=datetime.isoformat,
                                                    decoder=datetime.fromisoformat,
                                                    mm_field=fields.DateTime(format='iso')))

    num_products: int = 0
    num_errors: int = 0

    status: int = 0
    error: int = 0

    def begin(self) -> None:
        self.init_datetime = datetime.now()
        self.status = 1

    def end(self) -> None:
        self.end_datetime = datetime.now()
        self.status = 0
