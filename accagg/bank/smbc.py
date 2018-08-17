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
from selenium.common.exceptions import NoSuchElementException

from ..browser import Browser
import csv
import re
from datetime import date

class Aggregator(Aggregator):
    @classmethod
    def bankid(self):
        return self.__module__.split('.')[-1]

    @classmethod
    def description(self):
        return "Mitsui Sumitomo Bank"

    @classmethod
    def login_info(self):
        return {'USRID1': '契約者ID 1',
                'USRID2': '契約者ID 2',
                'PASSWORD': '暗証番号1'}

    def __decode_date(self, str):
        match = re.match(r"^([MTSH])(\d\d)\.(\d\d)\.(\d\d)$", str)
        if match:
            y = int(match.group(2))
            m = int(match.group(3))
            d = int(match.group(4))
            if match.group(1) == "M":
                y += 1868 - 1
            elif match.group(1) == "T":
                y += 1912 - 1
            elif match.group(1) == "S":
                y += 1926 - 1
            elif match.group(1) == "H":
                y += 1989 - 1
                return date(y, m, d)

    def run(self, login_info):
        URL = "https://direct.smbc.co.jp/aib/aibgsjsw5001.jsp"

        browser = Browser(webdriver.Firefox())
        #browser = webdriver.Chrome()
        #browser = webdriver.PhantomJS()
        browser.implicitly_wait(3)

        browser.get(URL)
        # open URL

        # enter
        browser.sync_send_keys((By.ID, "USRID1"), login_info['USRID1'])
        browser.sync_send_keys((By.ID, "USRID2"), login_info['USRID2'])

        # Password
        browser.sync_send_keys((By.ID, "PASSWORD"), login_info['PASSWORD'])

        # Click login
        browser.find_element_by_name("bLogon.y").click();

        # 期限切れなら次へをクリック
        try:
            es = browser.find_elements_by_name("imgNext.y")
        except NoSuchElementException:
            print("no entry")
        else:
            es[0].click()

        # ログイン後画面

        # 明細照会をクリック
        browser.find_element_by_css_selector(".detailsBtn > a").click()

        # csv形式でダウンロード
        resp = browser.download(browser.find_element_by_id("DownloadCSV")
                                .get_attribute("href"))

        # 先頭行を抜いて csv.reader に渡す
        rows = csv.reader(resp.decode("shift_jis").split("\r\n")[1:])

        all_data = {}
        data = []
        for row in rows:
            if len(row) != 5:
                continue
            item = {'date' : self.__decode_date(row[0]),
                    'deposit' : int('0' + row[2]) - int('0' + row[1]),
                    'desc' : row[3],
                    'balance' : int('0' + row[4])
            }
            #print('\t'.join(row))
            data.append(item)

        all_data['ordinary'] = data
        browser.quit()
        return all_data
