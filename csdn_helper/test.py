import helper


def test():
    try:
        print(helper.check_download_limit(772757236, 606737006))
        # helper.init()
        # print(helper.get_user_info())
        # print(helper.auto_download('https://download.csdn.net/download/cnhww/11153341'))
    finally:
        # helper.dispose()
        pass


def main():
    test()


if __name__ == '__main__':
    main()
