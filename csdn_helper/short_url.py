import requests
import config
from urllib import parse


def get(url):
    if not config.use_short_url:
        return url
    req = 'http://suo.im/api.htm'
    req = req + "?format=json&url=%s" % parse.urlencode({'_': url})[2:]
    req = req + '&key=5d1039698e676d15a1b17302@26f1c58fc6660c6e3e6b7e67cdf48f1b'
    req = req + '&expireDate=2050-01-01'
    json = requests.get(req).content
    json_data = eval(json)
    return json_data['url'][7:]


def test():
    print(get('http://www.baidu.com'))


if __name__ == '__main__':
    test()
