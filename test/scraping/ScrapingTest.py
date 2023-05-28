import unittest

from src.bdai.domain.model.Product import Product


class ScrapingTest(unittest.TestCase):
    # def test_scrape(self):
    #     scraping_service: ScrapingService = ScrapingService()
    #     scraping_service.scrape(None, None)

    def test_product(self) :
        product: Product = Product()
        product.add_extra({'a':2})
        print(product.to_json())

if __name__ == '__main__':
    unittest.main()
