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

import csv
import datetime
import glob
import re

class PassBook(object):

    def __init__(self, accountid, bankinfo):
        self.__data = []
        self.__accountid = accountid
        if type(bankinfo) is str:
            self.__info = {'name': bankinfo}
        else:
            self.__info = bankinfo
        self.load()

    @property
    def accountid(self):
        return self.__accountid

    @property
    def name(self):
        return self.__info['name']

    @property
    def type(self):
        return self.__info['account']

    @property
    def info(self):
        return self.__info

    def add(self, items, info = None):
        if len(self.__data) == 0:
            self.__data = items
            return

        if info:
            self.__info = info

        new_data = []
        while len(self.__data) > 0 and len(items) > 0:
            d = self.__data[0]
            i = items[0]
#            print('----')
#            print(d)
#            print(i)
            if i == d:
                new_data.append(d)
                self.__data.pop(0)
                items.pop(0)
            elif d['date'] <= i['date']:
                new_data.append(self.__data.pop(0))
            else:
                new_data.append(items.pop(0))

        for d in self.__data:
            new_data.append(d)
        for i in items:
            new_data.append(i)
        self.__data = new_data

    def dump(self):
        print('id:{} name:{} type:{}\n'.format(self.__accountid,
            self.name, self.type))
        print(self.__data)

    def __filename(self):
        return self.accountid + '-' + self.name + '.csv';

    def save(self):
        with open(self.__filename(), 'w') as f:
            writer = csv.writer(f, quoting = csv.QUOTE_NONNUMERIC)
            for key, val in self.__info.items():
                writer.writerow([key, val])
            writer.writerow(['==='])
            for i in self.__data:
                writer.writerow([i['date'], i['price'], i['amount'], i['payout'],
                                 i['balance'], i['desc']]);

    def __parse_csv(self, cols):
        date = cols[0].split('-')
        return {'date': datetime.date(int(date[0]), int(date[1]), int(date[2])),
                'price': cols[1],
                'amount': cols[2],
                'payout': cols[3],
                'balance': cols[4],
                'desc': cols[5]}

    def __parse_old_csv(self, cols):
        date = cols[0].split('-')
        return {'date': datetime.date(int(date[0]), int(date[1]), int(date[2])),
                'price': 1,
                'amount': cols[1],
                'payout': cols[1],
                'balance': cols[2],
                'desc': cols[3]}

    def load(self):
        self.__data = []
        parser = self.__parse_csv   # to support old format
        try:
            with open(self.__filename(), 'r') as f:
                old_info = self.__info
                self.__info = {}
                reader = csv.reader(f, quoting = csv.QUOTE_NONNUMERIC)

                for i in reader:
                    # old format
                    if len(i) > 2:
                        parser = self.__parse_old_csv
                        self.__data.append(parser(i))
                        self.__info = old_info
                        break

                    if i[0] == '===':
                        break
                    self.__info[i[0]] = i[1]

                for i in reader:
                    self.__data.append(parser(i))

        except IOError:
            pass

class PassBookManager(object):
    @classmethod
    def find(self):
        # for csv
        result = []
        for file in glob.glob("*.csv"):
            m = re.match('(\S+?)-(\S+)\.csv', file)
            if not m or m[1] == "fundlog":
                continue

            print(m[1]+" "+m[2])
            result.append((m[1], m[2]))
        return result
