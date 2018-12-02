# accagg

## このソフト何？

銀行のネットバンキングに自動でログインし、取引明細などの口座情報を抽出するソフトです。いわゆる[アカウントアグリゲーション](https://ja.wikipedia.org/wiki/%E3%82%A2%E3%82%AB%E3%82%A6%E3%83%B3%E3%83%88%E3%82%A2%E3%82%B0%E3%83%AA%E3%82%B2%E3%83%BC%E3%82%B7%E3%83%A7%E3%83%B3)を行うソフトです。

マネーフォワード や Zaim 、 MoneyLook のようなものをイメージしてもらえばわかりやすいと思いますが、そこまでの機能は目指していません。まずは、銀行の明細を取得するためのスクレイピング機能を開発しています。ゆくゆくはグラフ表示とかできるといいですけどね。

## できること

今は明細の取得と更新のみです。取得した明細はcsv形式で保存することができます。
csv形式であれば、スクリプトで集計したり、表計算ソフトでグラフ化したりが容易になります。

既に取得済みの場合は過去のcsvに更新された明細のみが追加されます。

## 注意点・制限事項

現在はパスワードなどのログイン情報、取得した明細データは平文で保存されます。
そのため、**これらの情報の保護の責任は使用者にあります**。

マルチユーザの環境や、管理者が他にいるようなPC/サーバ(要するに自由にファイルを見ることができる第三者がいるような環境)では使わないでください。自分専用の個人PCでの使用を推奨します。

## 対応銀行

少しづつ増やしていければいいなと思っています。

* [三井住友銀行](/doc/bank-smbc.md)
* [イオン銀行](/doc/bank-aeonbank.md)
* [住信SBIネット銀行](/doc/bank-sbinetbank.md)
* [新生銀行](/doc/bank-shinseibank.md)
* [THEO](/doc/bank-theo.md)
* [WealthNavi for 住信SBIネット銀行](/doc/bank-wealthnavi-for-sbi.md)

# 使い方
## 必要な環境

* python3
* selenium
* BeautifulSoup (※一部の銀行のみ)
* webdriver ([Firefox](https://github.com/mozilla/geckodriver/releases))

Ubuntu 18.04 の場合は、python3 と selenium は以下のコマンドでインストールできます。

~~~
$ sudo apt-get install python3 python3-pip
$ pip3 install selenium
~~~

Firefox の [webdriver](https://github.com/mozilla/geckodriver/releases) はダウンロード後、パスの通った場所にコピーしてください。

たとえば、 展開後の geckodriver を \~/bin にコピーして、\~/bin にパスを通してください。

## 設定

accagg-template.dat を参考に、 accagg.dat を作成します。
accagg.dat は以下のような形式で書かれています。

~~~
[SMBC]
BANKID=smbc
USRID1=01234
USRID2=56789
PASSWORD=1111
~~~

上記例では "SMBC" がアカウント名(任意の文字列)です。BANKID に使用するアグリゲータの bankid を指定します。ここまでは必須項目です。

それ以外は銀行毎に必要な情報が異なります。詳細は各銀行のドキュメントを参照下さい。

## ライセンス

AGPLv3.0 で公開しています。ライセンス全文は LICENSE を参照ください。

## 免責

このソフトウェアの使用で生じたいかなる損害も作者は責任を負いません。
ご自身の責任で使用してください。

銀行の情報を扱うため、コードが信頼できるかどうかをご自身で判断してご使用ください。
