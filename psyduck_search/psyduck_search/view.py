from django.shortcuts import render
from psyduck_search.helper import Helper
from django.http import HttpResponse
import json
from threading import Thread

import datetime


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return json.JSONEncoder.default(self, obj)


class Search:
    uuid = ''
    thread = None
    helper = None
    state = ''
    msg = ''
    signal = ''
    keyword = ''
    sort_type = ''
    source_type = ''
    tag = -1
    result = {}

    def __init__(self, uuid):
        self.uuid = uuid

    def reset_signal(self):
        self.signal = ''

    def clear_result(self):
        self.result = {}

    def dispose_helper(self):
        if self.helper is not None and self.helper.is_ready:
            self.helper.dispose()
        self.helper = None

    def reset(self):
        self.reset_signal()
        self.dispose_helper()
        self.remove_user_data()
        self.keyword = ''
        self.sort_type = ''
        self.source_type = ''
        self.msg = ''
        self.state = ''

    def remove_user_data(self):
        import os.path
        import shutil
        from psyduck_search import config
        try:
            path = config.frozen_path('user_data/{}'.format(self.uuid))
            if os.path.exists(path):
                shutil.rmtree(path)
        except:
            import traceback
            traceback.print_exc()

    def set_signal(self, signal):
        self.signal = signal

    def start(self):
        self.state = 'start'
        self.thread = Thread(target=self.__export_thread)
        self.thread.start()

    def __export_thread(self):
        self.helper = Helper(self.uuid)
        self.state = 'init'
        self.helper.init()
        self.state = 'search'

        def __get_signal():
            return self.signal

        def __new_info(url, info):
            if info['coin'] == 0 and url not in self.result.keys():
                self.result[url] = info

        self.helper.search(keyword=self.keyword, sort_type=self.sort_type, source_type=self.source_type,
                           signal_func=__get_signal, new_info_callback=__new_info)
        while self.signal == 'stop':
            self.reset_signal()
            self.helper.search(keyword=self.keyword, sort_type=self.sort_type, source_type=self.source_type,
                               signal_func=__get_signal, new_info_callback=__new_info)
        self.reset()
        log(self.uuid, 'search finish')


search_dict: {str, Search} = {}


def dispose_all():
    for u in search_dict.values():
        u.reset()


_gc_counter = 0


def _auto_gc():
    global _gc_counter
    if _gc_counter > 100:
        import gc
        gc.collect()
        _gc_counter = 0
    _gc_counter += 1


def _response(state, result_count=0, p_i=0, p_n=0, result_json=''):
    _auto_gc()
    return HttpResponse(
        json.dumps({'state': state, 'result_count': result_count, 'p_i': p_i, 'p_n': p_n, 'result_json': result_json}),
        content_type='application/json')


def search(request):
    return render(request, 'index.html')


def search_progress(request):
    uuid = request.GET.get('murmur', '')
    act = request.GET.get('act', '')
    args = request.GET.get('args', '')
    if uuid == '':
        return _response('none')

    if uuid not in search_dict.keys():
        search_dict[uuid] = Search(uuid)

    sr = search_dict[uuid]
    if act == 'begin':
        keyword = args.split('_%split%_')[0]
        sort_type = args.split('_%split%_')[1]
        source_type = args.split('_%split%_')[2]
        if sr.keyword != keyword or sr.sort_type != sort_type or sr.source_type != source_type:
            log(uuid, 'begin search {}'.format(keyword))
            sr.keyword = keyword
            sr.source_type = source_type
            sr.sort_type = sort_type
            if sr.state != '':
                sr.set_signal('stop')
            else:
                sr.start()
    elif act == 'clear':
        log(uuid, 'clear result')
        sr.clear_result()

    result_json = ''
    if act == 'result' or sr.tag != len(sr.result):
        result_json = json.dumps(sr.result, cls=DateEncoder)
        sr.tag = len(sr.result)

    p_i = 0
    p_n = 0
    if sr.helper is not None:
        p_i = sr.helper.search_index
        p_n = sr.helper.search_total

    return _response(sr.state, len(sr.result), p_i, p_n, result_json)


def log(uuid, msg):
    import datetime
    now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 现在
    print('[{}]: {} at ({})'.format(uuid, msg, now_time))
