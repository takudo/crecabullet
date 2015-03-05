#! /usr/bin/python
# -*- coding: utf-8 -*-

from peewee import *
from playhouse.sqlite_ext import *
import datetime
from model.db import Db

db = Db.get_conn()

class Meisai(Model):

    pull_down_date = DateField()
    use_date = DateField()
    content = CharField()
    amount = IntegerField()
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = Db.get_conn()


    @staticmethod
    def get_meisai(pull_down_date, use_date, content, amount):
        return Meisai.select().where(
            (Meisai.pull_down_date == pull_down_date) &
            (Meisai.use_date == use_date) &
            (Meisai.content == content) &
            (Meisai.amount == amount)
        )

    @staticmethod
    def get_month_amount(pull_down_date):
        return Meisai.select(
            fn.Sum(Meisai.amount)
        ).where(
            (Meisai.pull_down_date == pull_down_date)
        ).scalar(as_tuple=True)


db.create_tables([Meisai], True)
