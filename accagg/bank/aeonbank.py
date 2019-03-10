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

from ..browser import Browser

import re
from datetime import date
from time import sleep

class Aggregator(Aggregator):
    @classmethod
    def bankid(self):
        return self.__module__.split('.')[-1]

    @classmethod
    def description(self):
        return "AEON Bank"

    @classmethod
    def login_info(self):
        return {'USRID': 'ID',
                'PASSWORD': '暗証番号'}

    def __decode_date(self, str):
        match = re.match(r"^(\d{4})年(\d{2})月(\d{2})日$", str)
        if match:
            y = int(match.group(1))
            m = int(match.group(2))
            d = int(match.group(3))
            return date(y, m, d)

    def __decode_amount(self, str):
        return int('0' + str.replace(',', '').replace('円', ''))

    def run(self, login_info):
        URL = "https://www.aeonbank.co.jp/login/ib_02.html"

        browser = Browser(webdriver.Firefox())
        browser.implicitly_wait(3)

        # open URL
        browser.get(URL)

        # enter
        browser.sync_send_keys((By.NAME, 'cntrId'), login_info['USRID'])
        browser.sync_send_keys((By.ID, 'scndPinNmbr'), login_info['PASSWORD'])

        # Click login
        browser.find_element_by_id("btn_lgon").click();

        # wait for loading
        browser.wait_for_loaded()

        # 秘密の質問
        try:
            text = browser.find_element_by_id('title010').text
            if text == '合言葉認証':
                text = browser.find_element_by_css_selector('.InputTableStyle1 td:nth-of-type(1)').text.strip()
#                print(text)
#                import pdb; pdb.set_trace()
                answer = ""
                if text == login_info['Q1']:
                    answer = login_info['A1']
                elif text == login_info['Q2']:
                    answer = login_info['A2']
                elif text == login_info['Q3']:
                    answer = login_info['A3']
                else:
                    raise ValueError("Secret question is not match")
                browser.sync_send_keys((By.ID, 'wcwdAskRspo'), answer)

                # 通常利用する端末として登録しない
                browser.find_element_by_id('actvTmnlMsge2').click()
                # 次へ
                browser.find_element_by_id('butn01').click()

        except NoSuchElementException:
#            print("no entry")
            pass
        else:
            pass

        # 期限切れなら次へをクリック
        try:
            browser.implicitly_wait(0.1)
            es = browser.find_elements_by_name("btnNext")
            browser.implicitly_wait(3)
        except NoSuchElementException:
            print("no entry")
        else:
            if len(es) > 0:
                es[0].click()

        # wait
        browser.wait_for_loaded()

        # ログイン後画面

        ## 明細照会をクリック
        browser.find_element_by_css_selector(".CenterButnArea > input:nth-of-type(1)").click()
        browser.wait_for_loaded()

        # 残高照会画面

        count = len(browser.find_elements_by_css_selector(u'input[value="明細照会"]'))
        result = {}
        for i in range(count):
            browser.find_elements_by_css_selector(u'input[value="明細照会"]')[i].click()
            browser.wait_for_loaded()

            h1 = browser.find_element_by_tag_name('h1').text
            if h1 == '入出金明細照会':
                # 普通預金
                data = self.__get_ordinary(browser)
#                print(data)
                result['ordinary'] = data
            elif h1 == '定期預金明細照会':
                # 定期預金
                data = self.__get_time_deposit(browser)
#                print(data)
                result['time_deposit'] = data

        browser.quit()
        return result

    def __get_ordinary(self, browser):
        # 明細ページ
        ## 全期間を指定
        browser.find_element_by_id('dspyCondInqrTerm0').click()
        ## 「照会」を押下
        browser.find_element_by_id('gropButn3').click()

        data = []

        while True:
            for item in browser.find_elements_by_css_selector('table.MaxWidth.stripe-table tr'):
                if '日付' in item.text:
                    continue
                cols = item.find_elements_by_tag_name('td')
                item = {'date' : self.__decode_date(cols[0].text),
                        'deposit' : self.__decode_amount(cols[3].text)
                        - self.__decode_amount(cols[2].text),
                        'desc' : cols[1].text,
                        'balance' : self.__decode_amount(cols[4].text)
                }

                # prepend.
                data.insert(0, item)

            if not '次の' in browser.find_element_by_css_selector('p.page').text:
                # 次のxx件が無いので終了
                break
            browser.find_element_by_id('aftrPage2').click()

        ## 明細ページに戻る
        # scroll to bottom
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);");
        browser.find_elements_by_xpath('//a[contains(./text(), "口座一覧・残高照会")]')[-1].click()
        return data

    def __get_time_deposit(self, browser):
        # 預金明細

        data = []
#        import pdb; pdb.set_trace()

        # 解約明細
        browser.find_element_by_link_text("解約明細").click()

        # ページ切り替え待ち
        for i in range(1, 20):
            e = browser.wait_for_item((By.TAG_NAME, 'h1'))
#            print(e.text)
            if '解約明細' in e.text:
                break
            sleep(0.5)

#001 | スーパー定期 | 2017年06月09日 | 12カ月 | xxx円 | 年 0.050%
#    | 　　　　　　 | 2018年06月09日 |        |       |   満期
#    |    年 0.050% |          yyy円 |  zzz円 | 0円
#
# date:2017/6/9, deposit: xxx, balance:xxx desc: スーパー定期
# date:2018/6/9, deposit: zzz, balance:xxx+zzz desc: スーパー定期
# date:2018/6/9, deposit: -xxx-zzz, balance:0 desc: スーパー定期

        current_date = browser.find_element_by_css_selector('p.TimeStamp').text
        current_date = self.__decode_date(re.sub(r'時点.*', '', current_date))

        while True:
            item = {}
            deposit = 0
            end_date = 0
            sub_data = []
            for row in browser.find_elements_by_css_selector('table.fixdDtilTable tr'):

                # 表のヘッダ部分をスキップ
                if row.get_attribute('class') == 'center':
                    continue

                # 3行の場所を特定
                pos = 'bottom'
                if 'class="Top"' in row.get_attribute('innerHTML'):
                    pos = 'top'
                if 'class="Middle"' in row.get_attribute('innerHTML'):
                    pos = 'middle'

                cols = row.find_elements_by_tag_name('td')
                if pos == 'top':
                    deposit = self.__decode_amount(cols[4].text)
                    item = {'date' : self.__decode_date(cols[2].text),
                            'deposit' : deposit,
                            'desc' : cols[1].text,
                            'balance' : 0
                    }
                    sub_data = [item]
                elif pos == 'middle':
                    end_date = self.__decode_date(cols[0].text)
                else:
                    if end_date <= current_date:
                        interest = self.__decode_amount(cols[2].text)
                        item = {'date' : end_date,
                                'deposit' : interest,
                                'desc' : '',
                                'balance' : 0
                        }
                        sub_data.append(item)
                        item = {'date' : end_date,
                                'deposit' : -deposit - interest,
                                'desc' : '',
                                'balance' : 0
                        }
                        sub_data.append(item)
                        data[0:0] = sub_data  # prepend
                        sub_data = []
#                        print(data)
            break

        # 預入明細
        browser.find_element_by_link_text("預入明細").click()

        # ページ切り替え待ち
        for i in range(1, 20):
            e = browser.wait_for_item((By.TAG_NAME, 'h1'))
#            print(e.text)
            if '定期預金明細' in e.text:
                break
            sleep(0.5)

        while True:
            item = {}
            deposit = 0
            for row in browser.find_elements_by_css_selector('table.fixdDtilTable tr'):
                if '預入番号' in row.text:
                    continue
                if '満期日' in row.text:
                    continue
                top = False
                if 'class="Top"' in row.get_attribute('innerHTML'):
                    top = True

                # 明細なし
                cols = row.find_elements_by_tag_name('td')
                if len(cols) == 1:
                    continue

                if top:
                    deposit = self.__decode_amount(cols[4].text)
                    item = {'date' : self.__decode_date(cols[2].text),
                            'deposit' : deposit,
                            'desc' : cols[1].text,
                            'balance' : 0
                    }
                    data.append(item)
                else:
                    end_data = self.__decode_date(cols[0].text)
                    if end_date <= current_date:
                        item = {'date' : self.__decode_date(cols[0].text),
                                'deposit' : -deposit,
                                'desc' : '',
                                'balance' : 0
                        }
                        data.append(item)
#                print(data)
            break

        ## 明細ページに戻る
        # scroll to bottom
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);");
        browser.find_elements_by_xpath('//a[contains(./text(), "口座一覧・残高照会")]')[-1].click()

        data = sorted(data, key=lambda item: item['date'])
        balance = 0
        for item in data:
            balance += item['deposit']
            item['balance'] = balance

        return data
