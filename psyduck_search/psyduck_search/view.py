from django.shortcuts import render
from psyduck_search.crawler import Crawler
from django.http import HttpResponse
import json
import time
from psyduck_search import db_helper


class Search:
    result = None
    crawler = None
    out_tag = None
    current = 0
    total = 0
    keyword = ''
    uuid = ''
    pages = 0
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
            if not db_helper.exist_download(info['id']):
                db_helper.insert_download(info)

    def __finish_callback(self):
        cost = '%.2f' % (time.time() - self.start_time)
        log(self.uuid, f'搜索【{self.keyword}】完成，共{len(self.result)}条结果，耗时：{cost}秒')
        db_helper.insert_log(
            {'uuid': self.uuid, 'keyword': self.keyword, 'pages': self.pages, 'result': len(self.result), 'cost': cost})
        self.current = 0
        self.total = 0
        self.pages = 0
        self.keyword = ''

    def is_running(self):
        return self.crawler.is_running

    def search(self, keyword, pages):
        while self.is_running():
            self.crawler.signal_stop()
            time.sleep(0.1)
        log(self.uuid, f'开始搜索【{keyword}】，搜索深度：{pages}页')
        self.start_time = time.time()
        self.keyword = keyword
        self.pages = pages
        self.crawler.search_pages = pages
        self.crawler.async_search(keyword, self.__new_info_callback, self.__progress_callback, self.__finish_callback)


search_dict: {str, Search} = {}


def _response(state, result_count=0, p_i=0, p_n=0, result_json=''):
    return HttpResponse(
        json.dumps({'state': state, 'result_count': result_count, 'total_count': db_helper.count_download(),
                    'p_i': p_i, 'p_n': p_n, 'result_json': result_json}),
        content_type='application/json')


def search(request):
    return render(request, 'index.html')


def search_progress(request):
    if request.method == 'GET':
        return HttpResponse()

    uuid = request.POST.get('murmur', '')
    act = request.POST.get('act', '')
    keyword = request.POST.get('keyword', '')
    pages = request.POST.get('pages', 0)
    if uuid == '':
        return _response('none')

    if uuid not in search_dict.keys():
        search_dict[uuid] = Search(uuid)

    sr: Search = search_dict[uuid]
    if act == 'begin':
        if sr.keyword != keyword or sr.pages != pages:
            sr.search(keyword, pages)
    elif act == 'clear':
        log(uuid, '清空结果')
        sr.result = {}

    result_json = ''
    if act == 'result' or sr.out_tag != len(sr.result):
        result_json = json.dumps(sr.result)
        sr.out_tag = len(sr.result)

    state = ''
    if sr.is_running():
        state = 'search'

    return _response(state, len(sr.result), sr.current, sr.total, result_json)


def log(uuid, msg):
    import datetime
    now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 现在
    print('[{}]：{} 于 ({})'.format(uuid[0:6], msg, now_time))
