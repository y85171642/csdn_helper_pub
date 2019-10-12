import helper
import asyncio


async def async_export():
    async for item in helper.export_all():
        print(item)


def main():
    helper.init('chrome_option_temp')

    # helper.logout()
    helper.auto_login()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_export())

    helper.dispose()


if __name__ == '__main__':
    main()
