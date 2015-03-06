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

        login_url = "https://www.smbc-card.com/vp/xt_login.do?strURL=https%3A%2F%2Fwww%2Esmbc-card%2Ecom%2Fmem%2Fvps%2Findex%2Ejsp"
        r = client.post(login_url, {"userid": user_id, "password": password})

        # this month's
        meisai_url = "https://www.smbc-card.com/vp/web_meisai/web_meisai_top.do"

        cpage = Vpass.CurrentPage(meisai_url, client)
        Vpass.totalize_month(cpage)

        # next month's
        nextdate = cpage.get_next_pull_down_date()
        meisai_url = "https://www.smbc-card.com/vp/web_meisai/web_meisai_top.do?p01=" + nextdate
        npage = Vpass.NextPage(meisai_url, client)
        Vpass.totalize_month(npage)


    @staticmethod
    def totalize_month(page):

        rows = page.get_cvs_records()

        pull_down_date = page.get_pull_down_date()
        add_rows = []
        for row in rows:

            use_date = row[0]
            content = row[1]
            amount = row[2]

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
            text = "month_amount: " + str(month_amount[0]) + "\n" + text

            # notify pushbullet
            success, push = pb.push_note(pull_down_date.strftime('%Y-%m-%d pulldown update') + datetime.datetime.now().strftime('(%Y-%m-%d %H:%M:%S)'), text)

        return pull_down_date


    class CurrentPage():

        def __init__(self, url, client):

            res = client.get(url)
            self.res = res
            self.client = client
            self.pq_html = pq(res.text)
            pq_pull_down_date = pq(self.pq_html.find("td.bdc td.sdbc2 span.s3")[1])
            pull_down_date = re.sub(r'(\n|\r|\t|\(.\))', "", pq_pull_down_date.text())
            pull_down_date = re.sub(u'年(\d)月', u"年0\\1月", pull_down_date)
            pull_down_date = re.sub(u'月(\d)日', u"月0\\1日", pull_down_date)
            pull_down_date = re.sub(u'年', "-", pull_down_date)
            pull_down_date = re.sub(u'月', "-", pull_down_date)
            pull_down_date = re.sub(u'日', "", pull_down_date)
            pull_down_date = datetime.datetime.strptime(pull_down_date, "%Y-%m-%d")
            self.pull_down_date = pull_down_date

        def get_pull_down_date(self):
            return self.pull_down_date

        def get_next_pull_down_date(self):
            nextdate = (self.pull_down_date + datetime.timedelta(days=31)).strftime("%Y%m")
            return nextdate

        def get_csv_link(self):
            pq_csv_a = self.pq_html.find('td.sc20 span.s3 a')
            base_url = "https://www.smbc-card.com"
            csv_url = pq_csv_a.attr('href')
            return base_url + csv_url

        def get_cvs_records(self):
            r = self.client.get(self.get_csv_link())
            r.encoding = 'shift-jis'

            csv = r.text
            csv_rows = csv.split("\n")

            pull_down_date = self.get_pull_down_date()

            cnt = 0
            records = []
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

                records.append((use_date, content, amount))

            return records


    class NextPage():

        def __init__(self, url, client):

            res = client.get(url)
            self.res = res
            self.client = client
            self.pq_html = pq(res.text)

            pq_pull_down_date = pq(self.pq_html.find("table span.s3")[13])
            pull_down_date = re.sub(r'(\n|\r|\t|\(.\)).*', "", pq_pull_down_date.text())
            pull_down_date = re.sub(u'年(\d)月', u"年0\\1月", pull_down_date)
            pull_down_date = re.sub(u'月(\d)日', u"月0\\1日", pull_down_date)
            pull_down_date = re.sub(u'年', "-", pull_down_date)
            pull_down_date = re.sub(u'月', "-", pull_down_date)
            pull_down_date = re.sub(u'日', "", pull_down_date)
            pull_down_date = datetime.datetime.strptime(pull_down_date, "%Y-%m-%d")
            self.pull_down_date = pull_down_date

        def get_pull_down_date(self):
            return self.pull_down_date

        def get_csv_link(self):
            base_url = "https://www.smbc-card.com"
            pq_csv_a = pq(self.pq_html.find('span.s3 a')[1])
            csv_url = pq_csv_a.attr('href')

            return base_url + csv_url

        def get_cvs_records(self):
            r = self.client.get(self.get_csv_link())
            r.encoding = 'shift-jis'
            csv = r.text
            csv_rows = csv.split("\n")

            records = []
            for csv_row in csv_rows:
                fields = csv_row.split(',')

                if len(fields) <= 8:
                    continue
                if not fields[0]:
                    continue

                use_date = datetime.datetime.strptime(fields[0], "%Y/%m/%d")
                content = fields[1]
                amount = fields[6]
                records.append((use_date, content, amount))

            return records
