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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select

from bs4 import BeautifulSoup

from accagg.browser import Browser

from time import sleep
import unicodedata

import re
import datetime
from pprint import pprint

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
                'PASSWORD': 'パワーダイレクトパスワード',
                'PASSNUMBER': '暗証番号'}

    def __decode_date(self, str):
        match = re.match(r"^(\d{4})/(\d{2})/(\d{2})$", str)
        if match:
            y = int(match.group(1))
            m = int(match.group(2))
            d = int(match.group(3))
            return datetime.date(y, m, d)

    def __decode_amount(self, str):
        str = str.replace(',', '').replace('円', '')
        if str == '':
            return 0
        if str[0] != '-':
            str = '0' + str
        return int(str)

    def __decode_number(self, str):
#        print(str)
        return int('0' + re.sub(r'[,\-円口]', '', str))

    def wait_until_blocked(self, b, _css = '.block-ui-container'):
        for i in range(1, 100):
            e = b.wait_for_item((By.CSS_SELECTOR, _css))
            if e.size['height'] == 0:
                break
            sleep(0.1)
        sleep(0.1)

    def run(self, login_info):
        URL = "https://bk.shinseibank.com/SFC/apps/services/www/SFC/desktopbrowser/default/login?mode=1&forward=SA0001"

#        import pdb; pdb.set_trace()
        browser = Browser.firefox()
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

        # import pdb; pdb.set_trace()

        # 日付取得
        for i in range(1, 50):
            text = browser.find_element_by_css_selector('section.balance header .revised').text
            if text != "":
                break
            sleep(0.1)

        today = self.__decode_date(text.split(' ')[0])

        result = []

        # 普通預金
        data = self.__get_ordinary(browser)
        if data:
            result.extend(data)

        # 投資信託
        data = self.__get_fund(browser, login_info, today)
        if data:
            result.extend(data)

        browser.quit()
        # pprint(result)
        return result

        # 定期預金
        # section = browser.find_element_by_css_selector('section[ng-show="isDisplayRegularAccountTotal"]')
        #
        # data = []
        # item = {'date' : today,
        #         'deposit' : 0,
        #         'desc' : "円定期預金",
        #         'balance' : self.__decode_amount(section.find_element_by_tag_name('dd').text)
        # }
        # data.append(item)
        # result['time_deposit'] = data

        # 投資信託
        # section = browser.find_element_by_css_selector('section[ng-show="isDisplayLcymfFunds"]')
        #
        # rows = section.find_elements_by_tag_name('tr')
        # for row in rows:
        #     if '保有口数' in row.text:
        #         continue
        #     cols = row.find_elements_by_tag_name('td')
        #     data = []
        #
        #     item = {'date' : today,
        #             'deposit' : 0,
        #             'desc' : '',
        #             'currency' : cols[0].text,
        #             'unit' : self.__decode_amount(cols[1].text.split('\n')[0]),
        #             'balance' : self.__decode_amount(cols[5].text)
        #     }
        #     data.append(item)
        #     result['fund_' + cols[0].text] = data

    # 普通預金
    def __get_ordinary(self, browser):
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

            soup = BeautifulSoup(browser.page_source, "html.parser")

            for row in soup.find('table', class_='balanceDetails').tbody.find_all('tr'):

                c = [i.text for i in row.find_all('td')]
                # print(c)
                deposit = self.__decode_amount(c[3]) - self.__decode_amount(c[2])
                item = {'date' : self.__decode_date(c[0]),
                        'price' : 1,
                        'amount' : deposit,
                        'payout' : deposit,
                        'desc' : c[1],
                        'balance' : self.__decode_amount(c[4])
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

        browser.find_element_by_link_text('トップ').click()
        browser.wait_for_loaded()
        self.wait_until_blocked(browser, '.block-ui-overlay')

        return [{
            'name': 'ordinary',
            'unit': 'Yen',
            'account': '普通',
            'history': data,
        }]

    # 投資信託
    def __get_fund(self, browser, login_info, today):
        # 投資信託
        # import pdb; pdb.set_trace()

        ## 「投資信託のお取引」クリック
        browser.find_element_by_link_text('投資信託のお取引').click()
        browser.wait_for_loaded()
        self.wait_until_blocked(browser, '.block-ui-overlay')
        sleep(0.3)

        ## 「お取引・照会」ボタンクリック
        e = browser.wait_element((By.XPATH, '//button[contains(./text(),"お取引・照会")]'))
        sleep(0.1)
        self.wait_until_blocked(browser, '.block-ui-overlay')
        e.click()
        self.wait_until_blocked(browser)

        ## 「確認」ボタンクリック
        browser.implicitly_wait(0.2)
        browser.wait_for_loaded()
        browser.wait_element((By.XPATH, '//button[contains(./text(),"確認")]'))
        while True:
            e = browser.find_elements_by_xpath('//button[contains(./text(),"確認")]')
            if len(e) > 0:
                e[0].click()
                break

        self.wait_until_blocked(browser)
        browser.implicitly_wait(30)

        ## 暗証番号入力
        browser.sync_send_keys((By.ID, 'pin'), login_info['PASSNUMBER'])
        browser.find_element_by_xpath('//button[contains(.,"実行")]').click()

        # ここで別ウィンドウが開く
        # 開くまで待つ
        WebDriverWait(browser, 3).until(lambda d: len(d.window_handles) > 1)

        # 操作ウインドウ切り替え
        browser.switch_to.window(browser.window_handles[-1])
        # print("change window\n")
        browser.wait_for_loaded()
        browser.wait_for_item((By.ID, 'foot'))
        # print(browser.find_element_by_tag_name("html").text)

        # 大切なお知らせがあったら飛ばす
        browser.implicitly_wait(0.2)
        if len(browser.find_elements_by_xpath('//h2[contains(.,"お知らせ")]')) > 0:
            # 「次の画面へ」をクリック
            # print("お知らせ\n")
            browser.find_element_by_id('button').click()
#            browser.wait_for_loaded()

        browser.implicitly_wait(30)
        browser.find_element_by_link_text('各種変更・照会').click()
        # print("各種変更・照会 click")
        browser.find_element_by_link_text('保有残高照会').click()
        # print("保有残高照会 click")

        # 全ての「詳細開」をクリック
        browser.implicitly_wait(0.1)
        # for open_button in browser.find_elements_by_css_selector('table.typeE2 .open1 a'):
        #     open_button.click()

        # サマリ取得
        position = {}
        balance = {}
        for row in browser.find_elements_by_css_selector('table.typeE2 tr'):
            if len(row.find_elements_by_tag_name('td')) == 0:
                continue

            cols = [ e.text for e in row.find_elements_by_tag_name('td') ]

            if len(cols) == 3:
                # ['1', '野村ｲﾝﾃﾞｯｸｽﾌｧﾝﾄﾞ・日経225/Funds-i  ', '購 入\n解 約\nお受取']
                name = unicodedata.normalize('NFKC', cols[1].strip())
                meta = {'name': name,
                        'unit': name,
                        'history': [],
                }
            elif len(cols) == 8:
                # ['NISA口座\n適用年別', '149,271口', '23,447.29円\n23,448円', '23,587円\n23,587円\n（1万口当り）', '352,086円\n2,075円', '350,000円\n0円', '2,086円', '再投資']
                # ['合計\n詳細開\n詳細閉', '1,154,954口', '6,068.04円\n-', '5,705円\n5,705円\n（1万口当り）', '658,901円\n-43,141円', '700,000円\n0円', '-41,099円', '再投資']
#                meta['account'] = cols[0].split('\n')[0]
                meta['account'] = '総合'
                meta['balance'] = self.__decode_number(cols[1])
                meta['payout'] = self.__decode_number(cols[5].split('\n')[0])
                meta['price'] = self.__decode_number(cols[3].split('\n')[0])/10000
                meta['lastdate'] = today
#                position[(meta['name'], meta['account'])] = meta
                position[meta['name']] = meta
                balance[meta['name']] = meta['balance']
            # elif len(cols) == 10:
            #     # ['', 'NISA口座\n適用年別', '1,132,325口', '6,068.04円\n6,081円', '5,705円\n5,705円\n（1万口当り）', '645,991円\n-42,575円', '-\n-', '-', '', '解 約']
            #     account = cols[1].split('\n')[0]
            #     if account == '合計':
            #         continue
            #     meta['balance'] = self.__decode_amount(col[2])
            #     meta['payout'] = self.__decode_numer(col[5].split('\n')[0])
            #     position[(meta['name'], meta['account'])] = meta


        # pprint(position)

        # 取引履歴
        browser.find_element_by_link_text('取引履歴照会').click()

        browser.implicitly_wait(30)
        txt = browser.find_element_by_css_selector('.txt-notes').text
        match = re.match(r'.*?(\d{4})年(\d+)月(\d+)日', txt)
        y = int(match.group(1))
        m = int(match.group(2))
        d = int(match.group(3))

        Select(browser.find_element_by_id('year_1')).select_by_index(0)
        Select(browser.find_element_by_id('month_1')).select_by_index(m-1)
        Select(browser.find_element_by_id('date_1')).select_by_index(d-1)

        oldest_date = datetime.date(y, m, d)

        browser.find_element_by_link_text('表示条件変更').click()
        browser.wait_for_loaded()

        # 明細取得
        browser.implicitly_wait(0.1)

        while True:
            soup = BeautifulSoup(browser.page_source, "html.parser")

            for row in soup.find('table', class_='typeE2').find_all('tr'):
                if not row.td:
                    continue

                cols = [re.sub(r'\s*\n\s*', '\n', e.text.strip()) for e in row.find_all('td')]
                # print(cols)

                if len(cols) == 5:
                    # ['1', '2019/07/26\n2019/07/29', '購入\nNISA預り', '国内籍\n-', '野村ｲﾝﾃﾞｯｸｽﾌｧﾝﾄﾞ･外国株式･為替ﾍｯｼﾞ型/Funds-i']
                    # ['2', '2019/03/11\n\n2019/03/12', '再投資\n\n特定口座', '国内籍\n\n-', 'BAMﾜｰﾙﾄﾞ･ﾎﾞﾝﾄﾞ&ｶﾚﾝｼｰ･ﾌｧﾝﾄﾞ(毎月決算型)\n（愛称：ウィンドミル）']
                    name = cols[4].replace('\n', ' ')
                    name = unicodedata.normalize('NFKC', name)
                    date = self.__decode_date(cols[1].split('\n')[0])
                    desc = cols[2].split('\n')[0]
                    if '分配金' in desc:
                        name = None

                elif len(cols) == 6 and name:
                    # ['58,012口\n17,238円', '100,000円\n0円', '', '', '100,000円', 'NISA優先（WEB）']
                    # ['81口\n5,614円', '45円', '', '', '45円', ''
                    amount = self.__decode_number(cols[0].split('\n')[0])
                    price = self.__decode_number(cols[0].split('\n')[1]) / 10000
                    payout = self.__decode_number(cols[4].split('\n')[0])

                    if desc == '解約':
                        amount = -amount
                        payout = -payout

                    if not name in balance:
                        # 既に解約済み
                        balance[name] = 0
                        meta = {'name': name,
                                'unit': name,
                                'history': [],
                                'account': '総合',
                                'balance': 0,
                                'payout': 0,
                                'price': 0,
                                'lastdate': date,
                        }
                        position[meta['name']] = meta

                    item = {'date': date,
                            'price': price,
                            'amount': amount,
                            'payout': payout,
                            'balance': balance[name],
                            'desc': desc,
                    }

                    # print(item)
                    position[name]['history'].insert(0, item)
                    balance[name] -= amount

            # 次の10件
            if not '次の10件' in browser.find_element_by_class_name('pageNumbersT').text:
                break

            browser.find_element_by_link_text('次の10件').click()
            browser.wait_for_loaded()

        # pprint(position)

        result = [i for i in position.values()]
        for fund in result:
            if len(fund['history']) > 0:
                continue
            item = {'date': oldest_date,
                    'price': 0,
                    'amount': 0,
                    'payout': 0,
                    'balance': fund['balance'],
                    'desc': '(繰り越し)',
            }
            fund['history'].append(item)

        browser.close()
        browser.switch_to.window(browser.window_handles[0])
        browser.find_element_by_link_text('トップ').click()
        browser.wait_for_loaded()
        return result
