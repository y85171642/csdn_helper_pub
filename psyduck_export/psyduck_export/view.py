from django.shortcuts import render
from psyduck_export import helper
from django.http import HttpResponse
import json
from threading import Thread
import asyncio


class User:
    uuid = ''
    thread = None
    step = 0
    progress = 0
    msg = ''

    def __init__(self, **kwargs):
        self.uuid = kwargs['uuid']
        self.thread = kwargs['thread']
        self.step = kwargs['step']
        pass


users: {str, User} = {}


async def _async_export(uuid):
    helper.init(uuid)
    helper.auto_login()
    async for item in helper.export_all():
        print(item)
    helper.dispose()


def async_export(uuid):
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_async_export(uuid))


def export(request):
    context = {'step': 0}
    return render(request, 'index.html', context)


def export_start(request):
    uuid = request.GET.get('murmur', '')
    t = Thread(target=async_export, args=(uuid,))
    users[uuid] = User(uuid=uuid, step=1, thread=t)
    context = {'step': 1}
    return render(request, 'index.html', context)


def export_progress(request):
    uuid = request.GET.get('murmur', '')
    if uuid not in users.keys():
        return HttpResponse(json.dumps({'step': 0}), content_type='application/json')
    user = users[uuid]
    return HttpResponse(json.dumps({'step': user.step}), content_type='application/json')
