from django.shortcuts import render
from psyduck_search.crawler import Crawler
from django.http import HttpResponse
import json
import time


class Search:
    result = None
    crawler = None
    out_tag = None
    current = 0
    total = 0
    keyword = ''
    uuid = ''
    sort_type = 0
    search_deep = 0
    start_time = None

    def __init__(self, uuid):
        self.uuid = uuid
        self.crawler = Crawler()
        self.result = {}

    def __progress_callback(self, i, n):
        self.current = i
        self.total = n

    def __new_info_callback(self, info):
        if info['coin'] == 0 and info['url'] not in self.result.keys():
            self.result[info['url']] = info

    def __finish_callback(self):
        cost = '%.2f' % (time.process_time() - self.start_time)
        log(self.uuid, f'搜索【{self.keyword}】完成，耗时：{cost}秒')
        self.current = 0
        self.total = 0
        self.keyword = ''

    def is_running(self):
        return self.crawler.is_running

    def search(self, keyword, pages):
        while self.is_running():
            self.crawler.signal_stop()
            time.sleep(0.1)
        log(self.uuid, f'开始搜索【{keyword}】，搜索深度：{pages}页')
        self.start_time = time.process_time()
        self.keyword = keyword
        self.search_deep = pages
        self.crawler.search_pages = pages
        self.crawler.async_search(keyword, self.__new_info_callback, self.__progress_callback, self.__finish_callback)


search_dict: {str, Search} = {}


def _response(state, result_count=0, p_i=0, p_n=0, result_json=''):
    return HttpResponse(
        json.dumps({'state': state, 'result_count': result_count, 'p_i': p_i, 'p_n': p_n, 'result_json': result_json}),
        content_type='application/json')


def search(request):
    return render(request, 'index.html')


def search_progress(request):
    try:
        uuid = request.GET.get('murmur', '')
        act = request.GET.get('act', '')
        args = request.GET.get('args', '')
        if uuid == '':
            return _response('none')

        if uuid not in search_dict.keys():
            search_dict[uuid] = Search(uuid)

        sr: Search = search_dict[uuid]
        if act == 'begin':
            keyword = args.split('_%split%_')[0]
            sort_type = int(args.split('_%split%_')[1])
            search_deep = int(args.split('_%split%_')[2])
            if sr.keyword != keyword or sr.search_deep != search_deep:
                sr.search(keyword, search_deep)
                sr.sort_type = sort_type
        elif act == 'clear':
            log(uuid, 'clear result')
            sr.result = {}

        result_json = ''
        if act == 'result' or sr.out_tag != len(sr.result):
            result_json = json.dumps(sr.result)
            sr.out_tag = len(sr.result)

        state = ''
        if sr.is_running():
            state = 'search'

        return _response(state, len(sr.result), sr.current, sr.total, result_json)
    except ConnectionResetError:
        pass


def log(uuid, msg):
    import datetime
    now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 现在
    print('[{}]：{} 于 ({})'.format(uuid[0:4], msg, now_time))
