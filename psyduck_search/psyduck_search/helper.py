import selenium.webdriver
import time
import platform
import os
from psyduck_search import config
from psyduck_search import db_helper


class Helper:
    is_ready = False
    driver = None
    download_path = None
    export_path = None
    zip_export_path = None
    zip_save_path = None
    driver_path = None
    option_path = None
    data_path = None
    data_root = None
    uuid = None

    export_url_list = []
    export_name_list = []
    export_index = 0
    export_collecting = False
    export_downloading = False

    def __init__(self, uuid):
        self.uuid = uuid

    @staticmethod
    def _create_dir(_dir):
        _dir = config.frozen_path(_dir)
        if not os.path.exists(_dir):
            os.mkdir(_dir)

    @staticmethod
    def _get_driver_name(name):
        if platform.system() == 'Windows' and not name.endswith('.exe'):
            name += ".exe"
        return name

    def __settings(self):
        self.is_ready = False
        self.data_root = config.frozen_path('user_data')
        self.data_path = config.frozen_path(os.path.join(self.data_root, self.uuid))
        self.driver_path = config.frozen_path(os.path.join(self.data_path, Helper._get_driver_name('chromedriver')))
        self.option_path = config.frozen_path(os.path.join(self.data_path, 'chrome_option'))
        self.download_path = config.frozen_path(os.path.join(self.data_path, 'download'))
        self.export_path = os.path.abspath(config.frozen_path('../static/exports/{}'.format(self.uuid)))
        self.zip_export_path = os.path.abspath(config.frozen_path('../static/exports/{}.zip'.format(self.uuid)))
        self.zip_save_path = config.frozen_path(config.zip_save_path)

    def __prepare(self):
        Helper._create_dir(self.data_root)
        Helper._create_dir(self.data_path)
        import shutil
        _raw_driver_path = config.frozen_path(os.path.join('chrome_driver', Helper._get_driver_name('chromedriver')))
        _driver_dir = os.path.dirname(self.driver_path)
        Helper._create_dir(_driver_dir)
        os.chmod(_driver_dir, 0o777)
        shutil.copyfile(_raw_driver_path, self.driver_path)
        Helper._create_dir(self.download_path)
        Helper._create_dir(self.zip_save_path)
        Helper._create_dir(self.export_path)
        os.chmod(self.export_path, 0o777)

    def __selenium_init(self):
        options = selenium.webdriver.ChromeOptions()
        options.add_argument("user-data-dir=" + self.option_path)
        options.add_argument('disable-infobars')
        options.add_argument('--mute-audio')
        options.add_argument('--disable-gpu')
        options.add_argument("--log-level=3")

        prefs = {
            "disable-popup-blocking": False,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "download.default_directory": self.download_path,
            "profile.default_content_settings.popups": 0,
            'profile.default_content_setting_values': {'notifications': 2},
        }

        from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
        cap = DesiredCapabilities.CHROME
        cap["pageLoadStrategy"] = "none"

        options.add_experimental_option("prefs", prefs)
        os.chmod(self.driver_path, 0o777)

        self.driver = selenium.webdriver.Chrome(options=options, executable_path=self.driver_path,
                                                desired_capabilities=cap)
        self.driver.set_window_size(1000, 750)
        self.reset_timeout()

    def init(self):
        self.__settings()
        self.__prepare()
        self.__selenium_init()
        self.is_ready = True
        self.export_collecting = False
        self.export_downloading = False

    def reset_timeout(self):
        self.driver.set_page_load_timeout(10)
        self.driver.set_script_timeout(10)

    def get(self, url, timeout=10, retry=3):
        self.driver.get(url)
        time.sleep(1)
        time_counter = 0
        retry_counter = 0
        while retry_counter < retry:
            while time_counter < timeout:
                result = self.driver.execute_script("return document.readyState")
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

    def find(self, xpath):
        import selenium.common.exceptions
        try:
            el = self.driver.find_element_by_xpath(xpath)
        except selenium.common.exceptions.NoSuchElementException:
            return None
        return el

    def find_all(self, xpath):
        return self.driver.find_elements_by_xpath(xpath)

    def find_count(self, xpath):
        return len(self.find_all(xpath))

    def set_window_size(self, width, height):
        self.driver.set_window_size(width, height)

    def dispose(self):
        if self.driver is not None:
            self.driver.stop_client()
            self.driver.quit()
            self.driver = None
        self.is_ready = False
        self.export_downloading = False
        self.export_collecting = False

    def check_login(self):
        self.get("https://i.csdn.net/#/uc/profile")
        if self.driver.current_url.find('https://i.csdn.net/#/uc/profile') != -1:
            return True
        return False

    def logout(self):
        self.get('https://passport.csdn.net/account/logout')

    def login(self, phone_num, verify_code):
        if self.driver.current_url != 'https://passport.csdn.net/login':
            self.get('https://passport.csdn.net/login')
            time.sleep(1)
        self.find('//a[text()="免密登录"]').click()
        time.sleep(1)
        self.find('//input[@id="phone"]').clear()
        self.find('//input[@id="phone"]').send_keys(phone_num)
        time.sleep(1)
        self.find('//input[@id="code"]').clear()
        self.find('//input[@id="code"]').send_keys(verify_code)
        time.sleep(1)
        self.find('//button[@data-type="accountMianMi"]').click()
        time.sleep(1)
        err = self.find('//div[@id="js_err_dom"]')
        if err is not None and err.get_attribute('class').find('hide') == -1:
            return err.text
        return ''

    def __valid_download_url(self, url):
        # 暂时屏蔽验证
        return url != ''

    def download(self, url, qq_num=config.default_qq, qq_name=config.default_qq_name, qq_group=-1):
        step = 'begin download'
        try:
            step = 'url cut #'
            if url.find('#') != -1:
                url = url[0:url.index('#')]

            step = 'valid url'
            if not self.__valid_download_url(url):
                return self.__download_result(False, "无效的下载地址")

            step = 'get url'
            self.get(url)
            time.sleep(3)

            step = 'valid page'
            if self.find('//div[@class="error_text"]') is not None:
                return self.__download_result(False, self.find('//div[@class="error_text"]').text)

            step = 'get download info'
            info = self.__get_download_info()
            info['url'] = url
            info['qq_num'] = qq_num
            info['qq_name'] = qq_name
            info['qq_group'] = qq_group

            step = 'find download button'
            btn = self.find('//div[@class="dl_download_box dl_download_l"]/a[text()="VIP下载"]')
            vip_channel = True
            step = 'check download channel'
            if btn is None:
                vip_channel = False
            if not vip_channel:
                btn = self.find('//div[@class="dl_download_box dl_download_l"]/a[@class="direct_download"]')
            if btn is None:
                return self.__download_result(False, "该资源没有下载通道")

            step = 'clear download dir'
            self.__clear_download_dir()
            time.sleep(1)

            step = 'click download button'
            btn.click()
            time.sleep(1)

            step = 'check max count'
            if self.find('//div[@id="download_times"]').get_attribute('style').find('display: block;') != -1:
                return self.__download_result(False, 'CSDN今日下载次数已达上限（20），请明日在来下载。')

            step = 'find confirm download'
            if vip_channel:
                if self.find('//div[@id="vipIgnoreP"]').get_attribute('style').find('display: block;') != -1:
                    self.find('//div[@id="vipIgnoreP"]//a[@class="dl_btn vip_dl_btn"]').click()
                else:
                    pass  # 无弹窗情况（自己的资源）
            else:
                if self.find('//div[@id="noVipEnoughP"]').get_attribute('style').find('display: block;') != -1:
                    self.find('//div[@id="noVipEnoughP"]//a[@class="dl_btn js_download_btn"]').click()
                elif self.find('//div[@id="download"]').get_attribute('style').find('display: block;') != -1:
                    self.find('//div[@id="download"]//a[@class="dl_btn js_download_btn"]').click()
                elif self.find('//div[@id="noVipEnoughP"]').get_attribute('style').find('display: block;') != -1:
                    self.find('//div[@id="noVipEnoughP"]//a[@class="dl_btn js_download_btn"]').click()
                elif self.find('//div[@id="noVipEnoughP"]').get_attribute('style').find('display: block;') != -1:
                    self.find('//div[@id="noVipEnoughP"]//a[@class="dl_btn js_download_btn"]').click()
                elif self.find('//div[@id="noVipNoEnoughPNoC"]').get_attribute('style').find('display: block;') != -1:
                    return self.__download_result(False, "积分不足下载！")
                elif self.find('//div[@id="dl_lock"]').get_attribute('style').find('display: block;') != -1:
                    return self.__download_result(False, self.find('//div[@id="dl_lock"]').text)
                else:
                    pass  # 无弹窗情况（自己的资源）

                time.sleep(1)
                if self.find('//div[@id="dl_security_detail"]').get_attribute('style').find('display: block;') != -1:
                    # input('下载过于频繁，请输入验证码，并按任意键继续...')
                    # print('验证完成！继续下载任务中...')
                    return self.__download_result(False, "下载过于频繁，请输入验证码")

            step = 'wait for download'
            self.__wait_for_download()

            step = 'add filename to info'
            info['filename'] = os.path.basename(self.__get_tmp_download_file())

            step = 'zip file'
            self.__zip_file(info['id'])

            step = 'save to export'
            self.__save_to_export(info['id'])

            step = 'save to db'
            self.__save_to_db(info)

            step = 'finish'
            return self.__download_result(True, "success", info)
        except:
            import traceback
            traceback.print_exc()
            return self.__download_result(False, "error : %s" % step)

    def __save_to_export(self, _id):
        import shutil
        src = self.__get_tmp_download_file()
        dst = os.path.join(self.export_path, _id + "." + os.path.basename(src))
        shutil.copyfile(src, dst)

    def __zip_export(self):
        zip_path = os.path.join(self.zip_export_path)
        if os.path.exists(zip_path):
            os.remove(zip_path)
        import zipfile
        with zipfile.ZipFile(zip_path, mode='w') as zip_f:
            for f in os.listdir(self.export_path):
                zip_f.write(os.path.join(self.export_path, f), f)

        for f in os.listdir(self.export_path):
            os.remove(os.path.join(self.export_path, f))

    def export_all(self):
        format_url = 'https://download.csdn.net/my/uploads/1/{}'
        res_url = []
        res_name = []
        self.export_collecting = True
        for i in range(1, 100):
            _url = format_url.format(i)
            self.get(_url)
            n = 3
            while n > 0 and self.find('//div[@class="profile_card clearfix"]') is None:
                n -= 1
                time.sleep(1)
            if self.find('//dt[@class="empty_icons"]') is not None:
                break
            els = self.find_all('//div[@class="content"]/h3/a[@target="_blank"]')
            for el in els:
                if el.get_attribute('href') is None:
                    continue
                res_url.append(el.get_attribute('href'))
                res_name.append(el.text.strip())
        self.export_collecting = False
        self.export_downloading = True
        self.export_url_list = res_url
        self.export_name_list = res_name
        for i in range(0, len(res_url)):
            self.export_index = i
            self.download(res_url[i])
        self.__zip_export()
        self.export_downloading = False

    is_searching = False
    search_result = {}

    def search(self, keyword, sort_type=1, source_type=10, area=0, signal_func=None, new_info_callback=None):
        self.is_searching = True
        self.search_result = {}
        from urllib import parse
        keyword = parse.urlencode({'_': keyword})[2:]

        def _page_url(page):
            return 'https://download.csdn.net/psearch/{area}/{source}/0/{sort}/1/{keyword}/{page}' \
                .format(area=area, source=source_type, sort=sort_type, keyword=keyword, page=page)

        self.get(_page_url(1))
        if self.find('//div[@class="noSource"]') is not None:
            self.is_searching = False
            return

        if signal_func is not None and signal_func() == 'stop':
            self.is_searching = False
            return
        total_el = self.find('//div[@class="page_nav"]')
        if total_el is None or total_el.text == '':
            total_page = 1
        else:
            text = self.find('//div[@class="page_nav"]').text[2:]
            total_page = int(text[text.find('共') + 1: text.find('页')])
        for i in range(1, total_page + 1):
            self.get(_page_url(i))

            if signal_func is not None and signal_func() == 'stop':
                self.is_searching = False
                return

            _urls = []
            for el in self.find_all('//a[@class="album_detail_title"]'):
                _url = el.get_attribute('href')
                if _url not in self.search_result.keys():
                    _urls.append(_url)
            for _url in _urls:
                try:
                    self.until_get(_url, '//strong[@class="size_box"]/span[1]', 2)
                    self.search_result[_url] = self.__get_download_info()
                    if new_info_callback is not None:
                        new_info_callback(_url, self.search_result[_url])
                except:
                    pass
                if signal_func is not None and signal_func() == 'stop':
                    self.is_searching = False
                    return
        self.is_searching = False

    def until_get(self, url, xpath, timeout=10):
        self.driver.get(url)
        time.sleep(0.2)
        while timeout > 0 and self.find(xpath) is None:
            time.sleep(0.2)
            timeout -= 0.2
        if timeout <= 0:
            raise Exception('until get timeout: %s' % url)

    def __get_download_info(self):
        import datetime
        coin_el = self.find('//div[@class="dl_download_box dl_download_l"]/label/em')
        coin = -1 if coin_el is None else int(coin_el.text.strip())
        date_str = self.find('//strong[@class="size_box"]/span[1]').text.strip()[:10]
        info = {
            'id': self.find('//div[@id="download_top"]').get_attribute('data-id'),
            'title': self.find('//dl[@class="download_dl"]/dd/h3').get_attribute('title'),
            'description': self.find('//div[@class="pre_description"]').text.strip(),
            'type': self.find('//dl[@class="download_dl"]/dt/img').get_attribute('title'),
            'tag': self.find('//a[@class="tag"]').text.strip(),
            'coin': coin,
            'stars': self.find_count('//span[@class="starts"]//i[@class="fa fa-star yellow"]'),
            'upload_date': datetime.datetime.strptime(date_str, "%Y-%m-%d"),
            'size': self.find('//strong[@class="size_box"]/span[2]/em').text.strip(),
        }
        return info

    def __clear_download_dir(self):
        for f in os.listdir(self.download_path):
            os.remove(os.path.join(self.download_path, f))

    def __get_tmp_download_file(self):
        files = os.listdir(self.download_path)
        if len(files) <= 0:
            raise Exception('下载文件不存在！')
        elif len(files) > 1:
            raise Exception('下载目录存在多余文件！')
        return os.path.join(self.download_path, files[0])

    def __wait_for_download(self):
        time.sleep(3)  # wait for create file
        wait_time = 20
        last_size = os.path.getsize(self.__get_tmp_download_file())
        while wait_time > 0 and self.__get_tmp_download_file().endswith('.crdownload'):
            cur_size = os.path.getsize(self.__get_tmp_download_file())
            if cur_size == last_size:
                wait_time -= 1
            else:
                wait_time = 20
            time.sleep(1)

        if self.__get_tmp_download_file().endswith('.crdownload'):
            raise Exception('文件下载失败，请重试！')

    def __zip_file(self, _id):
        import zipfile
        zip_path = os.path.join(self.zip_save_path, "{0}.zip".format(_id))
        if os.path.exists(zip_path):
            os.remove(zip_path)
        with zipfile.ZipFile(zip_path, mode='w') as zipf:
            file_path = self.__get_tmp_download_file()
            zipf.write(file_path, os.path.basename(file_path))

    def __get_file_name_in_zip_file(self, _id):
        import zipfile
        zip_path = os.path.join(self.zip_save_path, "{0}.zip".format(_id))
        zip_f = zipfile.ZipFile(zip_path)
        files = zip_f.namelist()
        if len(files) != 1:
            return None
        return files[0]

    def __already_download(self, _id):
        zip_path = os.path.join(self.zip_save_path, "{0}.zip".format(_id))
        if os.path.exists(zip_path):
            file_name = self.__get_file_name_in_zip_file(_id)
            if file_name is not None and not file_name.endswith('.crdownload'):
                return True
        return False

    def __save_to_db(self, info):
        if not db_helper.exist_download(info['id']):
            db_helper.insert_download(info)

    def __download_result(self, success, message='', info=None):
        return {'success': success, 'message': message, 'info': info, }

    def get_user_info(self):
        try:
            self.get('https://download.csdn.net/my/vip')
            time.sleep(2)
            name = self.find('//div[@class="name"]/span').text.strip()
            is_vip = self.find('//a[@class="btn_vipsign"]') is None
            info = {
                'name': name,
                'vip': is_vip
            }
            if is_vip:
                remain = self.find('//div[@class="cardr"]/ul/li/span').text.strip()
                date = self.find('//div[@class="cardr"]/ul/li[2]/span').text.strip()
                info['remain'] = remain
                info['date'] = date
            else:
                remain = self.find('//ul[@class="datas clearfix"]//span').text.strip()
                info['remain'] = remain
            return info
        except:
            import traceback
            traceback.print_exc()
            return None
