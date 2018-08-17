#!/usr/bin/python3

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

import accagg.bank
from accagg.passbook import PassBook
from accagg.passwordmanager import PasswordManager

name = 'SMBC'

password = PasswordManager()
account = password.get(name)
aggregator = accagg.bank.Factory.aggregator(account['BANKID'])
all_data = aggregator.run(account)
#print(all_data)

for account in all_data:
#    print(account)
    passbook = PassBook(name, account)
    passbook.add(all_data[account])
    passbook.save()
