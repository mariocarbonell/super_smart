from dataclasses import dataclass, field
from dataclasses_json import dataclass_json

from src.bdai.domain.model.Product import Product


@dataclass_json
@dataclass
class ScrapingError:
    key: str = field(init=True, default='')
    product: Product = field(init=True, default=None)
    extra_data: dict = field(init=True, default_factory=dict)
    exception: str = ''
