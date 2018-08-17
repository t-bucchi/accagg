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

from configparser import ConfigParser

class PasswordManager:
    def __init__(self, filename = 'accagg.dat'):
        self.__parser = ConfigParser()
        self.__parser.optionxform = str # to case sensitve
        self.__filename = filename
        self.__parser.read(self.__filename)

    def get(self, name):
        items = {'name': name}
        for item in self.__parser.items(name):
            items[item[0]] = item[1]
        return items
