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

from .fund import Fund

import glob
import re
import csv
import datetime

class FundLog:
    @classmethod
    def list_ids(self):
        result = []
        for i in glob.glob("fundlog-*.csv"):
            m = re.match('fundlog-(\S+)\.csv', i)
            result.append(m.groups()[0])
        return result

    def __init__(self, id):
        self.__id = id
        self.__filename = 'fundlog-%s.csv' % id
        self.__log = []

    @property
    def id(self):
        return self.__id

    @property
    def log(self):
        if len(self.__log) == 0:
            self.__load()
        return self.__log

    def __load(self):
        self.__log = []
        try:
            with open(self.__filename, 'r') as f:
#                import pdb; pdb.set_trace()
                reader = csv.reader(f, quoting = csv.QUOTE_NONNUMERIC)

                for i in reader:
                    date = i[0].split('-')
                    item = {'date': datetime.date(int(date[0]), int(date[1]), int(date[2])),
                            'price': int(i[1])}
                    self.__log.append(item)
        except FileNotFoundError:
            pass

    def update(self):
        fund = Fund()
        log = fund.price_log(self.__id)
        if len(log) == 0:
            return

        self.__log = log

        with open(self.__filename, 'w') as f:
            writer = csv.writer(f, quoting = csv.QUOTE_NONNUMERIC)
            for i in log:
                writer.writerow([i['date'], i['price']]);

if __name__ == '__main__':
    print(FundLog.list_ids())
    f = FundLog("JP90C0003PR7")
    print(f.log)
    f.update()
    print(f.log)
