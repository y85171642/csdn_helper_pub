from psyduck_search.helper import Helper
from threading import Thread
import time

h: Helper = None


def helper_thread():
    global h
    h = Helper('123456')
    h.init()
    h.search('avpro', 0)


Thread(target=helper_thread, ).start()

while True:
    if h is not None:
        if h.is_searching:
            print("搜索到：{}个".format(len(h.search_result)))
            for k, v in h.search_result.items():
                if v['coin'] == 0:
                    print("检索到免费资源：" + k)
        else:
            print("搜索完成：{}个".format(len(h.search_result)))
    time.sleep(1)
