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
    while True:
        folder_id = lzy.list_dir()['folder_list'][folder_name]
        cloud_files = lzy.list_dir(folder_id)['file_list']
        local_files = os.listdir(config.zip_save_path)
        for lf in local_files:
            f_path = os.path.join(config.zip_save_path, lf)
            f_size = os.path.getsize(f_path)
            f_id = lf[:-4]
            # 文件的修改时间小于10分钟则不进行上传
            if time.time() - os.path.getmtime(f_path) < 600:
                continue
            # 文件大小超过 99MB 时不上传
            lf_size = os.path.getsize(f_path)
            if lf_size > 99 * 1024 * 1024:
                continue
            if lf not in cloud_files and db_helper.exist_download(f_id):
                print(f'开始上传文件【{lf}】 ({f_size}B)...')
                result = lzy.upload2(f_path, folder_id)
                db_helper.set_download_url(f_id, result['share_url'])
                os.remove(f_path)
                print("上传完成！")
                break
        time.sleep(10)


def login():
    print('登录蓝奏...')
    lzy.login(username, password)


def main_loop():
    while True:
        login()
        try:
            auto_sync_loop()
        except:
            import traceback
            traceback.print_exc()
        time.sleep(1)


if __name__ == '__main__':
    main_loop()
