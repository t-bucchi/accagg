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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

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
        return "ShinseiBank"

    @classmethod
    def login_info(self):
        return {'USRID': 'ID',
                'PASSWORD': '暗証番号'}

    def _decode_date(self, str):
        match = re.match(r"^(\d{4})/(\d{2})/(\d{2})$", str)
        if match:
            y = int(match.group(1))
            m = int(match.group(2))
            d = int(match.group(3))
            return date(y, m, d)

    def _decode_amount(self, str):
        return int('0' + str.replace(',', '').replace('円', ''))

    def wait_until_blocked(self, b):
        for i in range(1, 100):
            e = b.wait_for_item((By.CSS_SELECTOR, '.block-ui-container'))
            if e.size['height'] == 0:
                break
            sleep(0.1)

    def run(self, login_info):
        URL = "https://bk.shinseibank.com/SFC/apps/services/www/SFC/desktopbrowser/default/login?mode=1&forward=SA0001"

#        import pdb; pdb.set_trace()
        browser = Browser(webdriver.Firefox())
        browser.implicitly_wait(180)

        # open URL
        browser.get(URL)
        browser.wait_for_loaded()

        # enter
        browser.sync_send_keys((By.NAME, 'nationalId'), login_info['USRID'])
        browser.sync_send_keys((By.NAME, 'password'), login_info['PASSWORD'])

        # Click login
        browser.wait_element((By.TAG_NAME, 'button.ng-scope')).click()
        browser.wait_for_title_changed()

        # 一度トップへ飛ばす
        self.wait_until_blocked(browser)
        browser.wait_element((By.CSS_SELECTOR, 'a[ui-sref="top"]')).click();

        # サマリー画面
        self.wait_until_blocked(browser)

        # 口座情報
        browser.wait_element((By.PARTIAL_LINK_TEXT, '口座情報'));
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        browser.find_elements(By.PARTIAL_LINK_TEXT, '口座情報')[-1].click();
#        browser.wait_for_title_changed()
        browser.wait_for_loaded()

#        import pdb; pdb.set_trace()

        # 日付取得
        for i in range(1, 50):
            text = browser.find_element_by_css_selector('section.balance header .revised').text
            if text != "":
                break
            sleep(0.1)

        today = self._decode_date(text.split(' ')[0])

        # 定期預金
        section = browser.find_element_by_css_selector('section[ng-show="isDisplayRegularAccountTotal"]')

        result = {}
        data = []
        item = {'date' : today,
                'deposit' : 0,
                'desc' : "円定期預金",
                'balance' : self._decode_amount(section.find_element_by_tag_name('dd').text)
        }
        data.append(item)
        result['time_deposit'] = data

        # 投資信託
        section = browser.find_element_by_css_selector('section[ng-show="isDisplayLcymfFunds"]')

        rows = section.find_elements_by_tag_name('tr')
        for row in rows:
            if '保有口数' in row.text:
                continue
            cols = row.find_elements_by_tag_name('td')
            data = []

            item = {'date' : today,
                    'deposit' : 0,
                    'desc' : '',
                    'currency' : cols[0].text,
                    'unit' : self._decode_amount(cols[1].text.split('\n')[0]),
                    'balance' : self._decode_amount(cols[5].text)
            }
            data.append(item)
            result['fund_' + cols[0].text] = data

        # 残高
        browser.wait_element((By.PARTIAL_LINK_TEXT, '入出金明細'));
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        browser.find_elements(By.PARTIAL_LINK_TEXT, '入出金明細')[-1].click();
#        browser.wait_for_title_changed()
        browser.wait_for_loaded()

        # 普通預金入金明細
        browser.wait_element((By.ID, 'endDate')).click()
        ## 現日付取得
        date = browser.wait_element((By.ID, 'endDate')).get_attribute("value")
        date = '%04d/%s/01' % (int(date[0:4]) - 2, date[5:7])
        ## 取得範囲設定
        browser.find_element_by_id('beginDate').send_keys(Keys.CONTROL, "a")
        browser.find_element_by_id('beginDate').send_keys(Keys.DELETE)
        browser.sync_send_keys((By.ID, 'beginDate'), date)

        ## 照会
        browser.wait_element((By.CSS_SELECTOR, 'button.ng-binding')).click()

        # 照会ボタン disable 待ち
        WebDriverWait(browser, 20).until(
            lambda driver: driver.find_element_by_css_selector('button.ng-binding').is_enabled() == False
        )

        # 照会ボタン enable 待ち
        WebDriverWait(browser, 20).until(
            lambda driver: driver.find_element_by_css_selector('button.ng-binding').is_enabled() == True
        )

#        import pdb; pdb.set_trace()

        data = []

        while True:
            for item in browser.find_elements_by_css_selector('table.balanceDetails > tbody > tr'):
                # print(item.get_attribute('innerHTML'))
                cols = item.find_elements_by_tag_name('td')
                c = [x.text for x in cols]
#               print(c)
                item = {'date' : self._decode_date(c[0]),
                        'deposit' : self._decode_amount(c[3])
                        - self._decode_amount(c[2]),
                        'desc' : c[1],
                        'balance' : self._decode_amount(c[4])
                }
#               print('\t'.join(item))

                # Prepend.
                # Detail list is sorted by descending order
                # Passbook order is ascending
                data.insert(0, item)

            # pagerのテキストを取得
            page_li = browser.find_element_by_css_selector('.pager li:nth-child(3)')
            current_page = page_li.text

            next_link = browser.find_element_by_css_selector('li.next > a')
            if 'ng-hide' in next_link.get_attribute('class'):
                # 次のxx件が無いので終了
                break
            # 次をクリック
            next_link.click()

            # pager が切り替わるまで待つ
            WebDriverWait(browser, 20).until(
                lambda driver: driver.find_element_by_css_selector('.pager li:nth-child(3)').text != current_page
            )

        result['ordinary'] = data

        browser.quit()
        return result
