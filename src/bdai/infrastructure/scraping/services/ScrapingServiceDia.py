from datetime import datetime

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
from src.bdai.infrastructure.scraping.ScrapingUtils import request_page, normalize_text, get_driver
from src.bdai.infrastructure.storage.LoggingService import log_error, log_info, log_trace


class ScrapingServiceDia(ScrapingInterface):
    def get_origin(self) -> str:
        return 'dia'

    def __init__(self):
        self.is_saved = None
        self.find_product = None
        self.driver: Chrome = get_driver()
        self.on_product_callback = lambda p: print(p.to_json())
        self.on_error_callback = lambda p: print(p.to_json())
        self.base_url = 'https://www.dia.es/compra-online/'

    def scrape(self, on_product_callback, on_error_callback, find_product) -> None:
        log_info('dia - begin')
        p = Product()
        p.id = 'd1'
        p.name = 'producto dia 1'
        p.origin = 'dia'
        p.version = '2023050701'
        on_product_callback(p)
        p = Product()
        p.id = 'd1'
        p.name = 'producto dia 1'
        p.origin = 'dia'
        p.version = '2023050701'
        on_product_callback(p)
        p = Product()
        p.id = 'd1'
        p.name = 'producto dia 1'
        p.origin = 'dia'
        p.version = '2023050701'
        error = ScrapingError()
        error.product = p
        error.key = 'prueba'
        on_error_callback(p)
        log_info('dia - end')

    def __scrape(self, on_product_callback, on_error_callback, find_product, is_saved) -> None:
        log_info('scrape begin')

        self.on_product_callback = on_product_callback
        self.on_error_callback = on_error_callback
        self.find_product = find_product
        self.is_saved = is_saved

        content = request_page(self.base_url)
        menu = content.find('li', {'id': 'nav-submenu-container'})
        ul_element = menu.find('ul', {'class': 'nav-submenu ff-montse'})
        categories = ul_element.findAll('li', {'class': None}, recursive=False)

        for m1 in categories[0:6]:
            cat_1_name = m1.find('button', {'class': 'btn-main-category'}).text
            cat_1: Category = Category()
            cat_1.name = cat_1_name
            # print('-', cat_1_name)
            categories_2 = m1.find('div', {'class': 'child-menu'}).find('ul', {'class': 'child-menu-container'},
                                                                        recursive=False).findAll('li',
                                                                                                 {'class': None})
            for m2 in categories_2:
                a_element = m2.find('a')
                if a_element is not None:
                    cat_2_name = a_element.text
                    cat_2_url = a_element['href']
                    cat_2: Category = Category(name=cat_2_name, url=cat_2_url)
                    # print('--', cat_2_name)
                    grand_child = m2.find('ul', {'class', 'grandchild-menu'})
                    if grand_child is not None:
                        grand_child_li = grand_child.findAll('li', {'class': None})
                        for li in grand_child_li[1:]:
                            li_a_element = li.find('a')
                            products_url = li_a_element['href']
                            cat_3_name = li_a_element.text
                            cat_3_url = li_a_element['href']
                            cat_3: Category = Category(name=cat_3_name, url=cat_3_url)
                            # print('---', cat_3_name)
                            self.scrape_products_page(products_page_url=products_url, cat_1=cat_1, cat_2=cat_2,
                                                      cat_3=cat_3)
                    else:
                        self.scrape_products_page(products_page_url=cat_2.url, cat_1=cat_1, cat_2=cat_2)

        self.driver.close()
        self.driver.quit()
        log_info('scrape end')

    def scrape_products_page(self, products_page_url: str, cat_1: Category, cat_2: Category,
                             cat_3: Category = None) -> None:
        try:
            self.driver.get(self.base_url + products_page_url)
        except Exception:
            log_error()
            return
        page = BeautifulSoup(self.driver.page_source, features="lxml")
        self.scrape_products(page, cat_1, cat_2, cat_3)
        pages_select = page.find('select', {'name': 'pages-list'})
        if pages_select is not None:
            pages_options = len(pages_select.findAll('option'))
            for n in range(pages_options - 1):
                button = self.driver.find_elements(By.XPATH, "//a[@class='btn-pager btn-pager--next ']")[1]
                self.driver.execute_script("arguments[0].click();", button)
                page = BeautifulSoup(self.driver.page_source, features="lxml")
                self.scrape_products(page, cat_1, cat_2, cat_3)

    def scrape_products(self, products_content, cat_1: Category, cat_2: Category,
                        cat_3: Category = None):
        products_container = products_content.find('div', {'id': 'productgridcontainer'})
        products = products_container.findAll('div', {'class': 'product-list__item'})
        for product_element in products:

            id_element = product_element.find('div', {'class': 'prod_grid'})
            if id_element:
                product_id = id_element['data-productcode']
            else:
                product_id = 'aux_' + datetime.now().strftime('%Y%m%d%H%M%S')
                error = ScrapingError(key='no_id_element')
                self.on_error_callback(error)
            if self.is_saved(product_id):
                continue
            saved_product = self.find_product(id=product_id)
            product_exists: bool = not not saved_product
            if product_exists:
                try:
                    product = saved_product.copy()
                    price_container_element = product_element.find('div', {'class': 'price_container'})
                    if price_container_element:
                        price: Price = Price()
                        price_element = price_container_element.find('p', {'class': 'price'})
                        ref_price_element = price_container_element.find('p', {'class': 'pricePerKilogram'})
                        price.unit_value = price_element.text.strip()[:-2].replace(',', '.')
                        aux = ref_price_element.text.split('/')[0]
                        price.ref_unit_value = aux[:-2].strip().replace(',', '.')
                        product.prices = [price]
                        self.on_product_callback(product)
                        log_trace(f'saved product: {product.id}')
                    else:
                        error = ScrapingError(product=saved_product, key='no_stored_product_price_container')
                        self.on_error_callback(error)
                        product_exists = False
                except Exception as e:
                    product_exists = False
                    error = ScrapingError(product=saved_product, key='stored_product_except')
                    self.on_error_callback(error)
                    log_error()

            if not product_exists:
                product: Product = Product()
                product.brand = Brand()  # TRY REMOVE
                product.prices = []
                product.nutritional_data = NutritionalData()  # TRY REMOVE
                product.images = []  # TRY REMOVE
                product.categories = [cat_1, cat_2, cat_3]
                product.extra_data = {}  # TRY REMOVE
                product.url = self.base_url + product_element.find('a')['href']
                product.id = product_id
                self.scrape_product(product)

    def scrape_product(self, product: Product):
        try:
            product_page = request_page(self.base_url + product.url)
            name_element = product_page.find('h1', {'itemprop': 'name'})
            if name_element:
                product.name = name_element.text.strip()
            else:
                error = ScrapingError(product=product, key='no_product_name')
                self.on_error_callback(error)

            description_element = product_page.find('div', {'id': 'tab-productDescription'})
            if description_element:
                p_elements = description_element.findAll('p')
                product.description = '. '.join([desc.text.strip() for desc in p_elements])
            # else:
            #     error = ScrapingError(product=product, key='no_product_description')
            #     self.on_error_callback(error)

            price_container = product_page.find('div', {'class': 'price-container'})
            if price_container:
                product.prices = []
                unit_price = None  # TRY REMOVE
                unit_price_offer = None  # TRY REMOVE
                ref_unit_price = None  # TRY REMOVE
                ref_unit_price_offer = None  # TRY REMOVE
                price_element_parent = product_page.find('p', {'class': 'price price-discount'})
                if price_element_parent:
                    price_element = price_element_parent.find('span', {'class': 'big-price'})
                    unit_price = price_element.text.strip()[:-2].replace(',', '.')
                    price_element_offer = price_element_parent.find('s', {'class': None})
                    unit_price_offer = price_element_offer.text.strip()[:-2].replace(',', '.')

                ref_price_element = price_container.find('span', {'class': 'average-price average-discount'})
                if ref_price_element:
                    ref_price_text = ref_price_element.text.strip()
                    price_format_parts = ref_price_text.split('/')
                    ref_unit_price = price_format_parts[0][:-2].replace(',', '.')
                    product.ref_unit_format = price_format_parts[2][:-1].lower()
                    ref_unit_price_offer_element = ref_price_element.find('s', {'class': None})
                    aux_parts = ref_unit_price_offer_element.text.split('€')
                    ref_unit_price_offer = aux_parts[0].strip().replace(',', '.')

                if unit_price and unit_price_offer and ref_unit_price and ref_unit_price_offer:
                    price: Price = Price(type='PRICE', unit_value=unit_price, ref_unit_value=ref_unit_price)
                    offer: Price = Price(type='OFFER', unit_value=unit_price_offer, ref_unit_value=ref_unit_price_offer)
                    product.prices.append(price)
                    product.prices.append(offer)
                else:
                    price_element = product_page.find('span', {'class': 'big-price'})
                    if price_element:
                        unit_price = price_element.text.strip()[:-2].replace(',', '.')
                    else:
                        error = ScrapingError(product=product, key='no_unit_price_element',
                                              extra_data={'source': str(price_container)})
                        self.on_error_callback(error)
                        unit_price = -1

                    ref_price_element = price_container.find('span', {'class': 'average-price'})
                    if ref_price_element:
                        ref_price_text = ref_price_element.text.strip()
                        price_format_parts = ref_price_text.split('/')
                        ref_unit_price = price_format_parts[0][:-2].replace(',', '.')
                        product.ref_unit_format = price_format_parts[1][:-1].lower()
                    else:
                        error = ScrapingError(product=product, key='no_ref_unit_price_element',
                                              extra_data={'source': str(price_container)})
                        self.on_error_callback(error)
                        ref_unit_price = -1
                    if unit_price and ref_unit_price:
                        price: Price = Price(type='PRICE', unit_value=unit_price, ref_unit_value=ref_unit_price)
                        product.prices.append(price)
                    else:
                        error = ScrapingError(product=product, key='no_price_valid')
                        self.on_error_callback(error)
            else:
                error = ScrapingError(product=product, key='no_price_container')
                self.on_error_callback(error)

            brand_recommend = product_page.find('ul', {'class': 'brand-and-recommend'})
            brand_recommend_li = brand_recommend.findAll('li', recursive=False)
            if len(brand_recommend_li) > 1:
                error = ScrapingError(product=product, key='multiple_brand',
                                      extra_data={'source': str(brand_recommend)})
                self.on_error_callback(error)
            product_brand = brand_recommend.findAll('li', {'class': 'product-brand'})
            if len(product_brand) == 1:
                brand_a_element = product_brand[0].find('a')
                brand: Brand = Brand()
                brand.name = brand_a_element.text.strip().lower()
                brand.id = brand_a_element['href']
                product.brand = brand
            else:
                error = ScrapingError(product=product, key='no_brand',
                                      extra_data={'source': str(brand_recommend)})
                self.on_error_callback(error)

            images: list[Image] = []
            carrousel = product_page.find('div', {'id': 'carousel_alternate'})
            if carrousel is not None:
                carrousel_span = carrousel.findAll('span', {'class': 'thumb'})
                for span in carrousel_span:
                    src = span.find('img')['data-zoomimagesrc']
                    images.append(Image(url=src))
            product.images = images

            thumbnail_element = product_page.find('a', {'id': 'zoomImagen'})
            if thumbnail_element is not None:
                images.append(Image(url=thumbnail_element['href']))

            nutri_element = product_page.find('div', {'id': 'nutritionalinformation'})
            if nutri_element:
                product.nutritional_data = NutritionalData()
                nutri_info_title_elements = nutri_element.findAll('h4', {'class', 'nutri-title'})
                for info_element in nutri_info_title_elements:
                    info_title = normalize_text(info_element.text.strip().lower())
                    info_value = info_element.findNext('div')
                    if info_title == 'informacion adicional':
                        product.nutritional_data.description = info_value.text.strip()
                    elif info_title == 'ingredientes':
                        product.nutritional_data.ingredients = info_value.text.strip()
                    elif info_title == 'modo de empleo':
                        product.nutritional_data.use = info_value.text.strip()
                    elif info_title == 'otras menciones obligatorias o facultativas en la etiqueta':
                        product.nutritional_data.add_extra({'info': info_value.text.strip()})
                    elif info_title == 'condiciones de conservacion':
                        product.nutritional_data.conservation = info_value.text.strip()
                    elif info_title.startswith('informacion nutricional y adicional de'):
                        product.nutritional_data.nutritional_definitions = []
                        nutritional_table_element = nutri_element.find('div', {
                            'class': 'tabs-nutritionalinfo-table-nutrients'}, recursive=True)
                        if nutritional_table_element:
                            quantity_elements = nutritional_table_element.findAll('td', {'class': 'header-quantity'},
                                                                                  recursive=True)
                            if len(quantity_elements) > 1:
                                error = ScrapingError(product=product, key='info_nutrients_multiple_quantity')
                                self.on_error_callback(error)
                            elif len(quantity_elements) < 1:
                                error = ScrapingError(product=product, key='info_nutrients_no_quantity')
                                self.on_error_callback(error)
                            else:
                                quantity = quantity_elements[0].find('div').text.strip().lower()
                                definition: NutritionalDefinition = NutritionalDefinition(quantity=quantity, values=[])
                                nutrient_elements = nutritional_table_element.findAll('tr', {'class': None},
                                                                                      recursive=True)
                                for nutrient_element in nutrient_elements:
                                    td_elements = nutrient_element.findAll('td')[:2]
                                    title = td_elements[0].find('div').text.strip()
                                    value = td_elements[1].find('div').text.strip()
                                    definition.values.append(NutritionalValue(title=title, value=value))
                                product.nutritional_data.nutritional_definitions = [definition]
                    elif info_title.startswith('porcentaje de alochol'):
                        product.nutritional_data.add_extra({'alcohol': info_value.text.strip()})
                    elif info_title.startswith('variantes de produccion'):
                        product.nutritional_data.add_extra({'variantes': info_value.text.strip()})
                    else:
                        product.nutritional_data.add_extra({'title': info_title, 'value': info_value.text.strip()})
                        # error = ScrapingError(product=product, key='unknown_info',
                        #                       extra_data={'title': info_title, 'value': info_value.text.strip()})
                        # self.on_error_callback(error)
            # else:
            #     error = ScrapingError(product=product, key='no_nutri_element')
            #     self.on_error_callback(error)

            nutritional_elements = product_page.findAll('div',
                                                        {'class': 'tabs-nutritionalinfo-manufact-informationcontent'})
            for nutritional_element in nutritional_elements:
                title_element = nutritional_element.findNext('h4')
                title = title_element.text.lower().strip()
                if title == 'información contenido':
                    info_elements = title_element.findAllNext('div', {'class': 'tabs-nutritionalinfo-table-div'})
                    for info_element in info_elements[1:]:
                        info_title = info_element.find('div', {'class': 'tabs-nutritionalinfo-manufact-value'})
                        info_value = info_element.find('div', {'class': 'tabs-nutritionalinfo-manufact-quantity'})
                        if info_title and info_value:
                            info_title = normalize_text(info_title.text)
                            if 'cantidad neta' in info_title:
                                unit_parts = info_value.text.strip().split()
                                if len(unit_parts) == 2:
                                    product.unit_size = unit_parts[0]
                                    product.unit_format = unit_parts[1]
                                else:
                                    error = ScrapingError(product=product, key='no_enough_unit_parts',
                                                          extra_data={'value': info_value.text.strip()})
                                    self.on_error_callback(error)
                            elif 'signo de estimacion' in info_title:
                                pass
                            else:
                                error = ScrapingError(product=product, key='unknown_content_info',
                                                      extra_data={'title': info_title.strip(),
                                                                  'value': info_value.text.strip()})
                        else:
                            error = ScrapingError(product=product, key='no_info_title',
                                                  extra_data={'source': str(info_element)})
                            self.on_error_callback(error)
                elif title == 'manufacturado':
                    manufact_elements = title_element.findAllNext('div', {'class', 'tabs-nutritionalinfo-row-div'})
                    for manufact_value in manufact_elements:
                        product.brand.add_factory_extra(manufact_value.text.strip())
                else:
                    error = ScrapingError(product=product, key='unknown_info',
                                          extra_data={'source': str(nutritional_element)})
                    self.on_error_callback(error)
        except Exception as e:
            error = ScrapingError(product=product, key='exception', exception=str(e))
            self.on_error_callback(error)
            log_error()
        else:
            self.on_product_callback(product)
            log_trace(f'new product: {product.id}')
