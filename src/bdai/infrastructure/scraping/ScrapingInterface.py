from abc import ABC, abstractmethod


class ScrapingInterface(ABC):

    @abstractmethod
    def get_origin(self) -> str:
        pass

    @abstractmethod
    def scrape(self, on_product_callback, on_error_callback, find_product, is_saved) -> None:
        pass
