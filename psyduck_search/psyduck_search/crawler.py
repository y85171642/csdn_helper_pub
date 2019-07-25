import requests
from urllib import parse
from threading import Thread


class Crawler:
    progress_callback = None
    new_info_callback = None
    finish_callback = None
    total = 0
    current = 0
    search_pages = 10
    is_running = False
    signal = ''
    session = requests.session()

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

    def get_info(self, url):
        req = self.session.get(url)
        encodings = requests.utils.get_encodings_from_content(req.text)
        if encodings:
            encoding = encodings[0]
        else:
            encoding = req.apparent_encoding
        content = req.content.decode(encoding, 'replace')
        if content.find('<div class="download_top_wrap clearfix">') == -1:
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

    def __search(self, keyword):
        self.is_running = True
        host = 'download.csdn.net'
        urls = []
        keyword = parse.quote(keyword)
        for i in range(0, self.search_pages):
            _url = f'http://www.baidu.com/s?wd={keyword}&pn={i * 10}&oq={keyword}&ct=2097152&ie=utf-8&si={host}'
            _url += '&rsv_pq=e0ae025a0005e6cf&rsv_t=85b4xx%2BZgprKkkYDvOyIJXGUX4YfyI2YVdl4z5i8ZTIszo7fqwFyxgbeNwI' \
                    '&rqlang=cn&rsv_enter=1&rsv_dl=tb&rsv_sug3=1&rsv_sug1=1&rsv_sug7=100&rsv_sug2=0&inputT=14' \
                    '&rsv_sug4=735&rsv_sug=2'
            if self.signal == 'stop':
                break
            content = self.session.get(_url).content.decode('utf-8')
            will_break = False
            if content.find('class="n">下一页&gt;</a>') == -1:
                self.total -= (self.search_pages - i - 1) * 10
                will_break = True

            content = self.simplify_html(content)
            _urls = self.get_all_cache_urls(content)
            # print(f'page: {i}, result: {len(_urls)}')
            self.total -= 10
            self.total += len(_urls)
            for _u in _urls:
                if _u in urls:
                    self.current += 1
                    self.__progress_callback()
                    continue
                if self.signal == 'stop':
                    will_break = True
                    break
                info = self.get_info(_u)
                if info is not None:
                    self.__new_info_callback(info)
                self.current += 1
                self.__progress_callback()
            if len(_urls) == 0:
                self.__progress_callback()
            if will_break:
                break
        self.is_running = False
        self.signal = ''
        self.__finish_callback()

    def __progress_callback(self):
        if self.progress_callback is not None:
            self.progress_callback(self.current, self.total)

    def __new_info_callback(self, info):
        if self.new_info_callback is not None:
            self.new_info_callback(info)

    def __finish_callback(self):
        if self.finish_callback is not None:
            self.finish_callback()

    def async_search(self, keyword, new_info_callback=None, progress_callback=None, finish_callback=None):
        self.total = self.search_pages * 10
        self.current = 0
        self.new_info_callback = new_info_callback
        self.progress_callback = progress_callback
        self.finish_callback = finish_callback
        Thread(target=self.__search, args=(keyword,)).start()


def _new_info_callback(info):
    if info['coin'] == 0:
        print(info['url'])


def _progress_callback(i, n):
    print(f'progress: {i}/{n}')


def main():
    Crawler().async_search('voodoo f', _new_info_callback, _progress_callback)


if __name__ == '__main__':
    main()
