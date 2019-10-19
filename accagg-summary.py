#!/usr/bin/python3

import plotly
import plotly.plotly as py
import plotly.graph_objs as go
import accagg.passbook as pb
import re
from pprint import pprint
import sys
import copy

# import pdb; pdb.set_trace()

acc = pb.PassBookManager.find()
book = []
total = 0

# 全PassBook を走査して book リストに情報を読み込む
for i in acc:
    b = pb.PassBook(i[0], i[1])

    info = b.info
    # print(info)
    if info['unit'] == 'Yen':
        price = 1
        class_ = '日本円'
        payout = b.data[-1]['balance']
    else:
        price = info['price']
        class_ = info['class']
        payout = info['payout']

    last = b.data[-1]['balance'] * price
    if last == 0:
        continue

    name = info['name']
    if 'ordinary' in name:
        name = '普通預金' + name[8:]
    if 'time_deposit' in name:
        name = '定期預金' + name[12:]

    book.append({
#        'bankname': info['bankname'],
        'bankname': i[0],
        'name': name,
        'class': class_,
        'value': last,
        'payout': payout,
        'profit': last - payout,
        'balance': b.data[-1]['balance'],
    })
    total += last

class Asset:
    asset = {}
    book = []
    parent = {
        '非リスク資産': None,
        'リスク資産': None,
        '株式': 'リスク資産',
        '債券': 'リスク資産',
        'REIT': 'リスク資産',
        'その他': 'リスク資産',
        'バランス': 'リスク資産',
        '金': 'リスク資産',
        '日本円': '非リスク資産',
        '国内REIT': 'REIT',
        '海外REIT': 'REIT',
    }

    @classmethod
    def round_class(self, str):
        str = str.split('（')[0]
        if str == '先進国・新興国株式':
            str = '全世界株式'
        elif str[0:6] == '複合商品型-':
            str = 'バランス'
        elif str[0:4] == '金関連-':
            str = '金'
        elif str[0:6] == '国内債券型-':
            str = '国内債券'
        elif str[0:6] == '国内株式型-':
            str = '国内株式'
        elif str == '国際株式型-エマージング株式型':
            str = '新興国株式'
        elif str == '国際株式型-グローバル株式型':
            str = '先進国株式'
        return str

    def __get_parent(self, str):
        if str in self.parent.keys():
            return self.parent[str]
        if '株式' in str:
            self.parent[str] = '株式'
            return '株式'
        if '債券' in str:
            self.parent[str] = '債券'
            return '債券'
        if 'fund_' in str:
            self.parent[str] = 'その他'
            return 'その他'
        self.parent[str] = None
        return None

    def __add_sub(self, id, class_, value, profit, balance, payout):
        if not id in self.asset:
            self.asset[id] = {'label':class_, 'value':0, 'profit':0, 'balance':0, 'payout':0}
        self.asset[id]['value'] += value
        self.asset[id]['profit'] += profit
        self.asset[id]['balance'] += balance
        self.asset[id]['payout'] += payout

        parent = self.__get_parent(id)
        # print('id:%s class:%s value:%s parent:%s profit:%s' %
        #     (id, class_, value, parent, profit))
        if parent:
            self.__add_sub(parent, parent, value, profit, balance, payout)

    def add(self, book):
        value = int(book['value'])
        class_ = self.round_class(book['class'])
        id = book['name']
        name = book['name']
        if 'fund_' in name:
            class_ = 'その他'
            name = name[5:]
        self.parent[id] = class_
        if '預金' in book['name']:
            newid = '%s-%s' % (book['bankname'], name)
            self.parent[newid] = id
            id = newid
            name = book['bankname']
        self.__add_sub(id, name, value, book['profit'], book['balance'], book['payout'])

    def tree(self, parent=None):
        children = [x for x in self.parent if self.parent[x] == parent]
        result = []
        for x in children:
            if x in self.asset:
                a = copy.deepcopy(self.asset[x])
                a['children'] = self.tree(x)
                a['name'] = x
                result.append(a)
        return result


asset = Asset()

for i in book:
    asset.add(i)

pprint(asset.tree())

d = {
    'labels': ['Total'],
    'parents': [None],
    'values': [total],
    'text': ['{:,d}'.format(int(total))],
    'hover': [''],
    'ids': ['Total'],
}

for k, v in asset.asset.items():
    # print(k)
    # print(asset.parent[k])
    # pprint(v)
    value = v['value']
    profit = v['profit']

    d['ids'].append(k)
    d['labels'].append(v['label'])
    if asset.parent[k]:
        d['parents'].append(asset.parent[k])
    else:
        d['parents'].append('Total')
    d['values'].append(value)
    d['text'].append('{:,d}<br />{:.2f}%'.format(int(value), value / total * 100))
    if value - profit == 0:
        d['hover'].append('{:+,d}<br />--%'.format(int(profit)))
    else:
        d['hover'].append('{:+,d}<br />{:+.2f}%'.format(int(profit), profit / (value - profit) * 100))

trace = go.Sunburst(
    ids=d['ids'],
    labels=d['labels'],
    parents=d['parents'],
    values=d['values'],
    branchvalues="total",
    outsidetextfont = {"size": 20, "color": "#377eb8"},
    marker = {"line": {"width": 2}},
    text = d['text'],
    hovertext = d['hover'],
)

layout = go.Layout(
    margin = go.layout.Margin(t=0, l=0, r=0, b=0)
)

plotly.offline.plot(go.Figure([trace], layout), filename='basic_sunburst_chart_total_branchvalues.html')
#print(plotly.offline.plot(go.Figure([trace], layout), include_plotlyjs=True, output_type='div'))
