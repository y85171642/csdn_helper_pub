import helper


def stop():
    helper.dispose()
    pass


def test():
    try:
        helper.init()
        print(helper.get_user_info())
        print(helper.auto_download('https://download.csdn.net/download/ozhy111/10880596'))
        print(helper.auto_download('https://download.csdn.net/download/wjf8882300/10879204'))
        print(helper.auto_download('https://download.csdn.net/download/yeyuxingyun/3455948'))
        print(helper.auto_download('https://download.csdn.net/download/u013363856/9783561'))
    finally:
        helper.dispose()


def main():
    test()


if __name__ == '__main__':
    main()
