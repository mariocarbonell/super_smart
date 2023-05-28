import json
import time

import requests
from selenium.webdriver.common.by import By
from undetected_chromedriver import Chrome

from src.bdai.domain.model.Brand import Brand
from src.bdai.domain.model.Category import Category
from src.bdai.domain.model.Image import Image
from src.bdai.domain.model.NutritionalData import NutritionalData
from src.bdai.domain.model.NutritionalDefinition import NutritionalDefinition
from src.bdai.domain.model.NutritionalValue import NutritionalValue
from src.bdai.domain.model.Price import Price
from src.bdai.domain.model.Product import Product
from src.bdai.domain.model.ScrapingError import ScrapingError
from src.bdai.infrastructure.scraping.ScrapingInterface import ScrapingInterface
from src.bdai.infrastructure.scraping.ScrapingUtils import request_json, normalize_text, get_driver
from src.bdai.infrastructure.storage.LoggingService import log_info, log_error, log_trace


class ScrapingServiceMasymas(ScrapingInterface):

    def get_origin(self) -> str:
        return 'masymas'

    def __init__(self):
        self.driver: Chrome = get_driver()
        self.on_product_callback = lambda p: print(p.to_json())
        self.on_error_callback = lambda p: print(p.to_json())

    def scrape(self, on_product_callback, on_error_callback, find_product) -> None:
        print('masymas - begin')
        p = Product()
        p.id = 'm1'
        p.name = 'producto masymas 1'
        p.origin = 'masymas'
        p.version = '2023050701'
        on_product_callback(p)
        p = Product()
        p.id = 'm1'
        p.name = 'producto masymas 1'
        p.origin = 'masymas'
        p.version = '2023050701'
        on_product_callback(p)
        p = Product()
        p.id = 'm1'
        p.name = 'producto masymas 1'
        p.origin = 'masymas'
        p.version = '2023050701'
        error = ScrapingError()
        error.product = p
        error.key = 'prueba'
        on_error_callback(p)
        print('masymas - end')

    def __scrape(self, on_product_callback, on_error_callback, find_product, is_saved) -> None:
        log_info('scrape begin')

        self.on_product_callback = on_product_callback
        self.on_error_callback = on_error_callback
        self.find_product = find_product

        menu_url = 'https://tienda.masymas.com/api/rest/V1.0/shopping/category/menu'
        menu_structure = request_json(menu_url)

        for m1 in menu_structure:
            if not m1['id'] in [64, 65, 61, 62]:
                continue
            cat_1 = self.parse_category(m1)
            for m2 in m1['subcategories']:
                cat_2 = self.parse_category(m2)
                for m3 in m2['subcategories']:
                    cat_3 = self.parse_category(m3)
                    for m4 in m3['subcategories']:
                        cat_4 = self.parse_category(m4)

                        if m4['subcategories']:
                            error = ScrapingError(key='more_menu_levels', extra_data=m4)
                            self.on_error_callback(error)

                        product_list = self.scrape_products_list(cat_4)
                        for p in product_list:
                            if is_saved(p['id']):
                                continue
                            product = self.scrape_product([cat_1, cat_2, cat_3, cat_4], p)
                            self.on_product_callback(product)
        self.driver.close()
        self.driver.quit()
        log_info('scrape end')

    def scrape_product(self, categories: list[Category], p) -> Product:
        product: Product = Product()
        product.categories = categories
        product.id = p['id']
        extra = {'code': p['code']}
        product.extra_data = extra
        product.name = p['productData']['name']
        product.description = p['productData']['description']
        product.ean = p['ean']
        product.url = p['productData']['url']
        product.brand = Brand(id=p['productData']['brand']['id'],
                              name=p['productData']['brand']['name'])
        product.ref_unit_format = p['priceData']['unitPriceUnitType']
        product.unit_format = p['priceData']['priceUnitType']
        images: list[Image] = []
        for img in p['media']:
            images.append(Image(url=img['url'].replace('135x135', '1600x1600')))
        product.images = images
        prices: list[Price] = []
        for price in p['priceData']['prices']:
            prices.append(Price(type=price['id'], unit_value=str(price['value']['centAmount']),
                                ref_unit_value=str(price['value']['centUnitAmount'])))
        product.prices = prices

        stored_product = self.find_product(id=product.id)
        if stored_product and stored_product.nutritional_data and stored_product.nutritional_data.nutritional_definitions and stored_product.brand:
            log_trace(f'saved product: {product.id}')
            product.nutritional_data = stored_product.nutritional_data
            product.brand = stored_product.brand
            product.unit_size = stored_product.unit_size
            product.unit_format = stored_product.unit_format
        else:
            self.scrape_driver_data(product=product)
            log_trace(f'new product: {product.id}')

        return product

    def scrape_driver_data(self, product: Product) -> None:
        try:
            self.driver.get(product.url)
        except Exception:
            log_error()
            return
        time.sleep(3)

        product.nutritional_data = NutritionalData()
        info_table = self.driver.find_elements(By.XPATH, '(//cmp-nutritional-info-aecoc)[1]/div[@class="aecoc"]')
        if info_table:
            info_elements = info_table[0].find_elements(By.XPATH, './/div[@class="ng-star-inserted"]//h6')
            if info_elements:
                for element in info_elements:
                    title = element.text.strip()
                    norm_title = normalize_text(title)
                    value_element = element.find_element(By.XPATH, './/following-sibling::p')
                    value = value_element.text.strip()
                    if norm_title == 'denominacion':
                        product.nutritional_data.description = value
                    elif norm_title == 'ingredientes':
                        product.nutritional_data.ingredients = value
                    elif norm_title == 'cantidad neta':
                        try:
                            unit_size, unit_format = value.split(' ')
                            product.unit_size = unit_size
                            product.unit_format = unit_format
                        except Exception as e:
                            error = ScrapingError(product=product, key='unit_quantity_split_error', exception=str(e),
                                                  extra_data={'value': value})
                            self.on_error_callback(error)
                    elif norm_title == 'empresa':
                        product.brand.factory = value
                    elif norm_title == 'condiciones de conservacion y/o uso':
                        product.nutritional_data.conservation = value
                    else:
                        if norm_title not in ['ean']:
                            error = ScrapingError(product=product, key='unknown_nutritional_info',
                                                  extra_data={
                                                      'title': str(element.get_attribute('innerHTML')).strip(),
                                                      'value': str(value_element.get_attribute('innerHTML')).strip()})
                            self.on_error_callback(error)
            else:
                error = ScrapingError(product=product, key='no_info_elements')
                self.on_error_callback(error)

            nutrient_table = info_table[0].find_elements(By.XPATH, './/table')
            if nutrient_table:
                nutrient_head = nutrient_table[0].find_elements(By.XPATH, './/thead//th')
                if len(nutrient_head) > 2:
                    error = ScrapingError(product=product, key='multiple_quantities',
                                          extra_data={
                                              'source': str(nutrient_table[0].get_attribute('innerHTML')).strip()})
                    self.on_error_callback(error)
                quantity = nutrient_head[1].text.strip()
                nutritional_definition = NutritionalDefinition(quantity=quantity, values=[])
                nutrient_elements = nutrient_table[0].find_elements(By.XPATH, './/tbody//tr')
                if nutrient_elements:
                    for element in nutrient_elements:
                        td_elements = element.find_elements(By.XPATH, './/td')
                        if td_elements:
                            title = td_elements[0].text.strip()
                            value = td_elements[1].text.strip()
                            nutritional_definition.values.append(NutritionalValue(title=title, value=value))
                    product.nutritional_data.nutritional_definitions.append(nutritional_definition)
                else:
                    error = ScrapingError(product=product, key='no_nutrient_elements')
                    self.on_error_callback(error)
            else:
                error = ScrapingError(product=product, key='no_nutrient_table')
                self.on_error_callback(error)
        else:
            error = ScrapingError(product=product, key='no_info_elements')
            self.on_error_callback(error)

    def parse_category(self, menu) -> Category:
        cat: Category = Category()
        cat.id = menu['id']
        cat.name = menu['nombre']
        cat.url = menu['url']
        cat.description = menu['description']
        cat.type = menu['type']
        return cat

    def scrape_products_list(self, category: Category):
        try :
            text_json = requests.get(
                'https://tienda.masymas.com/api/rest/V1.0/catalog/product?limit=500&offset=0&orderById=5&showRecommendations=false&categories=' + str(
                    category.id),
                headers={
                    'Accep': 'application/json, text/plain, */*',
                    'Accept-Language': 'es-ES,es;q=0.9',
                    'Connection': 'keep-alive',
                    'Cookie': '_gcl_au=1.1.1736942417.1680461823; _ga=GA1.1.2141429782.1680461823; _fbp=fb.1.1680461822870.877063963; _hjSessionUser_3231790=eyJpZCI6ImU4ZWVhN2YwLWI4NzAtNTg4NC1iMzliLWY4ZDdiZGM4YmUzYyIsImNyZWF0ZWQiOjE2ODA0NjE4MjI5NzgsImV4aXN0aW5nIjp0cnVlfQ==; _hjAbsoluteSessionInProgress=1; _ga_1LYLPD1RX2=GS1.1.1680465842.2.1.1680466274.0.0.0; _ga_JY9BNB8V21=GS1.1.1680465841.2.1.1680466274.57.0.0',
                    'Referer': 'https://tienda.masymas.com/es/c/aceite-de-girasol/' + str(category.id),
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
                    'X-TOL-CHANNEL': '1',
                    'X-TOL-LOCALE': 'es',
                    'X-TOL-ZONE': '190',
                    'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"'
                }
            ).text
        
            return json.loads(text_json)['products']
        except Exception as e:
            print(e)
            error = ScrapingError(key='error_products_list', exception=str(e), extra_data={'text': text_json})
            self.on_error_callback(error)
        return []
