import configparser
import os
import sys


def app_path():
    """Returns the base application path."""
    if hasattr(sys, 'frozen'):  # Handles PyInstaller
        return os.path.dirname(sys.executable)  # 使用pyinstaller打包后的exe目录
    return os.path.dirname(__file__)  # 没打包前的py目录


def get_cfg(_name):
    return conf.get('general', _name)


def str_to_bool(_str):
    return True if _str.lower() == 'true' else False


def frozen_path(_path):
    if os.path.isabs(_path):
        return _path
    return os.path.join(app_path(), _path)


def get_donate_list():
    _path = frozen_path("donate_list.ini")
    if not os.path.exists(_path):
        return []
    _con = configparser.ConfigParser()
    _con.read(_path, encoding="utf-8")
    return eval(_con.get('general', 'list'))


cfg_path = frozen_path("config.ini")
if not os.path.exists(cfg_path):
    raise Exception("未能找到配置文件：{}".format(cfg_path))

# 创建管理对象
conf = configparser.ConfigParser()

# 读ini文件
conf.read(cfg_path, encoding="utf-8")

default_qq = get_cfg('default_qq')
default_qq_name = get_cfg('default_qq_name')
need_at_me = str_to_bool(get_cfg('need_at_me'))
psyduck_port = int(get_cfg('psyduck_port'))
default_group = get_cfg('default_group')

chrome_driver_path = frozen_path(get_cfg('chrome_driver_path'))
chrome_option_path = frozen_path(get_cfg('chrome_option_path'))
chrome_download_path = frozen_path(get_cfg('chrome_download_path'))

zip_save_path = frozen_path(get_cfg('zip_save_path'))
sqlite_db_path = frozen_path(get_cfg('sqlite_db_path'))
download_server_url = get_cfg('download_server_url')
donate_url = get_cfg('donate_url')
source_code_url = get_cfg('source_code_url')
export_url = get_cfg('export_url')
search_url = get_cfg('search_url')
admin_list = eval(get_cfg('admin_list'))
daily_download_count = int(get_cfg('daily_download_count'))
weekly_download_count = int(get_cfg('weekly_download_count'))
monthly_download_count = int(get_cfg('monthly_download_count'))
use_short_url = str_to_bool(get_cfg('use_short_url'))

donate_list = get_donate_list()

