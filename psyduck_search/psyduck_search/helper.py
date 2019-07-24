import selenium.webdriver
import time
import platform
import os
from psyduck_search import config
from psyduck_search import db_helper


class Helper:
    is_ready = False
    driver = None
    driver_path = None
    option_path = None
    data_path = None
    data_root = None
    uuid = None
    is_searching = False
    search_result = {}
    search_total = 0
    search_index = 0

    def __init__(self, uuid):
        self.uuid = uuid

    @staticmethod
    def _create_dir(_dir):
        _dir = config.frozen_path(_dir)
        if not os.path.exists(_dir):
            os.mkdir(_dir)

    @staticmethod
    def _get_driver_name(name='chromedriver'):
        if platform.system() == 'Windows' and not name.endswith('.exe'):
            name += ".exe"
        return name

    def __settings(self):
        self.is_ready = False
        self.data_root = config.frozen_path('user_data')
        self.data_path = config.frozen_path(os.path.join(self.data_root, self.uuid))
        self.driver_path = config.frozen_path(os.path.join(self.data_path, Helper._get_driver_name()))
        self.option_path = config.frozen_path(os.path.join(self.data_path, 'chrome_option'))

    def __prepare(self):
        Helper._create_dir(self.data_root)
        Helper._create_dir(self.data_path)
        import shutil
        _raw_driver_path = config.frozen_path(os.path.join('chrome_driver', Helper._get_driver_name()))
        _driver_dir = os.path.dirname(self.driver_path)
        Helper._create_dir(_driver_dir)
        os.chmod(_driver_dir, 0o777)
        shutil.copyfile(_raw_driver_path, self.driver_path)

    def __selenium_init(self):
        options = selenium.webdriver.ChromeOptions()
        options.add_argument("user-data-dir=" + self.option_path)
        options.add_argument('disable-infobars')
        options.add_argument('--mute-audio')
        options.add_argument('--disable-gpu')
        options.add_argument("--log-level=3")
        options.add_argument("--headless")

        prefs = {
            "disable-popup-blocking": False,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
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
        self.reset_timeout()

    def init(self):
        self.__settings()
        self.__prepare()
        self.__selenium_init()
        self.is_ready = True

    def reset_timeout(self):
        self.driver.set_page_load_timeout(10)
        self.driver.set_script_timeout(10)

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

    def dispose(self):
        if self.driver is not None:
            self.driver.stop_client()
            self.driver.quit()
            self.driver = None
        self.is_ready = False
        self.is_searching = False
        self.search_result = {}
        self.search_index = 0
        self.search_total = 0

    def search(self, keyword, sort_type=1, source_type=10, area=0, signal_func=None, new_info_callback=None):
        self.is_searching = True
        self.search_total = 0
        self.search_index = 0
        self.search_result = {}
        from urllib import parse
        keyword = parse.quote(keyword)

        def _page_url(page):
            return 'https://download.csdn.net/psearch/{area}/{source}/0/{sort}/1/{keyword}/{page}' \
                .format(area=area, source=source_type, sort=sort_type, keyword=keyword, page=page)

        try:
            self.get_until(_page_url(1), '//div[@class="album_detail_wrap"]')
        except:
            self.is_searching = False
            return

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

        self.search_total = 20 * total_page

        for i in range(1, total_page + 1):
            self.get_until(_page_url(i), '//div[@class="album_detail_wrap"]')

            if signal_func is not None and signal_func() == 'stop':
                self.is_searching = False
                return

            _urls = []
            self.search_total -= 20
            for el in self.find_all('//a[@class="album_detail_title"]'):
                _url = el.get_attribute('href')
                if _url not in self.search_result.keys():
                    _urls.append(_url)
                    self.search_total += 1

            for _url in _urls:
                self.search_index += 1
                try:
                    self.get_until(_url, '//strong[@class="size_box"]/span[1]', 2)
                    self.search_result[_url] = self.__get_download_info()
                    if new_info_callback is not None:
                        new_info_callback(_url, self.search_result[_url])
                except:
                    pass
                if signal_func is not None and signal_func() == 'stop':
                    self.is_searching = False
                    return
        self.is_searching = False

    def get_until(self, url, xpath, timeout=10):
        self.driver.get(url)
        time.sleep(0.5)
        while timeout > 0 and self.find(xpath) is None:
            time.sleep(0.5)
            timeout -= 0.5
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
