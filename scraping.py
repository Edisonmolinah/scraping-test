from scrapy.item import Field, Item
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from scrapy.crawler import CrawlerProcess
from bs4 import BeautifulSoup
import pandas as pd
from itemloaders.processors import MapCompose


class Articulo(Item):
    titulo = Field()
    precio = Field()
    descripcion = Field()


class MercadoLibreCrawler(CrawlSpider):
    name = 'mercadoLibre'

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
        'CLOSESPIDER_ITEMCOUNT': 100,  # Limitar el número de artículos a 100
        'DOWNLOAD_DELAY': 1,
    }

    allowed_domains = ['listado.mercadolibre.com.ec', 'articulo.mercadolibre.com.ec']
    start_urls = ['https://listado.mercadolibre.com.ec/guantes-para-moto']

    rules = (
        Rule(LinkExtractor(allow=r'/_Desde_\d+'), follow=True),
        Rule(LinkExtractor(allow=r'/MEC-'), follow=True, callback='parse_items'),
    )

    def __init__(self):
        super().__init__()
        self.data = []  # Lista para almacenar los resultados

    def parse_items(self, response):
        item = ItemLoader(Articulo(), response)

        # Extraer el título
        item.add_xpath('titulo', '//h1/text()', MapCompose(str.strip))

        # Extraer la descripción
        item.add_xpath('descripcion', '//div[@class="ui-pdp-description"]/p/text()',
                       MapCompose(lambda i: ' '.join(i.split()), str.strip))

        # Usar BeautifulSoup para extraer el precio
        soup = BeautifulSoup(response.body, 'html.parser')
        precio = soup.find(class_="andes-money-amount__fraction")
        if precio:
            precio_completo = precio.text.strip().replace(' ', '')  # Limpiar el precio
        else:
            precio_completo = "Precio no disponible"

        item.add_value('precio', precio_completo)

        # Almacenar el item en la lista
        self.data.append(item.load_item())

    def closed(self, reason):
        # Convertir la lista de datos en un DataFrame de pandas al cerrar el spider
        df = pd.DataFrame(self.data)
        df.to_csv('ml_guantes.csv', index=False)  # Guardar el DataFrame en un archivo CSV
        print("Se ha guardado 'ml_guantes.csv' con los datos.")
        print(df.head(10))  # Imprimir las primeras 10 filas del DataFrame


if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(MercadoLibreCrawler)
    process.start()