import helper
import db_helper

print('开始修复数据库...')
count = 0
helper.init()
for i in range(1, 100):
    helper.get('https://download.csdn.net/my/downloads/{}'.format(i))
    els = helper.find_all('//div[@class="card clearfix"]/div[2]/h3/a')
    hrefs = []
    for el in els:
        href = el.get_attribute('href')
        if href is None:
            continue
        hrefs.append(href)
    for href in hrefs:
        _id = href[href.rfind('/') + 1:]
        is_download = helper.__already_download(_id)
        if not is_download:
            continue
        if db_helper.exist_download(_id):
            continue
        helper.get(href)
        info = helper.__get_download_info()
        info['filename'] = helper.__get_file_name_in_zip_file(info['id'])
        info['url'] = href
        info['qq_num'] = '799329256'
        info['qq_name'] = '菜鸡儿NO.1'
        db_helper.insert_download(info)
        count += 1
        print('插入数据成功({})，ID:{}'.format(count, info['id']))
helper.dispose()
print('修复完成，共修复{}条'.format(count))
