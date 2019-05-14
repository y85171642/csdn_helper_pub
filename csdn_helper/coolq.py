from aiocqhttp import CQHttp
import db_helper
import helper
import config

bot = CQHttp(access_token='123',
             secret='abc')


def find_csdn_download_url(text):
    index = text.find('https://download.csdn.net/download/')
    if index != -1:
        d_end = index + len('https://download.csdn.net/download/')
        spindex = text[d_end:].find('/')
        if spindex != -1 and len(text[d_end + spindex + 1:]) > 0:
            id_len = 0
            for i in range(d_end + spindex + 1, len(text)):
                if '9' >= text[i] >= '0':
                    id_len += 1
                else:
                    break
            if id_len > 0:
                return text[index:d_end + spindex + 1 + id_len]
    return None


last_cmd = ''
last_arg_int = 0
last_arg_str = ''


@bot.on_message
# 上面这句等价于 @bot.on('message')
async def handle_msg(context):
    # 下面这句等价于 bot.send_private_msg(user_id=context['user_id'], message='你好呀，下面一条是你刚刚发的：')
    """
    try:
         await bot.send(context, '你好呀，下面一条是你刚刚发的：')
     except ApiError:
         pass
    """
    global last_cmd
    global last_arg_str
    global last_arg_int
    message = context['message']
    if message.startswith('@{}'.format(config.default_qq_name)):
        message = message[4:]
    message = message.strip()
    cmd_args = message.split(' ')
    cmd = cmd_args[0]
    args = cmd_args[1:] if len(cmd_args) > 1 else []

    def is_all_number(_str: str):
        if _str is None or _str == '':
            return False
        for a in _str:
            if not '0' <= a <= '9':
                return False
        return True

    arg_int = int(args[0]) if len(args) > 0 and is_all_number(args[0]) else 0
    arg_int_2 = int(args[1]) if len(args) > 1 and is_all_number(args[1]) else 0
    arg_str = args[0] if len(args) > 0 else ''

    if cmd == '-help' or cmd == '-?':
        msg = '● 用户信息　-user'
        msg += '\n● 排行榜　　-rank [index]'
        msg += '\n● 查询文件　-find [keyword]'
        msg += '\n● 文件信息　-info [id]'
        msg += '\n● 更多信息　-more'
        msg += '\n' + '-' * 38
        msg += '\n* 直接输入CSDN下载页链接即可下载'
        msg += '\n* 源码：http://t.cn/EK5Q58Y'
        await bot.send(context, msg)

    if cmd == '-user':
        await bot.send(context, '查询用户信息中...')
        helper.init()
        info = helper.get_user_info()
        helper.dispose()
        if info is None:
            msg = '获取用户信息失败！'
        else:
            msg = '{}'.format(info['name'])
            if info['vip']:
                msg += '【VIP】'
                msg += '\n剩余次数：{}次'.format(info['remain'])
                msg += '\n有效期至：{}'.format(info['date'][:10])
            else:
                msg += '\n剩余积分：{}积分'.format(info['remain'])
        await bot.send(context, msg)

    if cmd == '-rank':
        result = db_helper.rank_qq(arg_int)
        msg = build_rank_msg(result, arg_int)
        last_cmd = cmd
        last_arg_int = arg_int
        await bot.send(context, msg)

    if cmd == '-find':
        result = db_helper.find_all(arg_str, arg_int_2)
        count = db_helper.count_all(arg_str)
        msg = build_find_msg(result, count, arg_int_2)
        last_cmd = cmd
        last_arg_str = arg_str
        last_arg_int = arg_int_2
        await bot.send(context, msg)

    if cmd == '-info':
        result = db_helper.get_download(arg_int)
        if result is not None:
            msg = build_download_info(result)
            last_cmd = cmd
            last_arg_str = arg_str
            last_arg_int = arg_int
            await bot.send(context, msg)
        else:
            await bot.send(context, '文件不存在。')

    if cmd == '-more':
        if last_cmd == '-find':
            last_arg_int += 10
            result = db_helper.find_all(last_arg_str, last_arg_int)
            count = db_helper.count_all(arg_str)
            msg = build_find_msg(result, count, last_arg_int)
            await bot.send(context, msg)
        if last_cmd == '-rank':
            last_arg_int += 10
            result = db_helper.rank_qq(last_arg_int)
            msg = build_rank_msg(result, last_arg_int)
            await bot.send(context, msg)
        if last_cmd == '-info':
            result = db_helper.get_download(last_arg_int)
            if result is not None:
                msg = build_download_detail_info(result)
                await bot.send(context, msg)

    download_url = find_csdn_download_url(context['message'])
    if download_url is not None:
        if helper.is_busy():
            await bot.send(context, '资源正在下载中，请稍后...')
            return
        await bot.send(context, '开始下载...')
        try:
            helper.init()
            qq_num = context['sender']['user_id']
            qq_name = context['sender']['nickname']
            if 'card' in context['sender'] and context['sender']['card'] != '':
                qq_name = context['sender']['card']
            download_info = helper.auto_download(download_url, qq_num, qq_name)
            msg = download_info['message']
            if download_info['success']:
                result = db_helper.get_download(download_info['info']['id'])
                msg = build_download_info(result)
                last_cmd = '-info'
                last_arg_int = int(result.id)
            await bot.send(context, msg)
        finally:
            helper.dispose()


def build_download_detail_info(result: db_helper.Download):
    msg = result.title
    msg += '\n评分\t：{}{}'.format('★' * result.stars, '☆' * (5 - result.stars))
    msg += '\n所需\t：{} 积分/C币'.format(result.coin)
    msg += '\n大小\t：{}'.format(result.size)
    msg += '\n下载\t：{}{}.zip'.format(config.download_server_url, result.id)
    msg += '\nID\t：{}'.format(result.id)
    msg += '\n类型\t：{}'.format(result.type)
    msg += '\n标签\t：{}'.format(result.tag)
    msg += '\n文件名\t：{}'.format(result.filename)
    msg += '\n下载者\t：{}({})'.format(result.qq_name, result.qq_num)
    msg += '\n上传时间：{}'.format(result.upload_date.strftime("%Y-%m-%d %H:%M:%S"))
    msg += '\n下载时间：{}'.format(result.created_date.strftime("%Y-%m-%d %H:%M:%S"))
    msg += '\n原始链接：{}'.format(result.url)
    msg += '\n详细描述：{}'.format(result.description)
    return msg


def build_download_info(result: db_helper.Download):
    title = result.title
    if len(title) > 30:
        title = title[:30] + '....'
    msg = title
    msg += '\n评分：{}{}'.format('★' * result.stars, '☆' * (5 - result.stars))
    msg += '\n所需：{} 积分/C币'.format(result.coin)
    msg += '\n大小：{}'.format(result.size)
    msg += '\n下载：{}{}.zip'.format(config.download_server_url, result.id)
    msg += '\n' + '-' * 60
    msg += '\n-more 获取更多信息'
    return msg


def build_find_msg(result, total, start_index=0):
    if len(result) <= 0:
        return '未找到符合条件的结果。'
    msg = '共{2}条搜索结果（{0}~{1}）：'.format(start_index + 1, start_index + len(result), total)
    for d in result:
        t = d.title
        if len(t) > 25:
            t = t[:25] + '....'
        msg += '\nID({}){}：{}'.format(d.id, '  ' * (8 - len(str(d.id))), t)
    msg += '\n' + '-' * 65
    msg += '\n-more 获取更多信息'
    msg += '\n-info [id] 下载/查看文件信息'
    return msg


def build_rank_msg(result, start_index=0):
    if len(result) <= 0:
        return '没有更多信息了。'
    msg = '排行榜（{}~{}）：'.format(start_index + 1, start_index + len(result))
    index = start_index + 1
    for fo in result:
        name = fo[1]['name']
        txt_len = len(name)
        txt_len_utf8 = len(name.encode('utf-8'))
        size = int((txt_len_utf8 - txt_len) / 4 + txt_len / 2)
        name = '【{}】{}'.format(name, (10 - size) * '　')
        msg += '\n{}.{}\t{}次\t(共消耗{}积分)'.format(index, name, fo[1]['count'], fo[1]['coin'])
        index += 1
    msg += '\n' + '-' * 60
    msg += '\n-more 获取更多信息'
    return msg


@bot.on_notice('group_increase')
# 上面这句等价于 @bot.on('notice.group_increase')
async def handle_group_increase(context):
    info = await bot.get_group_member_info(group_id=context['group_id'],
                                           user_id=context['user_id'])
    nickname = info['nickname']
    name = nickname if nickname else '新人'
    await bot.send(context,
                   message='欢迎【{}】加入本群～\n友情提示：{}可以免费下载CSDN资源哦！\n-help 查看帮助'.format(name, config.default_qq_name),
                   at_sender=False, auto_escape=True)


'''
@bot.on_request('group', 'friend')
# 上面这句等价于 @bot.on('request.group', 'request.friend')
async def handle_group_request(context):
    if context['message'] != 'some-secret':
        # 验证信息不符，拒绝
        return {'approve': False, 'reason': '你填写的验证信息有误'}
    return {'approve': True}
'''

if __name__ == '__main__':
    bot.run(host='127.0.0.1', port=8800)
