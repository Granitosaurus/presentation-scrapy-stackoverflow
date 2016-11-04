# -*- coding: utf-8 -*-
import json

import scrapy
from scrapy import Request
from w3lib.url import add_or_replace_parameter, url_query_parameter


class SotagsSpider(scrapy.Spider):
    name = "sotags"
    start_url = "https://api.stackexchange.com/2.2/questions?page=1&" \
                "pagesize=100&order=desc&sort=activity&tagged=nutch&" \
                "site=stackoverflow&filter=!-n6UaSfTzX-uZPFjO11d8XTmqEPDA3cOgAH2GZHCeY6.3_Zm9(UZZm&" \
                "key={}".format

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.key = kwargs.get('key', None)
        if not self.key:
            raise Exception('missing key parameter')
        self.users_tpl = "https://api.stackexchange.com/2.2/users/{{}}?order=desc&" \
                         "sort=reputation&pagesize=100&site=stackoverflow" \
                         "&filter=!0Z-Lvhr_SD(beBlP8X73l5A9X" \
                         "&key={}".format(self.key).format
        self.start_urls = [self.start_url(self.key)]

    def parse(self, response):
        data = json.loads(response.body.decode('utf-8'))
        items = data['items']
        ids = [i['owner'].get('user_id', None) for i in items]
        ids = ';'.join([str(i) for i in ids if i])
        yield Request(self.users_tpl(ids), self.parse_questions,
                      meta={'item_data': data,
                            'url': response.url})

    def parse_questions(self, response):
        user_data = json.loads(response.body.decode('utf-8'))
        user_items = user_data['items']

        data = response.meta['item_data']
        url = response.meta['url']
        for item in data['items']:
            expanded_owner = [i for i in user_items
                              if item['owner'].get('user_id', None) == i['user_id']]
            if expanded_owner:
                item['owner'] = expanded_owner[0]
            else:
                self.crawler.stats.inc_value('expanded_owner/missing')
            yield item
        if not data['has_more']:
            return
        page = data['page'] + 1
        url = add_or_replace_parameter(url, 'page', page)
        yield Request(url, self.parse)
