"""
Scrapy Spider that crawls RIPUC webpage for commission dockets
run by command "scrapy crawl docket" on cmd
"""

from w3lib.html import remove_tags
import re
import scrapy
from urllib.parse import urljoin
import csv

from ..items import Docket

# from scrapy.http.request import Request


class DocketSpider(scrapy.Spider):
    name = 'docket'
    start_urls = [
        'http://www.ripuc.ri.gov/eventsactions/docket.html'
    ]
    base_url = 'http://www.ripuc.ri.gov/eventsactions/'

    def parse(self, response):
        #   Handling the response of the webpage
        rows = response.css("table")[2].css("table")[1].xpath('tr')

        #    temporary storage for dockets to check if there is any missing field

        docket_temporary_storage = dict()

        for row in rows:
            col = row.css('td')

            if len(col) == 3:

                #    when a row has three columns, it must have an ID, a Filer and a Description
                docket = self.create_docket(
                    docket_id=self.extract_docket_id(col[0]),
                    description=self.extract_description(col[2]),
                    date=self.extract_filing_date(col[2]),
                    filer=self.extract_filer(col[1]),
                    file_url=self.extract_links(col[0])
                )
                docket_temporary_storage = docket

            elif len(col) == 2:
                docket_id = self.extract_docket_id(col[0])

                if docket_id:
                    # if id is present, then the filer is merged with previous id
                    docket = self.create_docket(
                        docket_id=docket_id,
                        description=self.extract_description(col[1]),
                        date=self.extract_filing_date(col[1]),
                        filer=docket_temporary_storage["filer"],
                        file_url=self.extract_links(col[0])
                    )

                else:
                    # if id not present, then it is merged with previous id
                    docket = self.create_docket(
                        docket_id=docket_temporary_storage["docket_id"],
                        description=self.extract_description(col[1]),
                        date=self.extract_filing_date(col[1]),
                        filer=self.extract_filer(col[0]),
                        file_url=docket_temporary_storage["file_url"]
                    )

            # id and description are merged with previous
            else:
                docket = self.create_docket(
                    docket_id=docket_temporary_storage["docket_id"],
                    description=docket_temporary_storage["description"],
                    date=docket_temporary_storage["date"],
                    filer=self.extract_filer(col[0]),
                    file_url=docket_temporary_storage["file_url"]
                )

            self.append_in_file(docket)

            yield docket

    def create_docket(self,
                      docket_id,
                      description,
                      date,
                      filer,
                      file_url
                      ):
        # initializing docket item
        docket = Docket()
        docket['docket_id'] = docket_id
        docket['description'] = description
        docket["date"] = date
        docket["filer"] = filer
        docket["file_url"] = file_url
        return docket

    def append_in_file(self, docket):
        file = open('docket.csv', 'a', encoding='UTF-8', newline='')
        csv_columns = ['docket_id', 'description', 'date', 'filer', 'file_url']
        writer = csv.DictWriter(file, csv_columns)
        row = dict(docket)
        writer.writerow(row)

    def extract_links(self, docket_id):
        link = docket_id.css('a::attr("href")').get()
        if link:
            if re.match("^.*(.pdf)$", link):
                link = urljoin(base=self.base_url, url=link)
                return link
            elif re.match('^.*.(.html)$', link):
                link = urljoin(base=self.base_url, url=link)
                #                request = Request(url=link, callback=self.fetch_pdf_links)
                #                print(dir(request))
                #                yield request
                return link

    # def fetch_pdf_links(self, response):
    #     import pdb
    #     pdb.set_trace()
    #     extractor = LinkExtractor(allow='^.*.(pdf)$')
    #     extractor.extract_links(response)
    #     print(extractor)

    def extract_filing_date(self, description):
        description = self.extract_description(description)
        if description:
            date = re.search(
                "([0-9]{1,2}/{1,2}[0-9|X]{1,2}/{0,2}[0-9]{2,4})", description)
            if date:
                date = date.group()
                return date
            else:
                date = re.search("(filed )(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul("
                                 "?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|(Nov|Dec)(?:ember)?) ?([0-9]{1,"
                                 "2}),? *([0-9]{2,4})", description)
                if date:
                    date = date.group()
                    date = date.split()
                    months = {
                        'January': 1,
                        'February': 2,
                        'March': 3,
                        'April': 4,
                        'May': 5,
                        'June': 6,
                        'July': 7,
                        'August': 8,
                        'September': 9,
                        'October': 10,
                        'November': 11,
                        'December': 12
                    }
                    date = f"{months[date[1]]}/{date[2].replace(',','')}/{date[3]}"
                    return date

    def extract_description(self, description):
        description = description.css('td').extract()
        description = remove_tags(description[0])
        description = description.strip()
        description = re.sub(' +', ' ', description)
        if description:
            return description

    def extract_filer(self, filer):
        filer = filer.css('td').extract()
        filer = remove_tags(filer[0])
        if filer:
            return filer.strip()

    def extract_docket_id(self, docket_id):
        docket_id = docket_id.css('td').extract()
        docket_id = remove_tags(docket_id[0])
        docket_id = docket_id.strip()
        if docket_id.isnumeric():
            return docket_id
