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

import csv
import datetime

class PassBook(object):
    def __init__(self, bankid, type):
        self.__data = []
        self.__bankid = bankid
        self.__type = type
        self.load()

    @property
    def bankid(self):
        return self.__bankid

    @property
    def type(self):
        return self.__type

    def add(self, items):
        if len(self.__data) == 0:
            self.__data = items
            return

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
        print('id:{} type:{}\n'.format(self.__bankid, self.__type))
        print(self.__data)

    def __filename(self):
        return self.__bankid + '-' + self.__type + '.csv';

    def save(self):
        with open(self.__filename(), 'w') as f:
            writer = csv.writer(f, quoting = csv.QUOTE_NONNUMERIC)
            for i in self.__data:
                writer.writerow([i['date'], i['deposit'],
                                 i['balance'], i['desc']]);

    def load(self):
        self.__data = [];
        try:
            with open(self.__filename(), 'r') as f:
                reader = csv.reader(f)
                for i in reader:
                    date = i[0].split('-')
                    data = {'date': datetime.date(int(date[0]), int(date[1]), int(date[2])),
                            'deposit': int(i[1]),
                            'balance': int(i[2]),
                            'desc': i[3]}
                    self.__data.append(data)
        except IOError:
            pass

if __name__ == '__main__':
    book = PassBook('hoge', 'test')
    book.dump()
    book.add([{'date': datetime.date(2018, 1, 1), 'deposit': 1, 'desc': 'desc', 'balance': 1}])
    book.add([{'date': datetime.date(2018, 1, 1), 'deposit': 1, 'desc': 'desc', 'balance': 2}])
    book.add([{'date': datetime.date(2018, 1, 1), 'deposit': 1, 'desc': 'desc', 'balance': 1},
              {'date': datetime.date(2018, 1, 1), 'deposit': 1, 'desc': 'desc', 'balance': 2},
              {'date': datetime.date(2018, 1, 1), 'deposit': 1, 'desc': 'desc', 'balance': 3}])
    book.add([{'date': datetime.date(2018, 1, 1), 'deposit': 1, 'desc': 'desc', 'balance': 2},
              {'date': datetime.date(2018, 1, 1), 'deposit': 1, 'desc': 'desc', 'balance': 3},
              {'date': datetime.date(2018, 1, 1), 'deposit': 1, 'desc': 'desc', 'balance': 4},
    ])
    book.add([{'date': datetime.date(2018, 1, 1), 'deposit': 1, 'desc': 'desc', 'balance': 4},
              {'date': datetime.date(2018, 1, 1), 'deposit': 1, 'desc': 'desc', 'balance': 5},
              {'date': datetime.date(2018, 1, 1), 'deposit': 1, 'desc': 'desc', 'balance': 6},
    ])
    book.add([{'date': datetime.date(2017, 1, 1), 'deposit': 1, 'desc': 'desc', 'balance': 1}])
    book.add([{'date': datetime.date(2017, 1, 1), 'deposit': 1, 'desc': 'desc', 'balance': 1}])
    book.dump()
    book.save()
