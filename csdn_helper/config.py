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


cfg_path = frozen_path("config.ini")
if not os.path.exists(cfg_path):
    raise Exception("未能找到配置文件：{}".format(cfg_path))

# 创建管理对象
conf = configparser.ConfigParser()

# 读ini文件
conf.read(cfg_path, encoding="utf-8")  # python3

account = get_cfg('csdn_account')
password = get_cfg('csdn_password')

default_qq = get_cfg('default_qq')
default_qq_name = get_cfg('default_qq_name')
need_at_me = str_to_bool(get_cfg('need_at_me'))
psyduck_port = int(get_cfg('psyduck_port'))

chrome_driver_path = frozen_path(get_cfg('chrome_driver_path'))
chrome_option_path = frozen_path(get_cfg('chrome_option_path'))
chrome_download_path = frozen_path(get_cfg('chrome_download_path'))

zip_save_path = frozen_path(get_cfg('zip_save_path'))
sqlite_db_path = frozen_path(get_cfg('sqlite_db_path'))
download_server_url = get_cfg('download_server_url')

default_daily_download_count = 1
default_monthly_download_count = 10

donate_list = [
    {'qq': '1213634685', 'name': '非凡', 'money': 10},
    {'qq': '978767937', 'name': 'ip_555...', 'money': 20},
    {'qq': '1151021131', 'name': '各有所爱', 'money': 12},
    {'qq': '2918720083', 'name': '6666...', 'money': 1},
    {'qq': '444711706', 'name': '品位', 'money': 8},
    {'qq': '1265229798', 'name': '临客', 'money': 6.66},
    {'qq': '657534755', 'name': '烟花往一边...', 'money': 9},
    {'qq': '10512', 'name': '阿布', 'money': 10},
    {'qq': '1436816322', 'name': '好好先森', 'money': 10},
    {'qq': '850376525', 'name': 'dark', 'money': 5},
    {'qq': '873293006', 'name': 'sgm...', 'money': 10},
    {'qq': '1097515808', 'name': '凉心Tel', 'money': 5},
    {'qq': '1983422398', 'name': '自闭少年想要钱', 'money': 5},
    {'qq': '387697480', 'name': '寻找', 'money': 5},
    {'qq': '1466119776', 'name': '老婆', 'money': 4.44},
    {'qq': '1804047398', 'name': 'lovern\'t', 'money': 5},
    {'qq': '158881816', 'name': '逆风', 'money': 5},
    {'qq': '37617718', 'name': '我是机器人', 'money': 100},
    {'qq': '741091942', 'name': 'ttwo', 'money': 5},
    {'qq': '1583863436', 'name': '天涯', 'money': 5},
    {'qq': '921397175', 'name': 'c8008...', 'money': 5},
    {'qq': '1653077113', 'name': '南风', 'money': 10},
    {'qq': '1250226345', 'name': '咕噜 咕噜', 'money': 5},
    {'qq': '894001430', 'name': 'a`空白', 'money': 5},
    {'qq': '471707425', 'name': '淘宝直播人...', 'money': 5},
    {'qq': '319355229', 'name': '尘。封', 'money': 5},
    {'qq': '602210855', 'name': '雨 涵', 'money': 5},
    {'qq': '158233589', 'name': 'brick', 'money': 5},
    {'qq': '2304806324', 'name': 'Z', 'money': 5},
    {'qq': '1251417632', 'name': 'zhangson...', 'money': 5},
    {'qq': '164645554', 'name': '我的群名片', 'money': 5},
    {'qq': '799329256', 'name': '菜鸡儿', 'money': 10},
    {'qq': '1937074453', 'name': '天絮', 'money': 5},
    {'qq': '991959299', 'name': '991959299', 'money': 2},
    {'qq': '656669204', 'name': '清和', 'money': 5},
    {'qq': '1258586900', 'name': '志远', 'money': 200},
    {'qq': '454625731', 'name': 'nagatoyuki', 'money': 5},
    {'qq': '619825885', 'name': '≮阿→德≯', 'money': 5},
]
