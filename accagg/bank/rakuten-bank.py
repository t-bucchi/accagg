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
        data = self.__get_time_deposit(browser)
        if data:
            result.extend(data)

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

    def __get_time_deposit(self, browser):
        # import pdb; pdb.set_trace()

        # 現在の合計を取得
        total = self.__decode_amount(browser.find_elements_by_css_selector('.amount')[3].text)

        # 定期預金
        browser.find_element_by_link_text('定期預金').click()

        # 明細
        browser.find_element_by_css_selector(u'input[value="明細照会・変更・解約"]').click()

        data = []
        account = {'name': 'time_deposit',
                'unit': 'Yen',
                'account': '普通', # 口座種別
                'history': [],
        }

        # 解約済み
        ret = self.__get_time_deposit_old(browser)
        if ret:
            data.extend(ret)

        # 契約中
        soup = BeautifulSoup(browser.page_source, "html.parser")

        for row in soup.find('table', class_='smedium').find_all('tr'):
            if not row.td:
                continue

            cols = [i.text.strip() for i in row.find_all('td')]
            # ['', '2019/09/17', '0003', '資金お引越し', '1ヶ月', '0.15%', '2019/10/17', '満期自動解約', '142,976円']
            item = {'date': self.__decode_date(cols[1]),
                    'price': 1,
                    'amount': self.__decode_amount(cols[8]),
                    'payout': self.__decode_amount(cols[8]),
                    'balance': 0,
                    'desc': cols[3],
            }
            data.insert(0, item)

        # 解約済みと契約中を並べ替え
        data = sorted(data, key=lambda item: item['date'])

        # balance を逆算
        balance = total
        for i in reversed(range(0,len(data))):
            data[i]['balance'] = balance
            balance -= data[i]['amount']

        # from pprint import pprint
        # pprint(data)
        account['history'] = data

        # ホームへ戻る
        browser.find_element_by_partial_link_text('MyAccount').click()
        # wait for display
        browser.wait_for_loaded()

        return [account]

    def __get_time_deposit_old(self, browser):
        # 解約済み
        browser.implicitly_wait(1)
        try:
            browser.find_element_by_partial_link_text('満期・中途解約済み').click()
        except NoSuchElementException:
            browser.implicitly_wait(180)
            return
        browser.implicitly_wait(180)

        soup = BeautifulSoup(browser.page_source, "html.parser")
        data = []

        # 解約済みを収集
        for row in soup.find_all('div', class_='medium'):
            # if not row.td:
            #     continue
            div = row.find_all('div')

            begin = self.__decode_date(div[0].text.strip().split('：')[1])
            end = self.__decode_date(div[8].text.strip().split('：')[1])
            depo = self.__decode_amount(div[9].find_all('span')[1].text)
            ret = self.__decode_amount(div[10].find_all('span')[1].text)

            cols = [i.text.strip() for i in row.find_all('td')]

            # 返却
            item = {'date': end,
                    'price': 1,
                    'amount': -ret,
                    'payout': -ret,
                    'balance': 0,
                    'desc': '満期',
            }
            data.insert(0, item)

            # 利子
            item = {'date': end,
                    'price': 1,
                    'amount': ret - depo,
                    'payout': ret - depo,
                    'balance': 0,
                    'desc': '利息',
            }
            data.insert(0, item)

            # 預け入れ
            item = {'date': begin,
                    'price': 1,
                    'amount': depo,
                    'payout': depo,
                    'balance': 0,
                    'desc': div[2].find_all('span')[1].text,
            }
            data.insert(0, item)

        # 契約中
        browser.find_element_by_partial_link_text('定期預金一覧に戻る').click()
        return data
