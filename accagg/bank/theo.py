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

import json

class Aggregator(Aggregator):
    @classmethod
    def bankid(self):
        return self.__module__.split('.')[-1]

    @classmethod
    def description(self):
        return "THEO"

    @classmethod
    def login_info(self):
        return {'EMAIL': 'メールアドレス',
                'PASSWORD': 'パスワード'}

    def _decode_date(self, str):
        match = re.match(r"^(\d+)[/\-](\d+)[/\-](\d+)$", str)
        if match:
            y = int(match.group(1))
            m = int(match.group(2))
            d = int(match.group(3))
            return date(y, m, d)

    def run(self, login_info, lastdate):
        URL = "https://app.theo.blue/account/login"

        browser = Browser.firefox()
        browser.implicitly_wait(3)

        # open URL
        browser.get(URL)
        browser.wait_for_loaded()

#        import pdb; pdb.set_trace()

        # メンテナンス中なら停止
        try:
            es = browser.find_element_by_tag_name("h1")
        except NoSuchElementException:
            pass
        else:
            if 'メンテナンス' in es.text:
                browser.quit()
                return

        # enter
        browser.sync_send_keys((By.NAME, 'email'), login_info['EMAIL'])
        browser.sync_send_keys((By.NAME, 'password'), login_info['PASSWORD'])

        # Click login
        browser.find_elements_by_tag_name('button')[-1].click();
        # wait for loading
        browser.wait_for_title_changed()

        # Inject XHR hook
        browser.execute_script("""
        (function(XHR) {
          "use strict";

          var element = document.createElement('div');
          element.id = "interceptedResponse";
          element.appendChild(document.createTextNode(""));
          document.body.appendChild(element);

          var open = XHR.prototype.open;
          var send = XHR.prototype.send;

          XHR.prototype.open = function(method, url, async, user, pass) {
            this._url = url; // want to track the url requested
            open.call(this, method, url, async, user, pass);
          };

          XHR.prototype.send = function(data) {
            var self = this;
            var oldOnReadyStateChange;
            var url = this._url;

            function onReadyStateChange() {
              if(url == '/customer/portfolio-statuses' &&
                self.status === 200 && self.readyState == 4 /* complete */) {
                document.getElementById("interceptedResponse").innerHTML = self.responseText;
              }
              if(oldOnReadyStateChange) {
                oldOnReadyStateChange();
              }
            }

            if(this.addEventListener) {
              this.addEventListener("readystatechange", onReadyStateChange,
                false);
            } else {
              oldOnReadyStateChange = this.onreadystatechange;
              this.onreadystatechange = onReadyStateChange;
            }
            send.call(this, data);
          }
        })(XMLHttpRequest);
        """)
        print("wait\n")

        # ログイン後画面

        data = []

        timeout = 100
        while timeout > 0:
            js = browser.find_element_by_id('interceptedResponse').get_attribute('innerHTML')
            if js != '':
                break
            sleep(0.1)
            timeout -= 1
        else:
            print("error\n")
            return

        # import pdb; pdb.set_trace()

        items = json.loads(js)

        deposit = 0
        for i in items['result']:
            date = self._decode_date(i['date'])

            item = {'date' : date,
                    'amount' : int(i['jpy']['depositAmount']),
                    'payout' : int(i['jpy']['depositAmount']) - deposit,
                    'desc' : '',
                    'balance' : int(i['jpy']['marketAmount']),
                    'price': 1
            }
            data.append(item)
            deposit = int(i['jpy']['depositAmount'])

#        print(data)
#            item['balance'] = balance

        browser.quit()
        return [{
            'name': 'THEO',
            'unit': 'Fund',
            'account': '特定',
            'class': 'バランス',
            'price': 1,
            'payout': data[-1]['amount'],
            'lastdate': data[-1]['date'],
            'history': data,
        }]
