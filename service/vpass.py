#! /usr/bin/python
# -*- coding: utf-8 -*-

from peewee import *
import requests
from pyquery import PyQuery as pq
import ConfigParser
from model.meisai import Meisai
import re
import datetime
from pushbullet import PushBullet

config = ConfigParser.RawConfigParser()

config.read('app.cfg')
api_key = config.get("pushbullet", "api_key")
user_id = config.get("service.vpass", "user_id")
password = config.get("service.vpass", "password")

pb = PushBullet(api_key)

class Vpass():

    @staticmethod
    def totalize():
        client = requests.Session()

        base_url = "https://www.smbc-card.com"

        login_url = "https://www.smbc-card.com/vp/xt_login.do?strURL=https%3A%2F%2Fwww%2Esmbc-card%2Ecom%2Fmem%2Fvps%2Findex%2Ejsp"
        r = client.post(login_url, {"userid": user_id, "password": password})

        # meisai
        meisai_url = "https://www.smbc-card.com/vp/web_meisai/web_meisai_top.do"
        r = client.get(meisai_url)

        pq_html = pq(r.text)

        pq_pull_down_date = pq(pq_html.find("td.bdc td.sdbc2 span.s3")[1])
        pull_down_date = re.sub(r'(\n|\r|\t|\(.\))', "", pq_pull_down_date.text())
        pull_down_date = re.sub(u'年(\d)月', u"年0\\1月", pull_down_date)
        pull_down_date = re.sub(u'月(\d)日', u"月0\\1日", pull_down_date)
        pull_down_date = re.sub(u'年', "-", pull_down_date)
        pull_down_date = re.sub(u'月', "-", pull_down_date)
        pull_down_date = re.sub(u'日', "", pull_down_date)

        pull_down_date = datetime.datetime.strptime(pull_down_date, "%Y-%m-%d")

        pq_csv_a = pq_html.find('td.sc20 span.s3 a')

        csv_url = pq_csv_a.attr('href')

        r = client.get(base_url + csv_url)
        r.encoding = 'shift-jis'

        csv = r.text
        csv_rows = csv.split("\n")

        cnt = 0
        add_rows = []
        for csv_row in csv_rows:

            cnt += 1

            fields = csv_row.split(',')

            if cnt == 1:
                continue
            if len(fields) <= 6:
                continue
            if not fields[0]:
                continue

            use_date = datetime.datetime.strptime(fields[0], "%Y/%m/%d")
            content = fields[1]
            amount = fields[5]

            row = Meisai.get_meisai(pull_down_date, use_date, content, amount)

            if row.count() < 1:
                meisai = Meisai()
                meisai.pull_down_date = pull_down_date
                meisai.use_date = use_date
                meisai.content = content
                meisai.amount = amount
                meisai.save()

                add_rows.append(meisai)

        if len(add_rows) > 0:
            # sum monthly amount
            month_amount = Meisai.get_month_amount(pull_down_date)
            text = ""
            for add_row in add_rows:
                text += add_row.use_date.strftime("%Y-%m-%d") + "\t" + add_row.content + "\t" + add_row.amount  + "\n"
            text += "month_amount: " + str(month_amount[0])

            # notify pushbullet
            success, push = pb.push_note(pull_down_date, text)
