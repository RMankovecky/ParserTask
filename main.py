import json
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Tuple

class DataSaver:
    def save_json(self, json_data: dict, file_name: str = 'leaflets.json') -> None:
        with open(file_name, "w", encoding = "utf-8") as file:
            json.dump(json_data, file, ensure_ascii = False, indent = 4)

class LeafletCollection:
    def __init__(self):
        self.collection = {}
        self.data_saver = DataSaver()

    def append(self, key: str, data: list[dict]) -> None:
        if key not in self.collection:
            self.collection[key] = []

        self.collection[key].extend(data)

    def get_json(self):
        return self.data_saver.save_json(self.__serialize())

    def __serialize(self):
        serializable = {}

        for hypermarket_name, leaflets in self.collection.items():
            serializable[hypermarket_name] = []

            for leaflet in leaflets:
                serializable[hypermarket_name].append(leaflet.to_dict())

        return serializable


class Leaflet:
    __slots__ = ['title', 'thumbnail', 'shop_name', 'valid_from', 'valid_to', 'parsed_time']

    def __init__(
        self,
        title: str,
        thumbnail: str,
        shop_name: str,
        valid_from: str,
        valid_to: str,
    ):
        self.title = title
        self.thumbnail = thumbnail
        self.shop_name = shop_name
        self.valid_from = valid_from
        self.valid_to = valid_to
        self.parsed_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "thumbnail": self.thumbnail,
            "shop_name": self.shop_name,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "parsed_time": self.parsed_time,
        }

    def get_title(self) -> str:
        return self.title

    def get_thumbnail(self) -> str:
        return self.thumbnail

    def get_shop_name(self) -> str:
        return self.shop_name

    def get_valid_from(self) -> str:
        return self.valid_from

    def get_valid_to(self) -> str:
        return self.valid_to

    def get_parsed_time(self) -> str:
        return self.parsed_time

    def set_title(self, title: str) -> None:
        self.title = title

    def set_thumbnail(self, thumbnail: str) -> None:
        self.thumbnail = thumbnail

    def set_shop_name(self, shop_name: str) -> None:
        self.shop_name = shop_name

    def set_valid_from(self, valid_from: str) -> None:
        self.valid_from = valid_from

    def set_valid_to(self, valid_to: str) -> None:
        self.valid_to = valid_to


class HttpClient:
    def __init__ (self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; Python Scraper)"
        })

    def get(self, url: str) -> requests.Response:
        return self.session.get(url, timeout = 15)


class LeafletScraper:

    HYPERMARKET_LINK_SELECTOR: str = '#left-category-shops > li > a'
    LEAFLET_ELEMENT_SELECTOR: str = '.page-body div.brochure-thumb'
    THUMBNAIL_SELECTOR: str = 'picture img'
    DATE_SELECTOR: str = '.letak-description p:has(small) > small.hidden-sm'

    def __init__(self, http_client: HttpClient):
        self.http_client = http_client
        self.base_url = 'https://www.prospektmaschine.de'

    def scrape_all_leaflets(self) -> LeafletCollection:
        response = self.http_client.get(f"{self.base_url}/hypermarkte/")
        webpage = BeautifulSoup(response.content, 'html.parser')
        hypermarket_links = webpage.select(self.HYPERMARKET_LINK_SELECTOR)

        leaflet_collection = LeafletCollection()

        for link in hypermarket_links:
            hypermarket_name = link.text.strip()
            url = f"{self.base_url}{link.get('href')}"

            leaflets = self.__scrape_leaflets(url, hypermarket_name)

            leaflet_collection.append(hypermarket_name, leaflets)

        return leaflet_collection

    def __scrape_leaflets(self, url: str, hypermarket_name: str) -> list:
        response = self.http_client.get(url)
        page = BeautifulSoup(response.content, 'html.parser')
        leaflet_elements = page.select(self.LEAFLET_ELEMENT_SELECTOR)

        leaflets = []

        for element in leaflet_elements:
            leaflet = self.__extract_leaflet_data(element, hypermarket_name)
            leaflets.append(leaflet)

        return leaflets

    def __extract_leaflet_data(self, element, hypermarket_name: str) -> Leaflet:
        leaflet_thumbnail = element.select_one('picture img')['src']
        date_text = element.select_one(self.DATE_SELECTOR).text
        start, end = self.__parser_date(date_text)

        return Leaflet(
            title = 'Prospekt',
            thumbnail = leaflet_thumbnail,
            shop_name = hypermarket_name,
            valid_from = start,
            valid_to = end,
        )

    def __parser_date(self, dates: str) -> Tuple[str, str]:
        pattern = re.compile(r"(\d{2}\.\d{2}\.?(?:\d{4})?)\s*-\s*(\d{2}\.\d{2}\.\d{4})")
        match = pattern.search(dates)

        if not match:
            return '', ''

        start, end = match.groups()

        return start, end

class ProspektMaschineScraper:
    def __init__(self, leaflet_scraper: LeafletScraper):
        self.leaflet_scraper = leaflet_scraper

    def scrape(self) -> None:
        leaflet_collection = self.leaflet_scraper.scrape_all_leaflets()
        leaflet_collection.get_json()


def main():
    scraper = ProspektMaschineScraper(
        leaflet_scraper = LeafletScraper(
            http_client = HttpClient(),
        )
    )

    scraper.scrape()

if __name__ == "__main__":
    main()

