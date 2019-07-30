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

from .fundinfo import Rakuten, Minkabu

class Fund:
    def __init__(self):
        self.scraper = []
        self.scraper.append(Rakuten())
        self.scraper.append(Minkabu())

    def search(self, str):
        for s in self.scraper:
            result = s.search(str)
            if result:
                for i in result:
                    i['id'] = s.id() + '-' + i['id']
                return result
        return None

    def getinfo(self, id):
        i = id.find('-')
        if i < 0:
            return None

        s_id = id[0:i]
        for s in self.scraper:
            if s.id() != s_id:
                continue
            return s.getinfo(id[i+1:])
        return None
