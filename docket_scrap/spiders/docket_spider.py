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

# from scrapy.linkextractors import LinkExtractor
# from scrapy.http.request import Request


class DocketSpider(scrapy.Spider):
    # name of the spider
    name = 'docket'

    # url of the target page
    start_urls = [
        'http://www.ripuc.ri.gov/eventsactions/docket.html'
    ]

    # base url of the website category
    base_url = 'http://www.ripuc.ri.gov/eventsactions/'

    def parse(self, response):
        """
        Handling the initial response of the webpage
        """

        # Extracting the menu body of the webpage
        body = response.css("table")[2]

        # Extracting the table of the dockets
        docket_table = body.css("table")[1]

        # Importing all rows
        rows = docket_table.xpath('tr')

        # temporary storage for dockets for extraction purposes
        temporary_storage = dict()

        # Looping through each row for data
        for row in rows:

            # initializing docket item
            docket = Docket()

            # converting a row into a list of data
            col = row.css('td')

            # if a row has three elements
            if len(col) == 3:
                docket_id = col[0]

                # extracting file_url that resides in docket_id anchor tag
                file_url = self.extract_anchor(docket_id)
                docket["file_url"] = file_url

                # extracting docket_id that resides in first column of the row
                docket_id = self.extract_docket_id(docket_id)
                docket["docket_id"] = docket_id

                # extracting filer that resides in the second column of the row
                filer = col[1]
                filer = self.extract_filer(filer)
                docket["filer"] = filer

                # extracting description from third column in the row
                description = col[2]
                description = self.extract_description(description)
                docket["description"] = description

                # extracting date from the description
                date = self.extract_filing_date(description)
                docket["date"] = date

                # storing it all in temporary storage
                temporary_storage = docket

            # if the row has two elements
            elif len(col) == 2:

                # attempting to extract docket_id out of the first element
                docket_id = self.extract_docket_id(col[0])

                # if id is present, then the filer is merged with previous id
                if docket_id:
                    docket["docket_id"] = docket_id

                    # extracting description from second column
                    description = col[1]
                    description = self.extract_description(description)
                    docket["description"] = description

                    # extracting filer from temporary storage
                    filer = temporary_storage["filer"]
                    docket["filer"] = filer

                    # extracting file_url that resides in docket_id anchor tag
                    file_url = self.extract_anchor(docket_id)
                    docket["file_url"] = file_url

                    # extracting date from the description
                    date = self.extract_filing_date(description)
                    docket["date"] = date

                else:
                    # if id is not present, then it is merged with previous id
                    filer = col[0]
                    filer = self.extract_filer(filer)
                    docket["filer"] = filer

                    # extracting description from second column
                    description = col[1]
                    description = self.extract_description(description)
                    docket["description"] = description

                    # extracting date from description
                    date = self.extract_filing_date(description)
                    docket["date"] = date

                    # copying file_url and id from temporary storage
                    docket["file_url"] = temporary_storage["file_url"]
                    docket["docket_id"] = temporary_storage["docket_id"]

            # Since the row length is 1, id and description are merged with previous
            else:

                # extracting filer from the column
                filer = col[0]
                filer = self.extract_filer(filer)
                docket["filer"] = filer

                # copying previous docket data to current
                docket["file_url"] = temporary_storage["file_url"]
                docket["docket_id"] = temporary_storage["docket_id"]
                docket["description"] = temporary_storage["description"]
                docket["date"] = temporary_storage["date"]

            # writing docket into csv
            self.write_in_file(docket)

            yield docket

    def write_in_file(self, docket):
        # opening file for csv
        file = open('docket.csv', 'a', encoding='UTF-8', newline='')

        csv_columns = ['docket_id', 'description', 'date', 'filer', 'file_url']

        # creating a csv writer for the file
        writer = csv.DictWriter(file, csv_columns)

        # generating a row
        row = dict(docket)

        # writing on csv file
        writer.writerow(row)

    def extract_anchor(self, docket_id):
        link = docket_id.css('a::attr("href")').get()
        if link:
            if re.match("^.*(.pdf)$", link):
                link = urljoin(base=self.base_url, url=link)
            elif re.match('^.*.(.html)$', link):
                link = urljoin(base=self.base_url, url=link)
            return link
        #               Request(url=link, callback=self.fetch_pdf_links)
        else:
            return None

    #    def fetch_pdf_links(self, response):
    # extractor = LinkExtractor(allow='^.*\.(pdf)$')
    # extractor.extract_links()

    def extract_filing_date(self, description):
        if description:
            date = re.search("([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})", description)
            if date:
                date = date.group()
                return date
        return None

    def extract_description(self, description):
        description = description.css('td').extract()
        description = remove_tags(description[0])
        description = description.strip()
        description = re.sub(' +', ' ', description)
        if description:
            return description
        else:
            return None

    def extract_filer(self, filer):
        filer = filer.css('td').extract()
        filer = remove_tags(filer[0])
        if filer:
            return filer.strip()
        else:
            return None

    def extract_docket_id(self, docket_id):
        docket_id = docket_id.css('td').extract()
        docket_id = remove_tags(docket_id[0])
        docket_id = docket_id.strip()
        if docket_id.isnumeric():
            return docket_id
        else: return None
