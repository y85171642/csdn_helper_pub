import selenium.webdriver
import time
import platform
import os
import config

driver: selenium.webdriver.Chrome

is_driver_busy = False


def fix_path(_path):
    if os.path.isabs(_path):
        return _path
    execute_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(execute_dir, _path)


zip_save_path = fix_path(config.zip_save_path)
download_path = fix_path(config.chrome_download_path)
driver_path = fix_path(config.chrome_driver_path)
option_path = fix_path(config.chrome_option_path)


def create_dir():
    if not os.path.exists(download_path):
        os.mkdir(download_path)
    if not os.path.exists(zip_save_path):
        os.mkdir(zip_save_path)


def init():
    global is_driver_busy
    global driver
    is_driver_busy = True
    _driver_path = driver_path
    create_dir()
    if platform.system() == 'Windows':
        _driver_path += ".exe"
    if not os.path.exists(_driver_path):
        raise Exception('chromedriver not exist at {}'.format(_driver_path))

    options = selenium.webdriver.ChromeOptions()
    options.add_argument("user-data-dir=" + option_path)
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
    os.chmod(driver_path, 755)
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
    driver.stop_client()
    driver.close()
    is_driver_busy = False


def check_login():
    get("https://i.csdn.net/#/uc/profile")
    if driver.current_url.find('https://i.csdn.net/#/uc/profile') != -1:
        return True
    return False


def auto_login():
    while not check_login():
        print('自动登录...')
        if driver.current_url != 'https://passport.csdn.net/login':
            get('https://passport.csdn.net/login')

        find('//div[@class="main-select"]/ul/li[2]/a').click()
        time.sleep(1)
        find('//input[@id="all"]').clear()
        find('//input[@id="all"]').send_keys(config.account)
        time.sleep(1)
        find('//*[@id="app"]/div/div/div/div[2]').click()
        find('//input[@id="password-number"]').clear()
        find('//input[@id="password-number"]').send_keys(config.password)
        time.sleep(1)
        find('//*[@id="app"]/div/div/div/div[2]/div[4]/form/div/div[6]/div/button').click()
        time.sleep(3)

        if driver.current_url == 'https://passport.csdn.net/sign':
            input('需要进行安全验证，请在浏览器中完成验证，并按任意键继续...')
            print('验证完成！尝试重新登录中...')
        elif driver.current_url == 'https://passport.csdn.net/login':
            if find('//div[@class="shumei_captcha shumei_captcha_popup_wrapper shumei_show"]') is not None:
                input('需要进行滑块验证，请在浏览器中完成验证，并按任意键继续...')
                print('验证完成！尝试重新登录中...')
            elif find('//button[@class="btn btn-primary__disabled"]') is not None:
                input('用户名密码为空，请主动登录账号，并按任意键继续...')
                print('验证完成！尝试重新登录中...')
            elif find('//div[@class="form-group form-group-error"]') is not None:
                input('用户名密码错误，请主动登录账号，并按任意键继续...')
                print('验证完成！尝试重新登录中...')
            else:
                input('自动登录失败，请主动登录账号，并按任意键继续...')
                print('验证完成！尝试重新登录中...')
        else:
            print('账户登录成功！')


def auto_download(url, qq_num=config.default_qq, qq_name=config.default_qq_name):
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

        step = 'valid page'
        if find('//div[@class="error_text"]') is not None:
            return __download_result(False, find('//div[@class="error_text"]').text)

        step = 'get download info'
        info = __get_download_info()
        info['url'] = url
        info['qq_num'] = qq_num
        info['qq_name'] = qq_name

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
            find('//a[@class="dl_btn vip_dl_btn" and text()="VIP下载"]').click()
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
                return __download_result(False, "该资源无法下载！")

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


def __valid_download_url(url):
    import requests
    if requests.get(url).text.find('<div class="download_l fl" id="detail_down_l">') != -1:
        return True
    return False


def __get_download_info():
    import datetime
    coin_el = find('//div[@class="dl_download_box dl_download_l"]/label/em')
    coin = 0 if coin_el is None else int(coin_el.text.strip())
    info = {
        'id': find('//div[@id="download_top"]').get_attribute('data-id'),
        'title': find('//dl[@class="download_dl"]/dd/h3').get_attribute('title'),
        'description': find('//div[@class="pre_description"]').text.strip(),
        'type': find('//dl[@class="download_dl"]/dt/img').get_attribute('title'),
        'tag': find('//a[@class="tag"]').text.strip(),
        'coin': coin,
        'stars': find_count('//span[@class="starts"]//i[@class="fa fa-star yellow"]'),
        'upload_date': datetime.datetime.fromisoformat(find('//strong[@class="size_box"]/span[1]').text.strip()[:10]),
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
