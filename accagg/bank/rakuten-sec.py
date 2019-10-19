# coding: utf-8
#
# This file is part of accagg.
#
# Copyright (C) 2019 bucchi <bucchi79@gmail.com>
#
#  accagg is free software: you can redistribute it and/or modify
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
from bs4 import BeautifulSoup

from accagg.browser import Browser

from time import sleep

import re
from datetime import date

from pprint import pprint

class Aggregator(Aggregator):
    @classmethod
    def bankid(self):
        return self.__module__.split('.')[-1]

    @classmethod
    def description(self):
        return "Rakuten証券"

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

    def _decode_number(self, str):
#        print(str)
        return int('0' + re.sub(r'[,\-円口]', '', str))

    def run(self, login_info, lastdate):
        URL = "https://www.rakuten-sec.co.jp/"

        browser = Browser.firefox()
        browser.implicitly_wait(5)

        # open URL
        browser.get(URL)
        browser.wait_for_loaded()

#        import pdb; pdb.set_trace()

        es = browser.find_elements_by_name('loginid')
        if len(es) == 0:
            return
        browser.implicitly_wait(0.1)

        # enter
        browser.sync_send_keys((By.NAME, 'loginid'), login_info['USRID'])
        browser.sync_send_keys((By.NAME, 'passwd'), login_info['PASSWORD'])

        # Click login
        browser.find_element_by_css_selector('form[name=loginform] button').click()
#        browser.wait_for_title_changed()
        browser.wait_for_item((By.CLASS_NAME, 'copyright'))

        # 現在の保有商品取得
        # 口座管理→保有商品一覧
        browser.find_element_by_id('nav-main-menu').find_element_by_link_text('口座管理').click()
        browser.wait_for_item((By.PARTIAL_LINK_TEXT, '保有商品一覧を確認する')).click()
#        print("保有商品一覧")
        browser.wait_for_loaded()

        # 投信タブをクリック
        # FIXME: ここでクリックできないことが多い
        browser.wait_for_item((By.CLASS_NAME, 'copyright'))
        sleep(0.5)
        browser.find_element_by_id('str-main').find_element_by_link_text('投信').click()
#        print("投信")

        browser.wait_for_item((By.CLASS_NAME, 'copyright'))
        position = {}

        soup = BeautifulSoup(browser.page_source, "html.parser")
#        import pdb; pdb.set_trace()

        for table in soup.select('table [id*="poss-tbl-"]'):
            id = table['id']
            if id == 'poss-tbl-sp':
                account = '特定'
            elif id == 'poss-tbl-nisa':
                account = 'NISA'
            elif id == 'poss-tbl-tnisa':
                account = 'つみたてNISA'
            else:
                account = '普通'

            for row in table.find_all('tr', attrs={'align':'right'}):
                cols = [str.strip(x.text) for x in row.find_all('td')]

                    # ['', 'ＳＢＩ・全世界株式インデックス・ファンド(雪だるま（全世界株式）)', '再投資型',
                #  '73,497 口', '', '73,497 口', '9,895.10 円\n72,726 円',
                #  '10,244 円\n+35 円\n+203 円', '75,290 円\n+2,564 円\n+3.52 %',
                #  '+2,564 円', '', '+2,564 円', '詳細',
                #  '4\n\n3410857\n\n\n\n\n  \n\n4\n\n3410857', '']

                meta = {'name': cols[1], # 商品名
                        'unit': cols[1], # 単位
                        'account': account, # 口座種別
                        'balance': self._decode_number(cols[3]), # 所持口数
#                        'payout': self._decode_number(re.sub(r'.*\n', '', cols[6])),
                        'history': [],
                }
                # position[(meta['name'], meta['account')] = meta
                if (meta['name']) in position:
                    meta['balance'] += position[(meta['name'])]['balance']
                position[(meta['name'])] = meta

#        pprint(position)
        # import pdb; pdb.set_trace()

        # 取引履歴
        browser.find_element_by_id('nav-main-menu').find_element_by_link_text('口座管理').click()

        browser.find_element_by_partial_link_text('取引履歴を見る').click()

        # 投資信託タブ
        browser.find_element_by_link_text('投資信託').click()

        all_img = browser.find_elements_by_css_selector('img[alt="すべて"]')
        # 表示期間: すべて
        if not 'display: none' in all_img[0].get_attribute('outerHTML'):
            all_img[0].click()

        # ファンド種別: すべて
        if not 'display: none' in all_img[2].get_attribute('outerHTML'):
            all_img[2].click()

        # Submit
        browser.find_element_by_css_selector('input.roll').click()

        while True:
            soup = BeautifulSoup(browser.page_source, "html.parser")
            for row in soup.find('table', class_='tbl-data-01').find_all('tr'):
                if row.td is None:
                    continue

                cols = [str.strip(x.text) for x in row.find_all('td')]
#                print(cols)

                # [0], [1]約定日, [2]受渡日,
                # [3]ファンド名, [4]分配金,
                # [5]口座, [6]取引, [7]買付方法, [8]数量 [9]単価, [10]経費,
                # [11]受渡金額[円], [12]
                # [' ', '2019/03/20', '2019/03/27',
                #  '＜購入・換金手数料なし＞ニッセイ 外国株式インデックスファンド', '再投資型',
                # 'つみたてNISA', '買付', '積立', '63 口', '15,832', '0',
                # '100', '円']

                payout = self._decode_number(re.sub(r'\(.*\)', '', cols[11]))
                name = cols[3]
                amount = self._decode_number(cols[8])
                item = {'date' : self.__decode_date(cols[1]),
                        'price' : self._decode_number(cols[9])/10000,
                        'amount' : amount,
                        'payout' : payout,
                        'desc' : cols[7],
                }

#                index = (name, cols[5])
                index = (name)
                if not index in position:
                    # position にない場合は position を追加
                    meta = {'name': name,
                            'unit': name,
                            'account': cols[3],
                            'balance': 0,
#                            'payout': 0,
                            'history': [],
                    }
                    position[index] = meta

                position[index]['history'].append(item)

            browser.implicitly_wait(0.1)
            es = browser.find_elements_by_partial_link_text("次の")
            if len(es) == 0:
                break
            browser.implicitly_wait(30)
            es[0].click()

#            pprint(position)
        # import pdb; pdb.set_trace()

        for index in position.keys():
            balance = position[index].pop('balance')
            payout = 0
            for item in position[index]['history'][::-1]:
                item['balance'] = balance
                balance -= item['amount']
                payout += item['payout']
            position[index]['payout'] = payout

#        pprint(position)

        browser.quit()
        return [position[i] for i in position.keys()]
