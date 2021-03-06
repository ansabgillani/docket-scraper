# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class Docket(scrapy.Item):
    docket_id = scrapy.Field()
    description = scrapy.Field()
    date = scrapy.Field()
    filer = scrapy.Field()
    file_url = scrapy.Field()
