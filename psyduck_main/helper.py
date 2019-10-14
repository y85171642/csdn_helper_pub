import selenium.webdriver
import time
import platform
import os
import config

driver: selenium.webdriver.Chrome = None

is_driver_busy = False

zip_save_path = config.zip_save_path
download_path = config.chrome_download_path
driver_path = config.chrome_driver_path
option_path = config.chrome_option_path


def create_dir():
    if not os.path.exists(download_path):
        os.mkdir(download_path)
    if not os.path.exists(zip_save_path):
        os.mkdir(zip_save_path)


def init(_option_path=''):
    global is_driver_busy
    global driver
    is_driver_busy = True
    _driver_path = driver_path
    create_dir()
    if platform.system() == 'Windows':
        _driver_path += ".exe"
    if not os.path.exists(_driver_path):
        raise Exception('chromedriver not exist at {}'.format(_driver_path))

    if _option_path == '':
        _option_path = option_path
    options = selenium.webdriver.ChromeOptions()
    options.add_argument("user-data-dir=" + _option_path)
    options.add_argument('disable-infobars')
    options.add_argument('--mute-audio')
    options.add_argument('--disable-gpu')
    options.add_argument("--log-level=3")

    prefs = {
        "disable-popup-blocking": False,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "download.default_directory": download_path,
        "profile.default_content_settings.popups": 0,
        'profile.default_content_setting_values': {'notifications': 2},
    }

    from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
    cap = DesiredCapabilities.CHROME
    cap["pageLoadStrategy"] = "none"

    options.add_experimental_option("prefs", prefs)
    os.chmod(_driver_path, 755)
    driver = selenium.webdriver.Chrome(options=options, executable_path=_driver_path, desired_capabilities=cap)
    driver.set_window_size(1000, 750)
    reset_timeout()


def reset_timeout():
    driver.set_page_load_timeout(10)
    driver.set_script_timeout(10)
    # driver.implicitly_wait(10)


def is_busy():
    return is_driver_busy


def get(url, timeout=10, retry=3):
    driver.get(url)
    time.sleep(1)
    time_counter = 0
    retry_counter = 0
    while retry_counter < retry:
        while time_counter < timeout:
            result = driver.execute_script("return document.readyState")
            if result == 'complete':
                return
            if result == 'interactive':
                time.sleep(3)
                return
            time_counter += 1
            time.sleep(1)
        retry_counter += 1
        print('timeout retry %d -> %s' % (retry_counter, url))
    raise Exception('timeout retry %d all failed -> %s' % (retry, url))


def find(xpath):
    import selenium.common.exceptions
    try:
        el = driver.find_element_by_xpath(xpath)
    except selenium.common.exceptions.NoSuchElementException:
        return None
    return el


def find_all(xpath):
    return driver.find_elements_by_xpath(xpath)


def find_count(xpath):
    return len(find_all(xpath))


def set_window_size(width, height):
    driver.set_window_size(width, height)


def dispose():
    global driver
    global is_driver_busy
    if driver is not None:
        driver.stop_client()
        driver.quit()
        driver = None
    is_driver_busy = False


def check_login():
    get("https://i.csdn.net/#/uc/profile")
    if driver.current_url.find('https://i.csdn.net/#/uc/profile') != -1:
        return True
    return False


def logout():
    get('https://passport.csdn.net/account/logout')


def auto_login():
    while not check_login():
        print('自动登录...')
        if driver.current_url != 'https://passport.csdn.net/login':
            get('https://passport.csdn.net/login')

        input("请手动登录，并按任意键继续...")
        print('验证完成！尝试重新登录中...')
        continue


def auto_download(url, qq_num=config.default_qq, qq_name=config.default_qq_name, qq_group=-1):
    step = 'begin download'
    try:
        step = 'url cut #'
        if url.find('#') != -1:
            url = url[0:url.index('#')]

        step = 'valid url'
        if not __valid_download_url(url):
            return __download_result(False, "无效的下载地址")

        step = 'login'
        auto_login()

        step = 'get url'
        get(url)
        time.sleep(3)

        step = 'valid page'
        if find('//div[@class="error_text"]') is not None:
            return __download_result(False, find('//div[@class="error_text"]').text)

        step = 'get download info'
        info = __get_download_info()
        info['url'] = url
        info['qq_num'] = qq_num
        info['qq_name'] = qq_name
        info['qq_group'] = qq_group

        step = 'check already download'
        if __already_download(info['id']):
            step = 'already download set zip file name'
            info['filename'] = __get_file_name_in_zip_file(info['id'])
            step = 'save to db'
            __save_to_db(info)
            step = 'finish'
            return __download_result(True, "success", info)

        step = 'find download button'
        btn = find('//div[@class="dl_download_box dl_download_l"]/a[text()="VIP下载"]')
        vip_channel = True
        step = 'check download channel'
        if btn is None:
            vip_channel = False
        if not vip_channel:
            btn = find('//div[@class="dl_download_box dl_download_l"]/a[@class="direct_download"]')
        if btn is None:
            return __download_result(False, "该资源没有下载通道")

        step = 'clear download dir'
        __clear_download_dir()
        time.sleep(1)

        step = 'click download button'
        btn.click()
        time.sleep(1)

        step = 'check max count'
        if find('//div[@id="download_times"]').get_attribute('style').find('display: block;') != -1:
            return __download_result(False, 'CSDN今日下载次数已达上限（20），请明日在来下载。')

        step = 'find confirm download'
        if vip_channel:
            if find('//div[@id="vipIgnoreP"]').get_attribute('style').find('display: block;') != -1:
                find('//div[@id="vipIgnoreP"]//a[@class="dl_btn vip_dl_btn"]').click()
            else:
                pass  # 无弹窗情况（自己的资源）
        else:
            if find('//div[@id="noVipEnoughP"]').get_attribute('style').find('display: block;') != -1:
                find('//div[@id="noVipEnoughP"]//a[@class="dl_btn js_download_btn"]').click()
            elif find('//div[@id="download"]').get_attribute('style').find('display: block;') != -1:
                find('//div[@id="download"]//a[@class="dl_btn js_download_btn"]').click()
            elif find('//div[@id="noVipEnoughP"]').get_attribute('style').find('display: block;') != -1:
                find('//div[@id="noVipEnoughP"]//a[@class="dl_btn js_download_btn"]').click()
            elif find('//div[@id="noVipEnoughP"]').get_attribute('style').find('display: block;') != -1:
                find('//div[@id="noVipEnoughP"]//a[@class="dl_btn js_download_btn"]').click()
            elif find('//div[@id="noVipNoEnoughPNoC"]').get_attribute('style').find('display: block;') != -1:
                return __download_result(False, "积分不足下载！")
            elif find('//div[@id="dl_lock"]').get_attribute('style').find('display: block;') != -1:
                return __download_result(False, find('//div[@id="dl_lock"]').text)
            else:
                pass  # 无弹窗情况（自己的资源）

            time.sleep(1)
            if find('//div[@id="dl_security_detail"]').get_attribute('style').find('display: block;') != -1:
                # input('下载过于频繁，请输入验证码，并按任意键继续...')
                # print('验证完成！继续下载任务中...')
                return __download_result(False, "下载过于频繁，请输入验证码")

        step = 'wait for download'
        __wait_for_download()

        step = 'add filename to info'
        info['filename'] = os.path.basename(__get_tmp_download_file())

        step = 'zip file'
        __zip_file(info['id'])

        step = 'save to db'
        __save_to_db(info)

        step = 'finish'
        return __download_result(True, "success", info)
    except:
        import traceback
        traceback.print_exc()
        return __download_result(False, "error : %s" % step)


async def export_all():
    import asyncio
    await asyncio.sleep(1)
    format_url = 'https://download.csdn.net/my/uploads/1/{}'
    res_url = []
    for i in range(1, 100):
        _url = format_url.format(i)
        get(_url)
        if find('//dt[@class="empty_icons"]') is not None:
            break
        els = find_all('//div[@class="content"]/h3/a[@target="_blank"]')
        for el in els:
            if el.get_attribute('href') is None:
                continue
            res_url.append(el.get_attribute('href'))
    for _url in res_url:
        yield "开始下载：" + _url
        auto_download(_url)
        yield "下载完成：" + _url


def __valid_download_url(url):
    # 暂时屏蔽验证
    return True
    import requests
    if requests.get(url).text.find('<div class="download_l fl" id="detail_down_l">') != -1:
        return True
    return False


def get_money(qq_num):
    money = 0
    for donor in config.donate_list:
        if donor['qq'] == qq_num:
            money = donor['money']
            break
    return money


def monthly_download_count(qq_num):
    return int(get_money(qq_num) ** 0.7) + config.monthly_download_count


def weekly_download_count(qq_num):
    return int(get_money(qq_num) ** 0.5) + config.weekly_download_count


def daily_download_count(qq_num):
    return int(get_money(qq_num) ** 0.3) + config.daily_download_count


def check_download_limit(qq_num, qq_group):
    import db_helper

    count = daily_download_count(qq_num)
    if db_helper.count_daily(qq_num, qq_group) >= count:
        return False, "您今日下载次数已达到上限（%d）次，请明日再来下载！" % count

    count = weekly_download_count(qq_num)
    if db_helper.count_weekly(qq_num, qq_group) >= count:
        return False, "您本周下载次数已达到上限（%d）次，请下周再来下载！" % count

    count = monthly_download_count(qq_num)
    if db_helper.count_monthly(qq_num, qq_group) >= count:
        return False, "您本月下载次数已达到上限（%d）次，请下月再来下载！" % count

    return True, ""


def __get_download_info():
    import datetime
    coin_el = find('//div[@class="dl_download_box dl_download_l"]/label/em')
    coin = 0 if coin_el is None else int(coin_el.text.strip())
    date_str = find('//strong[@class="size_box"]/span[1]').text.strip()[:10]
    info = {
        'id': find('//div[@id="download_top"]').get_attribute('data-id'),
        'title': find('//dl[@class="download_dl"]/dd/h3').get_attribute('title'),
        'description': find('//div[@class="pre_description"]').text.strip(),
        'type': find('//dl[@class="download_dl"]/dt/img').get_attribute('title'),
        'tag': find('//a[@class="tag"]').text.strip(),
        'coin': coin,
        'stars': find_count('//span[@class="starts"]//i[@class="fa fa-star yellow"]'),
        'upload_date': datetime.datetime.strptime(date_str, "%Y-%m-%d"),
        'size': find('//strong[@class="size_box"]/span[2]/em').text.strip(),
    }
    return info


def __clear_download_dir():
    for f in os.listdir(download_path):
        os.remove(os.path.join(download_path, f))


def __get_tmp_download_file():
    files = os.listdir(download_path)
    if len(files) <= 0:
        raise Exception('下载文件不存在！')
    elif len(files) > 1:
        raise Exception('下载目录存在多余文件！')
    return os.path.join(download_path, files[0])


def __wait_for_download():
    time.sleep(3)  # wait for create file
    wait_time = 20
    last_size = os.path.getsize(__get_tmp_download_file())
    while wait_time > 0 and __get_tmp_download_file().endswith('.crdownload'):
        cur_size = os.path.getsize(__get_tmp_download_file())
        if cur_size == last_size:
            wait_time -= 1
        else:
            wait_time = 20
        time.sleep(1)

    if __get_tmp_download_file().endswith('.crdownload'):
        raise Exception('文件下载失败，请重试！')


def __zip_file(_id):
    import zipfile
    zip_path = os.path.join(zip_save_path, "{0}.zip".format(_id))
    if os.path.exists(zip_path):
        os.remove(zip_path)
        print('zip exist, then delete!')
    with zipfile.ZipFile(zip_path, mode='w') as zipf:
        file_path = __get_tmp_download_file()
        zipf.write(file_path, os.path.basename(file_path))


def __get_file_name_in_zip_file(_id):
    import zipfile
    zip_path = os.path.join(zip_save_path, "{0}.zip".format(_id))
    zipf = zipfile.ZipFile(zip_path)
    files = zipf.namelist()
    if len(files) != 1:
        return None
    return files[0]


def __already_download(_id):
    import db_helper
    if db_helper.exist_download(_id) and db_helper.get_download(_id).download_url is not None:
        return True
    zip_path = os.path.join(zip_save_path, "{0}.zip".format(_id))
    if os.path.exists(zip_path):
        file_name = __get_file_name_in_zip_file(_id)
        if file_name is not None and not file_name.endswith('.crdownload'):
            return True
    return False


def __save_to_db(info):
    import db_helper
    if not db_helper.exist_download(info['id']):
        db_helper.insert_download(info)


def __download_result(success, message='', info=None):
    return {'success': success, 'message': message, 'info': info, }


def get_user_info():
    try:
        auto_login()
        get('https://download.csdn.net/my/vip')
        time.sleep(2)
        name = find('//div[@class="name"]/span').text.strip()
        is_vip = find('//a[@class="btn_vipsign"]') is None
        info = {
            'name': name,
            'vip': is_vip
        }
        if is_vip:
            remain = find('//div[@class="cardr"]/ul/li/span').text.strip()
            date = find('//div[@class="cardr"]/ul/li[2]/span').text.strip()
            info['remain'] = remain
            info['date'] = date
        else:
            remain = find('//ul[@class="datas clearfix"]//span').text.strip()
            info['remain'] = remain
        return info
    except:
        import traceback
        traceback.print_exc()
        return None
