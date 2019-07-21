from django.shortcuts import render
from psyduck_export.helper import Helper
from django.http import HttpResponse
import json
from threading import Thread
import time


class Export:
    uuid = ''
    thread = None
    helper = None
    state = ''
    msg = ''
    signal = ''
    signal_args = None

    def __init__(self, uuid):
        self.uuid = uuid

    def reset_signal(self):
        self.signal = ''
        self.signal_args = {}

    def dispose_helper(self):
        if self.helper is not None and self.helper.is_ready:
            self.helper.dispose()
        self.helper = None

    def reset(self):
        self.reset_signal()
        self.dispose_helper()
        self.msg = ''
        self.state = ''

    def set_signal(self, signal, args=None):
        self.signal = signal
        self.signal_args = args

    def start(self):
        self.state = 'start'
        self.thread = Thread(target=self.__export_thread)
        self.thread.start()

    def __export_thread(self):
        self.helper = Helper(self.uuid)
        self.state = 'helper_init'
        self.helper.init()
        self.state = 'login'
        _login_msg = ''
        while _login_msg != '' or not self.helper.check_login():
            self.state = 'wait_for_login'
            while self.signal != 'login':
                time.sleep(0.1)
            phone_num = self.signal_args['phone_num']
            verify_code = self.signal_args['verify_code']
            self.state = 'login'
            _login_msg = self.helper.login(phone_num, verify_code)
            self.msg = _login_msg
            self.reset_signal()
        self.msg = ''

        self.state = 'wait_for_export'
        while self.signal != 'export':
            time.sleep(0.1)
        self.reset_signal()
        self.state = 'export'
        self.helper.export_all()
        self.state = 'finish'
        self.dispose_helper()


exports: {str, Export} = {}


def dispose_all():
    for u in exports:
        u.reset()


def _response(state, msg=''):
    return HttpResponse(json.dumps({'state': state, 'msg': msg}), content_type='application/json')


def export(request):
    return render(request, 'index.html')


def export_progress(request):
    uuid = request.GET.get('murmur', '')
    act = request.GET.get('act', '')
    args = request.GET.get('args', '')
    if uuid == '':
        return _response('none')

    if uuid not in exports.keys():
        exports[uuid] = Export(uuid)

    exp = exports[uuid]
    if exp.state == '' and act == 'start':
        exp.start()
    elif exp.state == 'wait_for_login' and act == 'get_verify_code':
        exp.set_signal('get_verify_code', {args})
    elif exp.state == 'wait_for_login' and act == 'login':
        _type = args.split('_')[0]
        _phone_num = args.split('_')[1]
        _verify_code = args.split('_')[2]
        exp.set_signal('login', {'phone_num': _phone_num, 'verify_code': _verify_code})
    elif exp.state == 'wait_for_export' and act == 'export':
        exp.set_signal('export')
    elif exp.state == 'export':
        cur = exp.helper.export_index + 1
        total = len(exp.helper.export_url_list)
        if total == 0:
            cur = 1
            total = 1
            name = '收集资源中...'
            url = ''
        else:
            name = exp.helper.export_name_list[exp.helper.export_index]
            url = exp.helper.export_url_list[exp.helper.export_index]
        exp.msg = '{}_{}_{}_{}'.format(cur, total, name, url)
    elif exp.state == 'finish' and act == 'reset':
        exp.reset()

    return _response(exp.state, exp.msg)
