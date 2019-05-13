import configparser
import os

curpath = os.path.dirname(os.path.realpath(__file__))
cfgpath = os.path.join(curpath, "config.ini")
# 创建管理对象
conf = configparser.ConfigParser()

# 读ini文件
conf.read(cfgpath, encoding="utf-8")  # python3


def __get_conf(_name):
    return conf.get('general', _name)


account = __get_conf('csdn_account')
password = __get_conf('csdn_password')

default_qq = __get_conf('default_qq')
default_qq_name = __get_conf('default_qq_name')

chrome_driver_path = __get_conf('chrome_driver_path')
chrome_option_path = __get_conf('chrome_option_path')
chrome_download_path = __get_conf('chrome_download_path')

zip_save_path = __get_conf('zip_save_path')
sqlite_db_path = __get_conf('sqlite_db_path')
download_server_url = __get_conf('download_server_url')

