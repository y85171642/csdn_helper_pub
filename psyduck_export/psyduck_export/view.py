from django.shortcuts import render
from psyduck_export.helper import Helper
from django.http import HttpResponse
import json
from threading import Thread
import time


class User:
    uuid = ''
    thread = None
    helper = None
    step = ''
    progress = 0
    msg = ''
    signal = ''
    args = {}

    def __init__(self, uuid):
        self.uuid = uuid


users: {str, User} = {}


def _export_thread(uuid):
    u = users[uuid]
    u.helper = Helper(uuid)
    h: Helper = u.helper
    u.step = 'start'
    h.init()
    u.step = 'login'
    while not h.check_login():
        while u.signal != 'login':
            time.sleep(100)
        u.signal = ''
        h.login(u.args['phone_num'], u.args['verify_code'])
    u.step = 'export'
    while not u.signal != 'export':
        time.sleep(100)
    u.signal = ''
    h.export_all()
    u.step = 'dispose'
    h.dispose()


def _export_init(uuid):
    users[uuid] = User(uuid)


def _export_start(uuid):
    users[uuid].thread = Thread(target=_export_thread, args=(uuid,))
    users[uuid].thread.start()


def _response(step, msg=''):
    return HttpResponse(json.dumps({'step': step, 'msg': msg}), content_type='application/json')


def export(request):
    context = {'step': 'need_init'}
    return render(request, 'index.html', context)


def export_progress(request):
    uuid = request.GET.get('murmur', '')
    act = request.GET.get('act', '')
    if uuid == '':
        return _response('none')

    if act == 'init':
        if uuid not in users.keys():
            _export_init(uuid)
        return _response('init')

    if uuid not in users.keys():
        return _response('need_init')

    u = users[uuid]
    if act == 'start':
        _export_start(uuid)
        return _response('starting')

    if act == 'starting':
        if u.helper.is_ready:
            if u.step == 'login':
                return _response('login')
            else:
                return _response('export')
        else:
            return _response('starting')

    if act == 'login':
        if u.step == 'login':
            return _response('login')
        else:
            return _response('export')

    if act == 'export':
        u.signal = 'export'
        return _response('process')

    if act == 'progress':
        return _response('process')

    return _response('none')
