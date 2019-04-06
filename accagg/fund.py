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

from .browser import Browser
from bs4 import BeautifulSoup

import urllib.parse
import urllib.request
import json
import time

from time import sleep

import re
from datetime import date

class Fund:
    def _decode_date(self, val):
        t = time.gmtime(val/1000)
        return date(t.tm_year, t.tm_mon, t.tm_mday)

    def search(self, name):
        name = name.translate({ord(u'('): u'（', ord(u')'): u'）'})
        URL = "https://www.rakuten-sec.co.jp/web/fund/find/search/result.html?condition31=%E3%83%95%E3%82%A1%E3%83%B3%E3%83%89%E5%90%8D%E7%A7%B0like*{}*"
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
        for item in soup.find("div", id="table1").tbody.find_all("tr"):
            link = item.th.a.get("href")
            name = str.strip(item.th.a.string)
            m = re.search(r'ID=(.*)', link)
            if m is False:
                continue
            id = m.group(1)
#            print(f'id={id} name={name}')
            result.append({'id': id, 'name': name})

        return result

    def price_log(self, id):
        URL = "https://www.rakuten-sec.co.jp/web/fund/detail/?ID="+id
        # print(URL)

        # open URL
        req = urllib.request.Request(URL)
        with urllib.request.urlopen(req) as res:
            body = res.read()
        # print(body)
        soup = BeautifulSoup(body, "html.parser")
        # print(soup.find_all("a"))
        # print(soup.html.string)
#        import pdb; pdb.set_trace()
        script = soup.find("script", language="javascript")
        phase = 0
        js = ""
        for line in script.string.split("\n"):
            if phase == 0:
                m = re.search(r"'基準価額'", line)
                if m:
                    phase += 1
#                    print(line)
            elif phase == 1:
#                print(line)
                m = re.search(r'\s+data\s*:(.*)', line)
                if m:
                    phase += 1
                    js = '{"data":' + m.group(1)
            elif phase == 2:
#                print(line)
#                print(json)
                js += line
                if js.count('[') == js.count(']'):
                    js += '}'
                    break

        data = json.loads(js)
#        print(js)
#        print(data)
#        print(self._decode_date(data['data'][-1][0]))
        result = []
        for i in data['data']:
            result.append({
                'date': self._decode_date(i[0]),
                'price': i[1]
            })
        return result

if __name__ == '__main__':
    fund = Fund()
    id = fund.search('ＳＢＩ・全世界株式インデックス・ファンド(雪だるま（全世界株式）)')
    print(id)
    log = fund.price_log("JP90C0003PR7")
    print(log)
