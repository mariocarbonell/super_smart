from marshmallow import fields

from src.bdai.domain.model.Brand import Brand
from src.bdai.domain.model.Category import Category
from src.bdai.domain.model.Image import Image
from src.bdai.domain.model.NutritionalData import NutritionalData
from src.bdai.domain.model.Price import Price

from dataclasses import dataclass, field
from datetime import datetime

from dataclasses_json import dataclass_json, config


@dataclass_json
@dataclass(init=True)
class Product:
    id: str = ''
    origin: str = ''
    version: str = ''
    version_date: str = ''
    scrape_datetime: datetime = field(default_factory=datetime.now,
                                      metadata=config(field_name='scrape_datetime', encoder=datetime.isoformat,
                                                      decoder=datetime.fromisoformat,
                                                      mm_field=fields.DateTime(format='iso')))
    name: str = ''
    url: str = ''
    description: str = ''
    brand: Brand = field(default_factory=Brand)
    nutritional_data: NutritionalData = field(default_factory=NutritionalData)
    unit_format: str = field(default='')
    unit_size: str = 0
    ref_unit_format: str = field(default='')
    ref_unit_size: str = 0
    prices: list[Price] = field(default_factory=list)
    images: list[Image] = field(default_factory=list)
    ean: str = field(default='')
    categories: list[Category] = field(default_factory=list)
    extra_data: dict = field(default_factory=dict)

    def add_extra(self, values: dict) -> None:
        if not self.extra_data:
            self.extra_data = {}
        self.extra_data = {**self.extra_data, **values}

    def copy(self):
        newone = type(self)()
        newone.__dict__.update(self.__dict__)
        newone.prices = []
        # newone.scrape_datetime = datetime.now() # se establece en el callback
        return newone
