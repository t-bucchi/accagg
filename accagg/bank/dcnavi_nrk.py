# coding: utf-8
#
# This file is part of accagg.
#
# Copyright (C) 2018-2019 bucchi <bucchi79@gmail.com>
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
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup

from ..browser import Browser
from selenium.webdriver import FirefoxProfile

import re
from datetime import date
from time import sleep
import json

class Aggregator(Aggregator):
    @classmethod
    def bankid(self):
        return self.__module__.split('.')[-1]

    @classmethod
    def description(self):
        return "DCNavi NRK"

    @classmethod
    def login_info(self):
        return {'USRID': 'ユーザID',
                'PASSWORD': '暗証番号'}

    def _decode_date(self, str):
        match = re.match(r"^(\d{4})/(\d+)$", str)
        if match:
            y = int(match.group(1))
            m = int(match.group(2))
            d = 1
            return date(y, m, d)

    def _decode_amount(self, str):
        return int('0' + str.replace(',', '').replace('円', ''))

    def run(self, login_info):
        URL = "https://www.j-pec.co.jp/dcnavi/u010login/g00101.do"

        profile = FirefoxProfile()
        profile.set_preference('general.useragent.override', 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko')
        profile.set_preference("permissions.default.image", 2)

        browser = Browser(webdriver.Firefox(firefox_profile=profile))
        browser.implicitly_wait(180)

        # open URL
        browser.get(URL)
        browser.wait_for_loaded()

#        import pdb; pdb.set_trace()

        browser.find_element_by_id('loginSelectLinkNRK').click();

        # enter
        browser.sync_send_keys((By.ID, 'loginAccount'), login_info['USRID'])
        browser.sync_send_keys((By.ID, 'loginPasswd'), login_info['PASSWORD'])

        # Click login
        browser.wait_element((By.ID, 'nrkLoginLinkForNoAuto')).click()
        browser.wait_for_loaded()

        # check maintenance
        browser.implicitly_wait(0)
        try:
            browser.find_element_by_css_selector('.col1 table:nth-of-type(1)')
        except NoSuchElementException:
#            print("No service")
            browser.quit()
            return None
        browser.implicitly_wait(180)

        # トップ
        browser.find_element_by_css_selector('.col1 table:nth-of-type(1)')
        total = browser.find_element_by_css_selector('.col1 table:nth-of-type(1) tr:nth-of-type(1) .txtR').text
        total = self._decode_amount(total)

        # 過去ページヘ
        browser.find_elements_by_css_selector('.linkTypeNormal a')[0].click()
        browser.wait_for_loaded()

        # 10年
#        browser.find_element_by_link_text('直近10年').click()
#        browser.wait_for_loaded()

        html = browser.find_element_by_css_selector('script:last-child').get_attribute('innerHTML')

        resp = browser.download('https://www.j-pec.co.jp/dcnavi/u080mypagerel/g02302.do?startCode=-10').decode('utf8')
        json_text = re.sub(r'.*Chart\({', '', resp, flags=(re.DOTALL))
        json_text = re.sub(r'}\);.*', '', json_text, flags=(re.DOTALL))
        json_text = re.sub(r'(\S+):', r'"\1":', json_text, flags=(re.DOTALL))
        json_text = re.sub(r'"formatter":\s+function\(\)\s*{.*?}', '', json_text, flags=(re.DOTALL))
        json_text = re.sub(r'//.*', '', json_text)
        json_text = re.sub(r'\'', '"', json_text)
        json_text = '{'+json_text+'}'
#        print(json_text)
        d = json.loads(json_text)
#        print(d)
        date = d['xAxis']['categories']
        amount = d['series'][1]['data']

#        import pdb; pdb.set_trace()
        data = []
        for i in range(0,len(date)-1):
#            print(date[i], amount[i])
            if amount[i] is None:
                continue
            item = {'date' : self._decode_date(date[i]),
                    'deposit' : 0,
                    'desc' : '',
                    'balance' : int(amount[i]),
            }
            data.append(item)

        browser.quit()
        return {'fund': data}
