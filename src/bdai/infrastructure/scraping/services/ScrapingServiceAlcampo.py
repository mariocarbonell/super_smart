import time

from bs4 import BeautifulSoup
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
from src.bdai.infrastructure.scraping.ScrapingUtils import get_driver
from src.bdai.infrastructure.storage.LoggingService import log_info, log_error, log_trace


class ScrapingServiceAlcampo(ScrapingInterface):
    def get_origin(self) -> str:
        """
        Metodo que devuelve el identificador del origen de datos para que el resto de la
        aplicación identifique todos los datos generados por este servicio de scraping

        :return str:
        """
        return 'alcampo'

    def __init__(self):
        self.on_product_callback = lambda p: print(p.to_json())
        self.on_error_callback = lambda p: print(p.to_json())
        self.driver: Chrome = get_driver()

    def __scrape(self, on_product_callback, on_error_callback, find_product, is_saved) -> None:
        """
        Metodo que inicia la obtencion de datos del origen de datos.

        :param on_product_callback:
        :param on_error_callback:
        :param find_product:
        :param is_saved:
        """

        log_info('scrape begin')

        self.on_product_callback = on_product_callback
        self.on_error_callback = on_error_callback

        base_url = 'https://www.alcampo.es'
        menu_url = base_url + '/compra-online/view/NavigationBarComponentController?componentUid=alcampoNavigationBar&show=fullMenu'
        try:
            self.driver.get(menu_url)
        except Exception:
            try:
                self.driver = get_driver()
                time.sleep(3)
                self.driver.get(menu_url)
                time.sleep(3)
            except Exception:
                log_error()
        menu = BeautifulSoup(self.driver.page_source, features="lxml")
        menu_1_elements = menu.findAll('ul', {'class': 'LEVEL_0'})

        products: list[Product] = []

        for menu_0 in menu_1_elements:
            cat_0: Category = Category(id=menu_0['id'])
            for menu_1 in menu_0.findAll('li', recursive=False)[:4]:
                a_element = menu_1.find('a')
                cat_1: Category = Category(id=a_element['id'], name=a_element['title'], url=a_element['href'])
                menu_3_link_elements = menu_1.findAll('a', {'class': 'LEVEL_3'})
                for menu_3_link in menu_3_link_elements:
                    cat_2: Category = Category(id=menu_3_link['id'], name=menu_3_link['title'], url=menu_3_link['href'])
                    print(cat_2.name)
                    try:
                        self.driver.get(base_url + menu_3_link['href'])
                    except Exception:
                        try:
                            self.driver = get_driver()
                            time.sleep(3)
                            self.driver.get(base_url + menu_3_link['href'])
                            time.sleep(3)
                        except Exception:
                            log_error()
                            continue
                    time.sleep(6)

                    all_products = False
                    page = 1
                    while not all_products:
                        products_elements = self.driver.find_elements(By.XPATH,
                                                                      '//div[contains(@class,"productGridItem ")]//a[@class="productMainLink productTooltipClass"]')
                        for n, product_element in enumerate(products_elements):
                            product_id: str = product_element.get_attribute('data-id')
                            if is_saved(id=product_id):
                                log_trace(f'is saved: {product_id}')
                                continue
                            saved_product: Product = find_product(id=product_id)
                            product_exists: bool = not not saved_product
                            if product_exists:
                                try:
                                    product: Product = saved_product.copy()
                                    parent_element = product_element.find_elements(By.XPATH,
                                                                                   './parent::h2/parent::div/parent::div[contains(@class,"productGridItem ")]')
                                    if not not parent_element:
                                        price_element = parent_element[0].find_elements(By.XPATH,
                                                                                        '//span[contains(@class,"long-price precio18")]')
                                        if not not price_element:
                                            price: Price = Price(type='PRICE')
                                            parts = price_element[0].text.replace(',', '.').split('\n')
                                            price.unit_value = parts[0].replace('€', '').strip()
                                            if len(parts) > 1:
                                                price.ref_unit_value = parts[1].split('/')[0].replace('€', '').replace(
                                                    '(', '').strip()
                                            product.prices = [price]
                                            self.on_product_callback(product)
                                            log_trace(f'saved product: {product.id}')
                                        else:
                                            product_exists = False
                                            error = ScrapingError(product=saved_product,
                                                                  key='no_saved_product_price_element')
                                            self.on_error_callback(error)
                                    else:
                                        product_exists = False
                                        error = ScrapingError(product=saved_product,
                                                              key='no_saved_product_parent_element')
                                        self.on_error_callback(error)
                                except Exception as e:
                                    product_exists = False
                                    error = ScrapingError(product=saved_product, key='no_saved_product_price')
                                    self.on_error_callback(error)
                                    log_error()

                            if not product_exists:
                                log_trace(f'new product: {product_id}')
                                product: Product = Product()
                                product.categories = [cat_0, cat_1, cat_2]
                                product.id = product_element.get_attribute('data-id')
                                product.name = product_element.get_attribute('title')
                                product.url = product_element.get_attribute('href')
                                product.brand = Brand()
                                product.nutritional_data = NutritionalData()
                                products.append(product)

                        next_button_elements = self.driver.find_elements(By.XPATH,
                                                                         '//div[@class="productGrid paginationBar bottom clearfix"]//li[@class="next"]/a')
                        if next_button_elements is not None and len(next_button_elements) > 0:
                            self.driver.execute_script("arguments[0].click();", next_button_elements[0])
                            time.sleep(6)
                            page += 1
                        else:
                            all_products = True
        self.scrape_products(products)
        log_info('scrape end 1')
        self.driver.close()
        self.driver.quit()
        log_info('scrape end 2')

    def scrape_products(self, products: list[Product]):
        """
        Metodo que obtiene el detalle de un producto y ejecuta el callback para que se almacene el producto

        :param products:
        """
        for product in products:
            try:
                self.driver.get(product.url)
            except:
                try:
                    self.driver = get_driver()
                    time.sleep(3)
                    self.driver.get(product.url)
                    time.sleep(3)
                except Exception:
                    log_error()
                    continue
            time.sleep(6)
            breadcrumb = self.driver.find_elements(By.XPATH, '//div[@id="breadcrumb"]/ul//li//a')
            if not not breadcrumb:
                product.add_extra({'breadcrumb': [item.text for item in breadcrumb]})
            else:
                error = ScrapingError(product=product, key='no_breadcrumb')
                self.on_error_callback(error)

            brand = self.driver.find_elements(By.XPATH, '//div[@class="productTitle"]')
            if not not brand:
                product.brand.name = brand[0].text
            else:
                error = ScrapingError(product=product, key='no_brand')
                self.on_error_callback(error)

            product_price_format = self.driver.find_elements(By.XPATH, '//div[@class="productUnitMeasure"]')
            if not not product_price_format:
                product.unit_format = product_price_format[0].text.strip()
            else:
                error = ScrapingError(product=product, key='no_unit_format')
                self.on_error_callback(error)

            price: Price = Price(type='PRICE')
            price_element = self.driver.find_elements(By.XPATH, '//span[contains(@class,"big-price")]')
            if not not price_element:
                price_text = price_element[0].text
                if '(' in price_text:
                    price_text = price_text.split('(')[0][:-2]
                price.unit_value = price_text.strip().replace(',', '.')
            else:
                error = ScrapingError(product=product, key='no_unit_price')
                self.on_error_callback(error)

            unit_price_element = self.driver.find_elements(By.XPATH, '//span[contains(@class,"precioUnidad")]')
            if not not unit_price_element:
                units_parts = unit_price_element[0].text.replace('(', '').replace(')', '').replace('€', '').split('/')
                price.ref_unit_value = units_parts[0].strip().replace(',', '.')
                product.ref_unit_format = units_parts[1].strip() if len(units_parts) > 1 else ''
            else:
                error = ScrapingError(product=product, key='no_ref_unit_price')
                self.on_error_callback(error)
            product.prices = [price]

            image_elements = self.driver.find_elements(By.XPATH,
                                                       '//li[contains(@class,"jcarousel-item")]//span[contains(@class,"thumb")]//img')
            if not not image_elements:
                product.images = [Image(url=img.get_attribute('data-primaryimagesrc')) for img in image_elements]
            else:
                error = ScrapingError(product=product, key='no_images')
                self.on_error_callback(error)

            quantity_element = self.driver.find_elements(By.XPATH,
                                                         '//div[@id="producto_pestana_informacion_nutricion"]//div[@class="tablaValores"]//td')
            if not not quantity_element:
                quantity_text = quantity_element[0].text.strip()
                if '100' not in quantity_text:
                    error = ScrapingError(product=product, key='unknown_quantity')
                    self.on_error_callback(error)
            else:
                error = ScrapingError(product=product, key='no_quantity')
                self.on_error_callback(error)

            definition: NutritionalDefinition = NutritionalDefinition(quantity='100', values=[])
            value_elements = self.driver.find_elements(By.XPATH,
                                                       '//div[@id="producto_pestana_informacion_nutricion"]//div[@class="tablaValores"]//td')
            if not not value_elements:

                for value in value_elements:
                    span_title_element = value.find_elements(By.XPATH, './/span[@class="tablaValoresTitulo"]')
                    span_value_element = value.find_elements(By.XPATH, './/span[@class="tablaValorContenido"]')
                    if not not span_title_element and not not span_value_element:
                        title = span_title_element[0].text.strip()
                        value = span_value_element[0].text.strip()
                        definition.values.append(NutritionalValue(title=title, value=value))
                    else:
                        error = ScrapingError(product=product, key='unknown_nutritional_value')
                        self.on_error_callback(error)
                product.nutritional_data.nutritional_definitions = [definition]
            else:
                error = ScrapingError(product=product, key='no_nutritional_values')
                self.on_error_callback(error)

            bs = BeautifulSoup(self.driver.page_source, features="lxml")
            tab_info_element = bs.find('section', {'id': 'productTabs'}, recursive=True)
            if not not tab_info_element:
                ingredients_tab_element = tab_info_element.find('div', {'id': 'producto_pestana_ingredientes'})
                if ingredients_tab_element is not None:
                    ingredients_element = ingredients_tab_element.find('div', {'class': 'foodIngredients'})
                    if ingredients_element is not None:
                        ingredients_spans = ingredients_element.findAll('span')
                        if not not ingredients_spans:
                            product.nutritional_data.ingredients = ingredients_spans[1].text.strip()

                    allergens_element = ingredients_tab_element.find('div', {'class': 'foodAllergens'})
                    if allergens_element is not None:
                        allergens_spans = allergens_element.findAll('span')
                        if not not allergens_spans:
                            product.nutritional_data.allergens = allergens_spans[1].text.strip()

                nutritional_tab_element = tab_info_element.find('div', {'id': 'producto_pestana_informacion_nutricion'})
                if nutritional_tab_element is not None:
                    nutritional_element = nutritional_tab_element.find('div',
                                                                       {'class': 'productNutritionalInformation'})
                    nutritional_description_element = nutritional_element.find('span').find('font', recursive=True)
                    product.nutritional_data.description = nutritional_description_element.text.strip()

                conservation_tab_content = tab_info_element.find('div',
                                                                 {'id': 'producto_pestana_condiciones_conservacion'})
                if not not conservation_tab_content:
                    conservation_element = conservation_tab_content.find('div',
                                                                         {'class': 'productConservationCoditions'})
                    product.nutritional_data.conservation = conservation_element.find('span').text.strip()

                use_tab_content = tab_info_element.find('div', {'class': 'productHowToUse'}, recursive=True)
                if not not use_tab_content:
                    product.nutritional_data.use = use_tab_content.text.strip()

            self.on_product_callback(product)
            log_trace(f'new product: {product.id}')
