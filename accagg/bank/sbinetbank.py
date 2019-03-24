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
        match = re.match(r"^(\d{4})/(\d{2})/(\d{2})$", str)
        if match:
            y = int(match.group(1))
            m = int(match.group(2))
            d = int(match.group(3))
            return date(y, m, d)

    def _decode_amount(self, str):
        return int('0' + str.replace(',', '').replace('円', ''))

    def wait_until_blocked(self, b):
        for i in range(1, 20):
            e = b.wait_for_item((By.CSS_SELECTOR, '.block-ui-container'))
            print(e.size)
            if e.size['height'] == 0:
                break
            sleep(0.5)

    def run(self, login_info):
        URL = "https://www.netbk.co.jp"

        browser = Browser.firefox()
        browser.implicitly_wait(180)

        # open URL
        browser.get(URL)
        browser.wait_for_loaded()

#        import pdb; pdb.set_trace()

        # enter
        browser.sync_send_keys((By.NAME, 'userName'), login_info['USRID'])
        browser.sync_send_keys((By.NAME, 'loginPwdSet'), login_info['PASSWORD'])

        # Click login
        browser.find_element_by_css_selector('input[alt="ログイン"]').click()
#        browser.wait_for_title_changed()

        # 確認 (次へを押す)
        browser.wait_element((By.CSS_SELECTOR, 'input.button-m01')).click()

        # ホーム

        result = {}
        # 普通預金
        data = self.__get_ordinary(browser)
        result['ordinary'] = data

        # 円定期預金
        data = self.__get_time_deposit(browser)
        result['time_deposit'] = data

        browser.quit()
        return result

    def __get_ordinary(self, browser):
        # 入出金明細
        browser.find_element_by_id('main').find_element_by_link_text('入出金明細').click()

#        import pdb; pdb.set_trace()
        #
        browser.find_element_by_id('CD020202VALUE05').click()
        Select(browser.find_element_by_css_selector('select[name="dsplyTrmSpcfdYearFrom"]')).select_by_index(0)
        Select(browser.find_element_by_css_selector('select[name="dsplyTrmSpcfdMonthFrom"]')).select_by_index(0)
        Select(browser.find_element_by_css_selector('select[name="dsplyTrmSpcfdDayFrom"]')).select_by_index(0)

        # 表示
        browser.find_element_by_css_selector('input[value="表示"]').click()

        data = []
#        import pdb; pdb.set_trace()

        while True:

            for item in browser.find_elements_by_css_selector('div.tableb02 table > tbody > tr'):
#                print(item.get_attribute('innerHTML'))
                cols = item.find_elements_by_tag_name('td')
                c = [x.text for x in cols]
#               print(c)
                item = {'date' : self.__decode_date(c[0]),
                        'deposit' : self._decode_amount(c[3])
                        - self._decode_amount(c[2]),
                        'desc' : c[1],
                        'balance' : self._decode_amount(c[4])
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
                es = browser.find_element_by_link_text("次へ→")
            except NoSuchElementException:
#                print("no entry")
                break
            browser.implicitly_wait(180)

            es.click()

        # ホームへ戻る
        browser.find_element_by_id('globalFoot').find_element_by_link_text('ホーム').click()

        return data

    def __get_time_deposit(self, browser):
        # 入出金明細
        actions = ActionChains(browser)
        actions.move_to_element(browser.find_element_by_link_text('口座情報')).perform()
        sleep(0.5)
        browser.wait_for_item((By.LINK_TEXT, '残高照会（口座別）')).click()
        browser.find_element_by_link_text('取引履歴').click()

#        browser.find_element_by_link_text('残高照会（口座別）').click()

        data = []
        balance = 0
        for item in browser.find_elements_by_css_selector('.tableb02 table > tbody > tr'):
#                print(item.get_attribute('innerHTML'))
            cols = item.find_elements_by_tag_name('td')
            c = [x.text for x in cols]
#               print(c)

            if len(c) > 2:
                # Top
                deposit = self._decode_amount(c[3])
                balance += deposit
                item = {'date' : self.__decode_date(c[0]),
                        'deposit' : deposit,
                        'desc' : c[1],
                        'balance' : balance
                }
#                print(item)
                data.append(item)

        return data
