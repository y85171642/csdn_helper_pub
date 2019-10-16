import lanzou_api
import config
import os
import time
import db_helper

username = config.lanzou_username
password = config.lanzou_password
folder_name = 'CSDN'

lzy = lanzou_api.LanZouCloud()


def auto_sync_loop():
    folder_id = lzy.list_dir()['folder_list'][folder_name]
    print('拉取文件列表...')
    list_dir = lzy.list_dir(folder_id)
    cloud_files = list_dir['file_list']
    cloud_files.update(list_dir['folder_list'])
    print('拉取文件列表完成。')
    while True:
        local_files = os.listdir(config.zip_save_path)
        for lf in local_files:
            f_path = os.path.join(config.zip_save_path, lf)
            f_size = os.path.getsize(f_path)
            f_id = lf[:-4]
            # 文件的修改时间小于10分钟则不进行上传
            if time.time() - os.path.getmtime(f_path) < 600:
                continue
            # 文件大小超过 99MB 时不上传
            # lf_size = os.path.getsize(f_path)
            # if lf_size > 99 * 1024 * 1024:
            #    continue
            if lf not in cloud_files and db_helper.exist_download(f_id):
                print(f'开始上传文件[{lf}]({f_size}b)...')
                d = db_helper.get_download(f_id)
                desc = d.title + "\n" + d.description
                if len(desc) > 159:
                    desc = desc[0:156] + "..."
                result = lzy.upload2(f_path, folder_id, desc)
                db_helper.set_download_url(f_id, result['share_url'])
                os.remove(f_path)
                cloud_files[lf] = result['file_id']
                print("上传完成！")
                break
        time.sleep(2)


def set_all_desc():
    folder_id = lzy.list_dir()['folder_list'][folder_name]
    print('拉取文件列表...')
    cloud_files = lzy.list_dir(folder_id)['file_list']
    print('拉取文件列表完成。')
    i = 0
    for (cf_name, cf_id) in cloud_files.items():
        db_id = cf_name[:-4]
        i = i + 1
        if not db_helper.exist_download(db_id):
            continue
        d = db_helper.get_download(db_id)
        desc = d.title + "\n" + d.description
        if len(desc) > 159:
            desc = desc[0:156] + "..."
        suc = lzy.modify_description(cf_id, desc)
        print(f'[{i}/{len(cloud_files)}]设置{db_id}描述结果：{suc}')
    print('所有文件描述设置完毕')


def login():
    print('登录蓝奏...')
    global lzy
    lzy = lanzou_api.LanZouCloud()
    lzy.login(username, password)


def main_loop():
    while True:
        login()
        try:
            # set_all_desc()
            auto_sync_loop()
        except:
            import traceback
            traceback.print_exc()
        time.sleep(1)


if __name__ == '__main__':
    main_loop()
