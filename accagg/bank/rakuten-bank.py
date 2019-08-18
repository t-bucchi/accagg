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

from .abstract import Aggregator

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select

from bs4 import BeautifulSoup

from accagg.browser import Browser

from time import sleep

import re
from datetime import date

class Aggregator(Aggregator):
    @classmethod
    def bankid(self):
        return self.__module__.split('.')[-1]

    @classmethod
    def description(self):
        return "Rakuten Bank"

    @classmethod
    def login_info(self):
        return {'USRID': 'ユーザID',
                'PASSWORD': 'ログインパスワード'}

    def __decode_date(self, str):
        match = re.match(r"(\d+)/(\d+)/(\d+)", str)
        if match:
            y = int(match.group(1))
            m = int(match.group(2))
            d = int(match.group(3))
            return date(y, m, d)

    def __decode_amount(self, str):
        if str[0] != '-':
            str = '0' + str
        return int(str.replace(',', '').replace('円', ''))

    def wait_until_blocked(self, b):
        b.implicitly_wait(0)
        for i in range(1, 20):
            try:
                print('try:%d' % i)
                es = b.find_element_by_class_name('loadingServer')
            except NoSuchElementException:
                b.implicitly_wait(180)
                return
            sleep(0.5)

    def run(self, login_info, lastdate):
        URL = "https://www.rakuten-bank.co.jp/"

        browser = Browser.firefox()
        browser.implicitly_wait(180)

        # open URL
        browser.get(URL)
        browser.wait_for_loaded()

        # import pdb; pdb.set_trace()

        # 新しいウインドウを開かずにログイン
        URL = browser.find_element_by_link_text('ログイン').get_attribute('href')
        browser.get(URL)
#        browser.find_element_by_link_text('ログイン').click()

        # enter
        browser.sync_send_keys((By.ID, 'LOGIN:USER_ID'), login_info['USRID'])
        browser.sync_send_keys((By.ID, 'LOGIN:LOGIN_PASSWORD'), login_info['PASSWORD'])

        # Click login
        browser.find_element_by_link_text('ログイン').click()
        browser.wait_for_loaded()

        # 日付
        today = self.__decode_date(browser.find_element_by_class_name('time-now01').text)

        # 普通預金
        result = []
        data = self.__get_ordinary(browser)
        if data:
            result.extend(data)

        # 円定期預金
        # data = self.__get_time_deposit(browser)
        # if data:
        #     result.extend(data)

        browser.quit()
        return result

    def __get_ordinary(self, browser):
#        import pdb; pdb.set_trace()
        # 入出金明細
        browser.wait_element((By.LINK_TEXT, "入出金明細")).click()
        browser.wait_for_loaded()

        soup = BeautifulSoup(browser.page_source, "html.parser")

        account = {'name': 'ordinary',
                'unit': 'Yen',
                'account': '普通', # 口座種別
                'history': [],
        }

        for row in soup.find('table', class_='table01').find_all('tr'):
            if not row.td:
                continue

            cols = [i.text.strip() for i in row.find_all('td')]
            # ['2019/08/01', 'xxxx', '60,000', '297,305']
            item = {'date': self.__decode_date(cols[0]),
                    'price': 1,
                    'amount': self.__decode_amount(cols[2]),
                    'payout': self.__decode_amount(cols[2]),
                    'balance': self.__decode_amount(cols[3]),
                    'desc': cols[1],
            }
            account['history'].insert(0, item)

        # ホームへ戻る
        browser.find_element_by_link_text('口座情報').click()
        # wait for display
        browser.wait_for_loaded()

        return [account]
