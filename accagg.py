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
from accagg.passbook import PassBook, PassBookManager
from accagg.passwordmanager import PasswordManager
from accagg.fund import Fund
import datetime

def aggregate(account):
    aggregator = accagg.bank.Factory.aggregator(account['BANKID'])
    all_data = aggregator.run(account)
    #print(all_data)
    if not all_data:
        return

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

    fund = Fund()

    # new format
    for data in all_data:
        history = data.pop('history')
        passbook = PassBook(account['name'], data)
        if data['unit'] != 'Yen' and data['unit'] != 'Fund':
            if 'unitid' in data:
                pass
            elif 'unitid' in passbook.info:
                data['unitid'] = passbook.info['unitid']
            else:
                print("Getting fund id...")
                ids = fund.search(data['unit'])
                if ids == None:
                    print("%s is not found." % data['unit'])
                elif len(ids) == 1:
                    data['unitid'] = ids[0]['id']
                else:
                    print("some ids found.")

            if 'unitid' in data:
                print("Update fund info...")
                info = fund.getinfo(data['unitid'])
                data['class'] = info['class']
                data['price'] = info['price'] / 10000
                data['lastdate'] = info['lastdate']

        data['bankid'] = aggregator.bankid()
        data['bankname'] = aggregator.description()

        passbook.add(history, info = data)
        if data['unit'] != 'Yen' and data['unit'] != 'Fund' and not 'unitid' in passbook.info:
            ids = fund.search(data['unit'])
            if len(ids) == 1:
                data['unitid'] = ids[0]['id']
            else:
                print("some ids found.\n")
        passbook.save()

    # Remove cancelled account
    names = [data['name'] for data in all_data]
    for i in [i[1] for i in PassBookManager.find() if i[0] == account['name']]:
        if i in names or i in i.replace('/', '／'):
            continue

        passbook = PassBook(account['name'], i)
        if passbook.data[-1]['balance'] == 0:
            continue

        print("%s:%s had been already cancelled. set 'balance' to 0"
            % (data['name'], i))
        passbook.add([{
            'date': datetime.date.today(),
            'price': 0,
            'amount': 0,
            'balance': 0,
            'payout': 0,
            'desc': 'CANCELLED (AUTO ADDED)',
        }])
        passbook.save()

password = PasswordManager()

for name in password.list():
    print("Aggregate " + name)
    account = password.get(name)
    if (account.get('disabled')):
        print(" ...disabled");
        continue
    aggregate(account)
