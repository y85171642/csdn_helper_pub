import helper


def stop():
    helper.dispose()
    pass


def test():
    try:
        print(helper.check_download_limit(45671948, 623597263))
        # helper.init()
        # print(helper.get_user_info())
        # print(helper.auto_download('https://download.csdn.net/download/cnhww/11153341'))
    finally:
        helper.dispose()


def main():
    test()


if __name__ == '__main__':
    main()
