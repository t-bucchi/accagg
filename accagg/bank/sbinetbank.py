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
        return "SBI Sumishin Net Bank"

    @classmethod
    def login_info(self):
        return {'USRID': 'ID',
                'PASSWORD': '暗証番号'}

    def __decode_date(self, str):
        match = re.match(r"^(\d+)年(\d+)月(\d+)日$", str)
        if match:
            y = int(match.group(1))
            m = int(match.group(2))
            d = int(match.group(3))
            return date(y, m, d)

    def _decode_amount(self, str):
        if str[0] != '-':
            str = '0' + str
        return int('0' + str.replace(',', '').replace('円', ''))

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

    def run(self, login_info):
        URL = "https://www.netbk.co.jp"

        browser = Browser.firefox()
        browser.implicitly_wait(180)

        # open URL
        browser.get(URL)
        browser.wait_for_loaded()

#        import pdb; pdb.set_trace()

        # ログイン
        browser.find_element_by_link_text("ログイン").click()

        # enter
        browser.sync_send_keys((By.NAME, 'userName'), login_info['USRID'])
        browser.sync_send_keys((By.CSS_SELECTOR, 'input[type="password"]'), login_info['PASSWORD'])

        # Click login
        browser.find_element_by_css_selector('button[type="submit"]').click()
        browser.wait_for_title_changed()

        # 確認 (次へを押す)
        browser.wait_element((By.LINK_TEXT, '次へ進む')).click()

        # ホーム

        result = []
#        import pdb; pdb.set_trace()
        # 普通預金
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
        self.wait_until_blocked(browser)
        sleep(0.5)
        e = browser.wait_element((By.LINK_TEXT, "入出金明細"))
        browser.execute_script('arguments[0].click();', e)

        # 口座名取得
        browser.wait_element((By.CSS_SELECTOR, '[nblabel="口座名"]'))
        num = len(browser.find_elements_by_css_selector('[nblabel="口座名"] li'))
        result = []
        for i in range(0, num):
            e = browser.find_element_by_css_selector('[nblabel="口座名"]')
            e.click()
            e = e.find_elements_by_css_selector('li')[i]
            subname = e.text
            e.click()

            name = 'ordinary'
            if i > 0:
                name = name + '_' + subname
            result.append({
                'name': name,
                'unit': 'Yen',
                'account': '普通',
                'history': self.__get_ordinary_sub(browser),
            })

        # print(result)

        # ホームへ戻る
        browser.find_element_by_link_text('ホーム').click()
        # wait for display
        browser.wait_for_title_changed()
        browser.wait_for_loaded()
        browser.wait_element((By.LINK_TEXT, '円普通預金'))

        return result

    def __get_ordinary_sub(self, browser):
        browser.wait_element((By.PARTIAL_LINK_TEXT, '並び替え')).click()
        browser.find_element_by_xpath('//label[contains(text(),"期間指定")]').click()

        e = browser.find_elements_by_css_selector('.m-formSelectDate')[0]
        e.find_element_by_css_selector('p.m-select-year nb-simple-select').click()
        e.find_elements_by_css_selector('p.m-select-year li')[1].click()
        e.find_element_by_css_selector('p.m-select-month nb-simple-select').click()
        e.find_elements_by_css_selector('p.m-select-month li')[1].click()
        e.find_element_by_css_selector('p.m-select-day nb-simple-select').click()
        e.find_elements_by_css_selector('p.m-select-day li')[1].click()

        # 表示
        browser.find_elements_by_link_text('表示')[1].click()

        # wait for update
        browser.find_elements_by_partial_link_text('明細ダウンロード')

        data = []
#        import pdb; pdb.set_trace()

        while True:

            soup = BeautifulSoup(browser.page_source, "html.parser")

            for row in soup.select('.m-tblDetailsBox'):
                date = row.select('.m-date')[0].string
                desc = row.select('.m-subject span')[0].string
                deposit = self._decode_amount(row.select('.m-txtEx')[0].string)
                if row.select('.m-sign')[0].string == '出':
                    deposit = -deposit
                balance = self._decode_amount(row.select('.m-txtEx')[1].string)

                item = {'date' : self.__decode_date(date),
                        'price': 1,
                        'amount' : deposit,
                        'payout' : deposit,
                        'desc' : desc,
                        'balance' : balance
                }

#                print(item)

                # Prepend.
                # Detail list is sorted by descending order
                # Passbook order is ascending
                data.insert(0, item)

            # 次へリンクがあるかチェック
            browser.implicitly_wait(0)
            es = 0
            try:
                es = browser.find_element_by_css_selector('.m-pager-prev')
            except NoSuchElementException:
#                print("no entry")
                break
            browser.implicitly_wait(180)

            next_page = es.text
            es.click()

            # wait for update
            while browser.find_element_by_class_name('m-counter').text.split(' ')[0] != next_page:
                sleep(0.1)

        return data

    def __get_time_deposit(self, browser):

        browser.implicitly_wait(0)
        es = 0
        try:
            es = browser.find_element_by_link_text('円定期預金')
        except NoSuchElementException:
            print("no entry")
            return None
        browser.implicitly_wait(180)
        es.click()
        self.wait_until_blocked(browser)
        sleep(0.5)

        # 取引履歴
        browser.find_element_by_link_text('取引履歴').click()

        # 口座名取得
#        browser.wait_element((By.CSS_SELECTOR, '[nblabel="口座名"]'))
        num = len(browser.find_elements_by_css_selector('[nblabel="口座名"] li'))
        result = []
        for i in range(0, num):
            # 口座切り替え
            browser.wait_element((By.PARTIAL_LINK_TEXT, '並び替え')).click()
            e = browser.find_element_by_css_selector('[nblabel="口座名"]')
            e.click()
            e = e.find_elements_by_css_selector('li')[i]
            subname = e.text
            e.click()
            browser.find_element_by_partial_link_text('表示').click()

            # 更新待ち
            browser.wait_element((By.PARTIAL_LINK_TEXT, '並び替え'))

            name = 'time_deposit'
            if i > 0:
                name = name + '_' + subname
            result.append({
                'name': name,
                'unit': 'Yen',
                'account': '普通',
                'history': self.__get_time_deposit_sub(browser),
            })

        # print(result)

        # ホームへ戻る
        browser.find_element_by_link_text('ホーム').click()
        # wait for display
        browser.wait_for_title_changed()
        browser.wait_for_loaded()
        browser.wait_element((By.LINK_TEXT, '円普通預金'))

        return result

    def __get_time_deposit_sub(self, browser):
        data = []
        balance = 0

        soup = BeautifulSoup(browser.page_source, "html.parser")
        for row in soup.select('tr'):
            c = [x for x in row.select('th p')[0].stripped_strings]
            date = self.__decode_date(c[0])
            desc = ' '.join(c[1:])

            c = [x for x in row.select('td .m-txtEx')[0].stripped_strings]
            deposit = self._decode_amount(c[1])
            if c[0] == '出':
                deposit = -deposit

            balance += deposit
            item = {'date' : date,
                    'price': 1,
                    'amount' : deposit,
                    'payout' : deposit,
                    'desc' : desc,
                    'balance' : balance
            }
#            print(item)
            data.append(item)

        return data
