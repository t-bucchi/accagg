# coding: utf-8
#
# This file is part of accagg.
#
# Copyright (C) 2018 bucchi <bucchi79@gmail.com>
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

from .abstract import Aggregator

from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

from ..browser import Browser

import re
from datetime import date
from time import sleep

class Aggregator(Aggregator):
    @classmethod
    def bankid(self):
        return self.__module__.split('.')[-1]

    @classmethod
    def description(self):
        return "WealthNavi for 住信SBIネット銀行"

    @classmethod
    def login_info(self):
        return {'EMAIL': 'メールアドレス',
                'PASSWORD': 'パスワード'}

    def _decode_date(self, str):
        match = re.match(r"^(\d+)-(\d+)-(\d+)$", str)
        if match:
            y = int(match.group(1))
            m = int(match.group(2))
            d = int(match.group(3))
            return date(y, m, d)

    def run(self, login_info):
        URL = "https://ssnb.wealthnavi.com/"

        browser = Browser(webdriver.Firefox())
        browser.implicitly_wait(3)

        # open URL
        browser.get(URL)
        browser.wait_for_loaded()

        import pdb; pdb.set_trace()

        # enter
        browser.sync_send_keys((By.ID, 'username'), login_info['EMAIL'])
        browser.sync_send_keys((By.ID, 'password'), login_info['PASSWORD'])

        # Click login
        browser.find_element_by_id('login').click();

        # ログイン後画面
        html = browser.find_element_by_css_selector('.data-history tbody').get_attribute('innerHTML')
        rows = BeautifulSoup(html).find_all('tr')

        for item in rows:
#            print(item.get_attribute('innerHTML'))
            date = self._decode_date(item.th.string)
            c = [x.string for x in item.select(".value")]

            item = {'date' : date,
                    'deposit' : int(c[1]),
                    'desc' : '',
                    'balance' : int(float(c[0]))
            }
#            print('\t'.join(item))

            # Prepend.
            # Detail list is sorted by descending order
            # Passbook order is ascending
            data.insert(0, item)

        deposit = 0
        for i in data:
            if deposit != i['deposit']:
                tmp = deposit
                deposit = i['deposit']
                i['deposit'] -= tmp
            else:
                i['deposit'] = 0

        browser.quit()
        return {'fund': data}