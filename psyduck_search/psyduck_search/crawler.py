import requests
from urllib import parse
from threading import Thread
import time


class Crawler:
    progress_callback = None
    new_info_callback = None
    finish_callback = None
    total = 0
    current = 0
    search_pages = 10
    is_running = False
    keyword = ''
    signal = ''
    _cache_urls = []
    session = None

    def __init__(self):
        self.session = requests.session()

    def signal_stop(self):
        self.signal = 'stop'

    def simplify_html(self, html):
        begin = html.find('<div class="result c-container "')
        end = html.rfind('<div style="clear:both;height:0;"></div>')
        return "<div>" + html[begin:end - 1]

    def get_all_cache_urls(self, html):
        urls = []
        _begin = html.find('http://cache.baiducontent.com/')
        while _begin != -1:
            _end = html.find('"', _begin + 20)
            urls.append(html[_begin:_end])
            _begin = html.find('http://cache.baiducontent.com/', _end)
        return urls

    def get_url(self, url):
        try:
            req = self.session.get(url)
            return req
        except:
            return None

    def get_info(self, url):
        req = self.get_url(url)
        encodings = requests.utils.get_encodings_from_content(req.text)
        if encodings:
            encoding = encodings[0]
        else:
            encoding = req.apparent_encoding
        content = req.content.decode(encoding, 'replace')
        st_tag = content.find('<div class="download_top_wrap clearfix">')
        if st_tag == -1:
            return None

        title = None
        description = None
        _url = None
        coin = None
        upload_date = None
        _b = content.find('<h3 title=\'')
        if _b != -1:
            _e = content.find('\'', _b + 11)
            title = content[_b + 11:_e].strip()

        _b = content.find('<div class="pre_description">')
        if _b != -1:
            _e = content.find('</div>', _b)
            description = content[_b + 29:_e].strip()

        _b = content.find('<base href="')
        if _b != -1:
            _e = content.find('">', _b + 12)
            _url = content[_b + 12:_e]
        else:
            _b = content.find('<link rel="canonical" href="')
            if _b != -1:
                _e = content.find('">', _b + 28)
                _url = content[_b + 28:_e]

        _e = content.find('</em>积分/C币')
        if _e != -1:
            _b = content.rfind('>', 0, _e)
            coin = int(content[_b + 1:_e])

        _b = content.find('<strong class="size_box">')
        if _b != -1:
            _b = content.find('<span>', _b)
            _e = content.find('上传', _b)
            upload_date = content[_b + 6:_e].strip()

        if title is None or description is None or _url is None or coin is None or upload_date is None:
            return None
        return {'title': title, 'description': description, 'url': _url, 'coin': coin, 'upload_date': upload_date}

    def __search_one_page(self, page_index):
        host = 'download.csdn.net'
        keyword = parse.quote(self.keyword)
        _url = f'http://www.baidu.com/s?wd={keyword}&pn={page_index * 10}&oq={keyword}&ct=2097152&ie=utf-8&si={host}'
        _url += '&rsv_pq=e0ae025a0005e6cf&rsv_t=85b4xx%2BZgprKkkYDvOyIJXGUX4YfyI2YVdl4z5i8ZTIszo7fqwFyxgbeNwI' \
                '&rqlang=cn&rsv_enter=1&rsv_dl=tb&rsv_sug3=1&rsv_sug1=1&rsv_sug7=100&rsv_sug2=0&inputT=14' \
                '&rsv_sug4=735&rsv_sug=2'

        req = self.get_url(_url)
        if req is None:
            self.total -= 10
            return

        content = req.content.decode('utf-8')
        content = self.simplify_html(content)
        _urls = self.get_all_cache_urls(content)
        self.total -= 10
        self.total += len(_urls)
        if len(_urls) == 0:
            self.__progress_callback()
            return

        _cache_n = 0
        for _u in _urls:
            if self.signal == 'stop':
                self.total -= 10 - _cache_n
                self.__progress_callback()
                break
            _cache_n += 1
            if _u not in self._cache_urls:
                self._cache_urls.append(_u)
                info = self.get_info(_u)
                time.sleep(0.5)
                if info is not None:
                    self.__new_info_callback(info)
            self.current += 1
            self.__progress_callback()

    def __progress_callback(self):
        if self.progress_callback is not None:
            self.progress_callback(self.current, self.total)

    def __new_info_callback(self, info):
        if self.new_info_callback is not None:
            self.new_info_callback(info)

    def __finish_callback(self):
        if self.finish_callback is not None:
            self.finish_callback()

    def __start_threads(self):
        _threads = []

        def _alive_thread_count():
            _alive_count = 0
            for __t in _threads:
                if __t.is_alive():
                    _alive_count += 1
            return _alive_count

        for i in range(0, self.search_pages):
            if self.signal == 'stop':
                self.total -= self.search_pages * (10 - i)
                break
            _t = Thread(target=self.__search_one_page, args=(i,))
            _t.start()
            _threads.append(_t)
            time.sleep(0.1 * _alive_thread_count())

        while _alive_thread_count() > 0:
            time.sleep(0.5)

        self.is_running = False
        self.signal = ''
        self.keyword = ''
        self.__finish_callback()

    def async_search(self, keyword, new_info_callback=None, progress_callback=None, finish_callback=None):
        self.is_running = True
        self.keyword = keyword
        self.signal = ''
        self.total = self.search_pages * 10
        self.current = 0
        self.new_info_callback = new_info_callback
        self.progress_callback = progress_callback
        self.finish_callback = finish_callback
        Thread(target=self.__start_threads).start()


def _new_info_callback(info):
    if info['coin'] == 0:
        print(info['url'])


def _progress_callback(i, n):
    print(f'progress: {i}/{n}')


def _finish_callback():
    print(f'progress: finish')


def main():
    c = Crawler()
    c.search_pages = 40
    c.async_search('voodoo', _new_info_callback, _progress_callback, _finish_callback)


if __name__ == '__main__':
    main()
