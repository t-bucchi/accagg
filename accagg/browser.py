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

import requests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from time import sleep

class Browser(object):
    def __init__(self, webdriver):
        self.driver = webdriver

    # webdriver のメソッドはそのまま透過
    def __getattr__(self, name):
        if hasattr(self.driver, name):
            return getattr(self.driver, name)
        raise AttributeError

    @classmethod
    def firefox(self):
        profile = webdriver.FirefoxProfile()
        # 1 - Allow all images
        # 2 - Block all images
        # 3 - Block 3rd party images
        profile.set_preference('permissions.default.image', 2)
        profile.set_preference('gfx.downloadable_fonts.enabled', False)
        return Browser(webdriver.Firefox(firefox_profile = profile))

    def download(self, url):
        ua = {'User-agent': self.execute_script("return navigator.userAgent")}
        #print(ua)

        session = requests.Session()
        cookies = self.get_cookies()

        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'])
            #print(cookie['name'], cookie['value'])

        #print(url)
        response = session.get(url, headers = ua)
        #print(response.status_code)
        #print(response.content)
        #print(response.headers)
        return response.content

    def sync_send_keys(self, locator, key):
        # wait for element
        WebDriverWait(self, 120).until(
            EC.element_to_be_clickable(locator)
        )
        # send keys
        self.find_element(locator[0], locator[1]).send_keys(key)
        # wait for update
        WebDriverWait(self, 30).until(
            EC.text_to_be_present_in_element_value(locator, key)
        )

    def wait_for_loaded(self):
#        print("wait_for_loaded: start")
#        self.driver.find_element_by_tag_name("html")
        WebDriverWait(self, 20).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
#        print(self.execute_script("return document.readyState"))
#        print("wait_for_loaded: end")

    def wait_for_item(self, locator):
        WebDriverWait(self, 20).until(
            EC.presence_of_element_located(locator)
        )
        return self.find_element(locator[0], locator[1])

    def wait_element(self, locator):
        # wait for element
        WebDriverWait(self, 30).until(
            EC.element_to_be_clickable(locator)
        )
        return self.find_element(locator[0], locator[1])

    def wait_for_title_changed(self):
        org_title = self.title
#        print(org_title)
        for i in range(1, 20):
#            print(self.title)
            if org_title != self.title:
                break
            sleep(0.5)
