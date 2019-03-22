#!/usr/bin/python3

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

import accagg.bank
from accagg.passbook import PassBook
from accagg.passwordmanager import PasswordManager

def aggregate(account):
    aggregator = accagg.bank.Factory.aggregator(account['BANKID'])
    all_data = aggregator.run(account)
    #print(all_data)

    # old format
    if type(all_data) is dict:
        # Convert to new format

        new_data = []
        for name, data in all_data.items():
            meta = {
                'name': name,
                'unit': 'Yen',
                'account': '普通',
                'history': []}
            for i in data:
                item = {
                    'date': i['date'],
                    'price': 1,
                    'amount': i['deposit'],
                    'payout': i['deposit'],
                    'balance': i['balance'],
                    'desc': i['desc'],
                }
                meta['history'].append(item)
            new_data.append(meta)
        all_data = new_data

    # new format
    for data in all_data:
        history = data.pop('history')
        passbook = PassBook(account['name'], data)
        passbook.add(history, info = data)
        passbook.save()

password = PasswordManager()

for name in password.list():
    print("Aggregate " + name)
    account = password.get(name)
    if (account.get('disabled')):
        print(" ...disabled");
        continue
    aggregate(account)
