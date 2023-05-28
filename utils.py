import os


def get_root_path() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def get_src_path() -> str:
    return os.sep.join([os.path.dirname(os.path.abspath(__file__)), 'src', 'bdai'])


def get_data_path() -> str:
    return os.sep.join(
        [os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'super_smart_scraping_data', 'data'])
