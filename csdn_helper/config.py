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

chrome_driver_path = frozen_path(get_cfg('chrome_driver_path'))
chrome_option_path = frozen_path(get_cfg('chrome_option_path'))
chrome_download_path = frozen_path(get_cfg('chrome_download_path'))

zip_save_path = frozen_path(get_cfg('zip_save_path'))
sqlite_db_path = frozen_path(get_cfg('sqlite_db_path'))
download_server_url = get_cfg('download_server_url')

donate_list = {
    '1213634685': 10,
    '1151021131': 12,
    '978767937': 20,
    '2918720083': 1,
    '444711706': 8,
    '1265229798': 6.66,
    '657534755': 9,
    '10512': 10,
    '1436816322': 10,
    '850376525': 5,
    '873293006': 10,
    '1097515808': 5,
    '1983422398': 5,
    '387697480': 5,
    '1466119776': 4.44,
    '1804047398': 5,
    '158881816': 5,
    '37617718': 100,
    '741091942': 5,
    '1583863436': 5,
    '921397175': 5,
    '1653077113': 10,
    '1250226345': 5,
    '894001430': 5,
    '471707425': 5,
    '319355229': 5,
    '602210855': 5,
    '158233589': 5,
    '2304806324': 5,
    '1251417632': 5,
    '164645554': 5,
    '799329256': 10,
    '1937074453': 5,
    '991959299': 2,
    '656669204': 5,
    '1258586900': 200,
    '454625731': 5,
}
