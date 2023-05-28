import requests
import json
import undetected_chromedriver as uc
from bs4 import BeautifulSoup


def request_json(url: str) -> any:
    menu_response = requests.get(url)
    return json.loads(menu_response.text)


def request_page(url: str):
    response = requests.get(url)
    return BeautifulSoup(response.text, features="lxml")


def get_driver() -> uc.Chrome:
    options = uc.ChromeOptions()

    options.add_argument('--headless')
    options.add_argument("window-size=1920x1080")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    driver = uc.Chrome(options=options, version_main=111)
    return driver


def normalize_text(text: str) -> str:
    return text.lower().strip().replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')

