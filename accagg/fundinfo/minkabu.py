# coding: utf-8
#
# This file is part of accagg.
#
# Copyright (C) 2019 bucchi <bucchi79@gmail.com>
#
#  Foobar is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Foobar is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

from .abstract import Scraper
from bs4 import BeautifulSoup

import urllib.parse
import urllib.request
import json
import time
import unicodedata

import re
from datetime import date

class Minkabu(Scraper):
    @classmethod
    def id(self):
        return 'minkabu'

    def __decode_date(self, val):
        t = time.gmtime(val/1000)
        return date(t.tm_year, t.tm_mon, t.tm_mday)

    def __decode_strdate(self, str):
        match = re.match(r"(\d{4})年(\d{2})月(\d{2})日", str)
        if match:
            y = int(match.group(1))
            m = int(match.group(2))
            d = int(match.group(3))
            return date(y, m, d)
        match = re.match(r".*(\d{2,4})/(\d{2})/(\d{2})", str)
        if match:
            y = int(match.group(1))
            if y < 100:
                y += 2000
            m = int(match.group(2))
            d = int(match.group(3))
            return date(y, m, d)

    def __decode_amount(self, str):
        if str[0] != '-':
            str = '0' + str
        return int('0' + str.replace(',', '').replace('円', ''))

    def search(self, name):
        # 半角カナ→全角変換
        name = unicodedata.normalize('NFKC', name)
        # name = name.translate({ord(u'('): u'（', ord(u')'): u'）'})
        URL = "https://itf.minkabu.jp/search/result?keywords={}"
        URL = URL.format(urllib.parse.quote(name))
        # print(URL)

        # open URL
        req = urllib.request.Request(URL)
        with urllib.request.urlopen(req) as res:
            body = res.read()
        # print(body)
        soup = BeautifulSoup(body, "html.parser")
        # print(soup.find_all("a"))
        # print(soup.html.string)
        # import pdb; pdb.set_trace()
        result = []

        if soup.em.text == '0':
            return result

        for item in soup.find("table", class_="compare_table").tbody.find_all('tr'):
            link = item.a.get("href")
            name = str.strip(item.a.string)
            m = re.search(r'/([^/]*)$', link)
            if m is False:
                continue
            id = m.group(1)
#            print(f'id={id} name={name}')
            result.append({'id': id, 'name': name})

        return result

    def price_log(self, id):
        URL = 'https://itf.minkabu.jp/fund/' + id + '/get_line_daily_json'
        # print(URL)

        # open URL
        req = urllib.request.Request(URL)
        with urllib.request.urlopen(req) as res:
            body = res.read()
        # print(body)
        data = json.loads(body)
        result = []
        for i in data['data']:
            result.insert(0, {
                'date': self.__decode_date(i[0]),
                'price': i[1]
            })
        return result

    def getinfo(self, id):
        URL = "https://itf.minkabu.jp/fund/"+id
        # print(URL)

        # open URL
        req = urllib.request.Request(URL)
        with urllib.request.urlopen(req) as res:
            body = res.read()
        # print(body)
        soup = BeautifulSoup(body, "html.parser")
        # import pdb; pdb.set_trace()

        info = {}
        info['id'] = id
        info['name'] = soup.find(class_='stock_name').text
        info['class'] = soup.find(text='分類').parent.parent.td.text
        info['price'] = self.__decode_amount(soup.find(class_='stock_price').text)
        info['lastdate'] = self.__decode_strdate(soup.find(class_='fsm').text)
        return info
