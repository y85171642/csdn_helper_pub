import requests
import config
from urllib import parse


def get(url):
    if not config.use_short_url:
        return url
    return _get_2(url)


def _get_1(url):
    req = 'http://suo.im/api.htm'
    req = req + "?format=json&url=%s" % parse.urlencode({'_': url})[2:]
    req = req + '&key=5d1039698e676d15a1b17302@26f1c58fc6660c6e3e6b7e67cdf48f1b'
    req = req + '&expireDate=2050-01-01'
    try:
        headers = {
            "Host": "suo.im",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/65.0.3325.146 "
                          "Safari/537.36 "
        }
        json = requests.get(req, headers=headers).content
        json_data = eval(json)
        return json_data['url'][7:]
    except:
        return url


def _get_header():
    headers = {
        "Host": "suo.im",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/65.0.3325.146 "
                      "Safari/537.36 "
    }
    return headers


def _get_2(url):
    req = 'http://api.ft12.com/api.php'
    req = req + "?url=%s" % parse.urlencode({'_': url})[2:]
    req = req + '&apikey=qgMwVpN632zadRc4Pz@ddd'
    try:
        headers = {
            "Host": "api.ft12.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/65.0.3325.146 "
                          "Safari/537.36 "
        }
        json = requests.get(req, headers=headers).content
        return json.decode()[7:]
    except:
        return url


def test():
    print(get('http://www.baidu.com'))


if __name__ == '__main__':
    test()
