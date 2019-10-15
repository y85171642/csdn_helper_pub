import os


def _split_file(file_path, block_size):
    """
    拆分大文件为若干个小文件
    :param file_path: 文件路径
    :param block_size: 单个小文件的大小(字节)
    :return: 保存拆分文件的文件夹的完整路径 或者 原文件路径(不超过block_size时)
    """
    file_size = os.path.getsize(file_path)  # 文件字节数
    real_path, file_name = os.path.split(file_path)  # 除去文件名以外的path，文件名
    suffix = file_name.split('.')[-1]  # 文件后缀名
    if file_size < block_size:
        return file_path
    else:
        fp = open(file_path, 'rb')
        count = file_size // block_size + 1
        temp_dir = real_path + os.sep + file_name + '_split'
        if not os.path.exists(temp_dir):
            os.mkdir(temp_dir)

        merge_bat = 'copy /b '
        del_bat = ''
        for i in range(1, count + 1):
            f_name = file_name.replace('.' + str(suffix), '[{}].{}'.format(i, suffix))
            f_path = temp_dir + os.sep + f_name
            f = open(f_path, 'wb')
            f.write(fp.read(block_size))
            merge_bat = merge_bat + f_name + '+'
            del_bat = del_bat + '\ndel ' + f_name
        fp.close()
        merge_bat = merge_bat[:-1] + ' ' + file_name
        mb = open(os.path.join(temp_dir, 'combine.bat'), 'w')
        mb.write(merge_bat + del_bat)
        mb.close()
        return temp_dir


if __name__ == '__main__':
    _split_file(r'G:\Test\a.rar', 10 * 1024 * 1024)
    # _merge_file(r'G:\Test\a.rar_split')
