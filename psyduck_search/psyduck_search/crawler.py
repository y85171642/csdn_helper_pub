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
    session = None

    get_url_sleep = 0.1
    page_items = 10
    max_threads = 100

    __cache_urls = []
    __threads = []

    def __init__(self):
        self.session = requests.session()

    def __simplify_html(self, html):
        begin = html.find('<div class="result c-container "')
        end = html.rfind('<div style="clear:both;height:0;"></div>')
        return "<div>" + html[begin:end - 1]

    def __get_all_cache_urls(self, html):
        urls = []
        _begin = html.find('http://cache.baiducontent.com/')
        while _begin != -1:
            _end = html.find('"', _begin + 20)
            urls.append(html[_begin:_end])
            _begin = html.find('http://cache.baiducontent.com/', _end)
        return urls

    def __get_url(self, url, retry=3):
        req = None
        while retry > 0:
            try:
                req = self.session.get(url, timeout=5)
                encodings = requests.utils.get_encodings_from_content(req.text)
                if encodings:
                    encoding = encodings[0]
                else:
                    encoding = req.apparent_encoding
                content = req.content.decode(encoding, 'replace')
                time.sleep(self.get_url_sleep)
                return content
            except:
                pass
                # print(f'retry({retry}) -> {url}')
            finally:
                if req is not None:
                    req.close()
            retry -= 1
            time.sleep(self.get_url_sleep)
        return None

    def __get_info(self, url):
        content = self.__get_url(url)
        if content is None:
            return None

        st_tag = content.find('<div class="download_top_wrap clearfix">')
        if st_tag == -1:
            return None

        _id = None
        title = None
        description = None
        _url = None
        coin = None
        upload_date = None
        stars = None

        _b = content.find('<h3 title=\'')
        if _b != -1:
            _e = content.find('\'', _b + 11)
            if _e != -1:
                title = content[_b + 11:_e].strip()

        _b = content.find('<div class="pre_description">')
        if _b != -1:
            _e = content.find('</div>', _b)
            if _e != -1:
                description = content[_b + 29:_e].strip()

        _b = content.find('<base href="')
        if _b != -1:
            _e = content.find('">', _b + 12)
            if _e != -1:
                _url = content[_b + 12:_e]
        else:
            _b = content.find('<link rel="canonical" href="')
            if _b != -1:
                _e = content.find('">', _b + 28)
                if _e != -1:
                    _url = content[_b + 28:_e]

        _e = content.find('</em>积分')
        if _e != -1:
            _b = content.rfind('<em>', 0, _e)
            if _b != -1:
                _coin_str = ''
                for c in content[_b + 4:_e]:
                    if '0' <= c <= '9':
                        _coin_str += c
                if _coin_str != '':
                    coin = int(_coin_str)

        _b = content.find('<strong class="size_box">')
        if _b != -1:
            _b = content.find('<span>', _b)
            _e = content.find('上传', _b)
            if _b != -1 and _e != -1:
                upload_date = content[_b + 6:_e].strip()

        _b = content.find('<span class="starts">')
        if _b != -1:
            _e = content.find('</span>', _b + 20)
            if _e != -1:
                _center = content[_b: _e]
                stars = _center.count('fa fa-star yellow')

        if _url is not None:
            _b = _url.rfind('/')
            if _b != -1:
                _id = _url[_b + 1:]

        if _id is None or title is None or description is None \
                or _url is None or coin is None or upload_date is None or stars is None:
            return None
        return {'id': _id, 'title': title, 'description': description, 'url': _url, 'coin': coin, 'stars': stars,
                'upload_date': upload_date}

    def __get_one_item(self, url):
        if url in self.__cache_urls:
            pass
            # print('duplicate url !!!')
        else:
            self.__cache_urls.append(url)
            info = self.__get_info(url)
            if info is not None:
                self.__new_info_callback(info)
        self.current += 1
        self.__progress_callback()

    def __search_one_page(self, page_index):
        host = 'download.csdn.net'
        keyword = parse.quote(self.keyword)
        _url = f'http://www.baidu.com/s?wd={keyword}&pn={page_index * 10}&oq={keyword}&ct=2097152&ie=utf-8&si={host}'
        _url += '&rsv_pq=e0ae025a0005e6cf&rsv_t=85b4xx%2BZgprKkkYDvOyIJXGUX4YfyI2YVdl4z5i8ZTIszo7fqwFyxgbeNwI' \
                '&rqlang=cn&rsv_enter=1&rsv_dl=tb&rsv_sug3=1&rsv_sug1=1&rsv_sug7=100&rsv_sug2=0&inputT=14' \
                '&rsv_sug4=735&rsv_sug=2'

        content = self.__get_url(_url)
        if content is None:
            self.total -= self.page_items
            return

        content = self.__simplify_html(content)
        _urls = self.__get_all_cache_urls(content)
        self.total -= self.page_items
        self.total += len(_urls)
        for _url in _urls:
            self.__get_one_item(_url)

    def __progress_callback(self):
        if self.progress_callback is not None:
            self.progress_callback(self.current, self.total)

    def __new_info_callback(self, info):
        if self.new_info_callback is not None:
            self.new_info_callback(info)

    def __finish_callback(self):
        if self.finish_callback is not None:
            self.finish_callback()

    def __alive_thread_count(self):
        _alive_count = 0
        for __t in self.__threads:
            if __t.is_alive():
                _alive_count += 1
        return _alive_count

    def __start_thread(self, target, args):
        while self.__alive_thread_count() >= self.max_threads:
            time.sleep(0.5)
        _t = Thread(target=target, args=args)
        self.__threads.append(_t)
        _t.start()

    def __mgr_thread(self):
        for i in range(0, self.search_pages):
            if self.signal == 'stop':
                self.total -= self.search_pages * (self.page_items - i)
                break
            self.__start_thread(target=self.__search_one_page, args=(i,))

        while self.__alive_thread_count() > 0:
            time.sleep(0.5)

        self.is_running = False
        self.__finish_callback()

    def async_search(self, keyword, new_info_callback=None, progress_callback=None, finish_callback=None):
        self.is_running = True
        self.keyword = keyword
        self.signal = ''
        self.total = self.search_pages * self.page_items
        self.current = 0
        self.new_info_callback = new_info_callback
        self.progress_callback = progress_callback
        self.finish_callback = finish_callback
        self.__cache_urls = []
        self.__threads = []
        Thread(target=self.__mgr_thread).start()

    def signal_stop(self):
        self.signal = 'stop'


def _new_info_callback(info):
    if info['coin'] == 0:
        print(info)
    global _total_info_count
    _total_info_count += 1


def _progress_callback(i, n):
    global _total_result_count
    _total_result_count = n
    # print(f'progress: {i}/{n}')


def _finish_callback():
    print(f'progress: finish')
    print(f'cost time: {time.time() - _program_start_time:.2f}s')
    print(f'info/total: {_total_info_count}/{_total_result_count}')


_total_info_count = 0
_program_start_time = 0
_total_result_count = 0


def main():
    global _program_start_time
    _program_start_time = time.time()
    c = Crawler()
    c.search_pages = 60
    c.async_search('python', _new_info_callback, _progress_callback, _finish_callback)


if __name__ == '__main__':
    main()
