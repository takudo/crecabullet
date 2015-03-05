#! /usr/bin/python
# -*- coding: utf-8 -*-

from peewee import *
from playhouse.sqlite_ext import *

class Db():

    conn = False

    @staticmethod
    def get_conn():
        if not Db.conn :
            Db.conn = SqliteDatabase("creca.db")

        return Db.conn