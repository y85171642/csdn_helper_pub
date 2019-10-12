from peewee import *
import datetime
import config
import os

db_dir = os.path.dirname(config.sqlite_db_path)
if not os.path.exists(db_dir):
    os.mkdir(db_dir)
db = SqliteDatabase(config.sqlite_db_path)


class Download(Model):
    class Meta:
        database = db

    id = CharField(primary_key=True, unique=True)
    url = CharField(null=True)
    title = CharField(null=True)
    type = CharField(null=True)
    size = CharField(null=True)
    tag = CharField(null=True)
    description = CharField(null=True)
    filename = CharField(null=True)
    coin = IntegerField(null=True)
    stars = IntegerField(null=True)
    upload_date = DateTimeField(null=True)
    qq_num = CharField(null=True)
    qq_group = CharField(null=True)
    qq_name = CharField(null=True)
    download_url = CharField(null=True)
    created_date = DateTimeField(null=True)


def check_table():
    if not db.table_exists("download"):
        db.create_tables([Download])


def insert_download(info):
    check_table()
    result = Download.create(id=info['id'], url=info['url'], title=info['title'], type=info['type'], coin=info['coin'],
                             stars=info['stars'], size=info['size'], tag=info['tag'], description=info['description'],
                             filename=info['filename'], upload_date=info['upload_date'], qq_num=info['qq_num'],
                             qq_name=info['qq_name'], qq_group=info['qq_group'], download_url='',
                             created_date=datetime.datetime.now())
    return result


def get_download(_id):
    check_table()
    return Download.select().where(Download.id == _id).first()


def exist_download(_id):
    return get_download(_id) is not None


def set_download_url(_id, _url):
    Download.update(download_url=_url).where(Download.id == _id).execute()
