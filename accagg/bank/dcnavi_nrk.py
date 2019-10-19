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
from selenium.common.exceptions import TimeoutException
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

    def __decode_date(self, str):
        match = re.match(r"(\d{4})/(\d+)/(\d+)", str)
        if match:
            y = int(match.group(1))
            m = int(match.group(2))
            d = int(match.group(3))
            return date(y, m, d)

    def __decode_amount(self, str):
        return int('0' + str.replace(',', '').replace('円', ''))

    def __fixupname(self, name):
        if name[-3:] == '・野村':
            name = name[:-3]
        if name == 'ＤＣ日本株式インデックスＬ':
            name = 'ＤＣ日本株式インデックスファンドＬ'
        return name

    def run(self, login_info, lastdate):
        URL = "https://www.j-pec.co.jp/dcnavi/u010login/g00101.do"

        profile = FirefoxProfile()
        profile.set_preference('general.useragent.override', 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko')
        profile.set_preference('permissions.default.image', 2)
        profile.set_preference('gfx.downloadable_fonts.enabled', False)

        browser = Browser(webdriver.Firefox(firefox_profile=profile))
        browser.implicitly_wait(180)

        # open URL
        browser.get(URL)
        browser.wait_for_loaded()

        # import pdb; pdb.set_trace()

        # メンテナンス
        if 'メンテナンス中' in browser.find_element_by_tag_name('html').text:
            return []

        browser.find_element_by_id('dcnvToNrkLogin').click();

        # enter
        browser.sync_send_keys((By.ID, 'loginAccount'), login_info['USRID'])
        browser.sync_send_keys((By.ID, 'loginPasswd'), login_info['PASSWORD'])

        # Click login
        browser.wait_element((By.ID, 'nrkLoginLinkForPcAuto')).click()
        browser.wait_for_loaded()

        # check already logged in
        if '同じユーザーIDで利用されています' in browser.page_source:
            browser.sync_send_keys((By.CSS_SELECTOR, 'input[name="userId"]'), login_info['USRID'])
            browser.sync_send_keys((By.CSS_SELECTOR, 'input[name="password"]'), login_info['PASSWORD'])
            browser.find_element_by_css_selector('input[type="SUBMIT"]').click()
            browser.wait_for_loaded()

        # トップ
        # 表示待ち
        browser.wait_element((By.CSS_SELECTOR, '.linkTypeNormal a'))
        browser.wait_for_loaded()

        browser.implicitly_wait(1)
        try:
            browser.find_element_by_id('modal-close').click()
        except NoSuchElementException:
            pass
        except TimeoutException:
            pass

        browser.implicitly_wait(180)

        browser.execute_script('$("div.rkBnrBlock").removeClass("rkBnrBlock")')
        browser.execute_script('$("a[target=\\"_blank\\"]").removeAttr("target")')
        browser.execute_script('$(".externalLink").removeClass("externalLink")')

        # NRK のページへ
        browser.execute_script('$("img[alt*=\\"NRK\\"]").parent().text("NRK")')
        browser.find_element_by_link_text('NRK').click()

        # ここからNRKのページ
        browser.wait_for_loaded()

        # 「資産評価額照会」ページへ
        browser.find_element_by_partial_link_text('資産評価額照会').click()

        #
        date = self.__decode_date(browser.find_elements_by_class_name('dateInq')[0].text)

        result = []
        # 現在の商品を取得
        es = browser.find_elements_by_class_name('infoDetailUnit_02')
        for e in es:
            item = e.find_elements_by_tag_name('dd')
            cols = [i.text for i in item]
            # 商品名,商品分類,数量,基準価額,解約価額,
            # 資産評価額,解約時評価額,取得価額累計,損益,資産比率

            # print(cols)

            if cols[1] == '国内投信':
                name = self.__fixupname(cols[0])
                unit = name
                balance = self.__decode_amount(cols[2])
            else:
                name = cols[0]
                unit = 'Yen'
                balance = self.__decode_amount(cols[5])

            result.append({
                'name': name,
                'unit': unit,
                'account': 'DC',
                'payout': self.__decode_amount(cols[7]),
                'lastdate': date,
                'history': [{
                    'date' : date,
                    'price' : 0,
                    'amount' : 0,
                    'payout' : 0,
                    'balance' : balance,
                    'desc' : '',
                    }],
            })

        browser.find_element_by_link_text('ログアウト').click()
        browser.quit()
        return result
