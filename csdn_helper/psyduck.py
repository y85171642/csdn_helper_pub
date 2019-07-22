from aiocqhttp import CQHttp
import db_helper
import helper
import config
import short_url

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


def find_csdn_download_id(text):
    url = find_csdn_download_url(text)
    if url is not None:
        return url[url.rfind('/') + 1:]
    return None


last_cmd = ''
last_arg_int = 0
last_arg_str = ''


def is_at_me(message):
    if message.find('[CQ:at,qq=%s]' % config.default_qq) != -1:
        return True
    return False


def rm_at_me(message):
    return message.replace('[CQ:at,qq=%s]' % config.default_qq, '')


@bot.on_message('private')
async def handle_msg_private(context):
    qq_num = int(context['sender']['user_id'])
    if qq_num in config.admin_list:
        await handle_msg_group(context)
    else:
        await bot.send(context, "您没有权限使用大黄鸭，请加群：%s" % config.default_group)


@bot.on_message('group')
async def handle_msg_group(context):
    global last_cmd
    global last_arg_str
    global last_arg_int
    message = context['message']

    if config.need_at_me:
        if not is_at_me(message):
            return
    if is_at_me(message):
        message = rm_at_me(message)

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

    qq_num = str(context['sender']['user_id'])
    qq_name = context['sender']['nickname']
    if 'card' in context['sender'] and context['sender']['card'] != '':
        qq_name = context['sender']['card']
    qq_group = '-1'
    if 'group_id' in context:
        qq_group = str(context['group_id'])

    if cmd == '-help' or cmd == '-?':
        msg = '● 个人信息　-personal'
        msg += '\n● 排行榜　　-rank [index]'
        msg += '\n● 查询文件　-find [keyword]'
        msg += '\n● 文件信息　-info [id]'
        msg += '\n● 更多信息　-more'
        msg += sep_s()
        msg += '\n* 输入CSDN下载页链接下载'
        msg += source_code_tail()
        msg += donate_tail()
        msg += export_tail()
        last_cmd = cmd
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

    if cmd == '-donors':
        msg = build_donors(arg_int)
        last_cmd = cmd
        last_arg_int = arg_int
        await bot.send(context, msg)

    if cmd == '-personal':
        msg = build_personal(qq_num, qq_group, qq_name)
        await bot.send(context, msg)

    if cmd == '-more':
        if last_cmd == '-find':
            last_arg_int += 10
            result = db_helper.find_all(last_arg_str, last_arg_int)
            count = db_helper.count_all(last_arg_str)
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
        if last_cmd == '-donors':
            last_arg_int += 10
            msg = build_donors(last_arg_int)
            await bot.send(context, msg)
        if last_cmd == '-help' or last_cmd == '-?':
            msg = '● 用户信息　-user'
            msg += '\n● 捐赠名单　-donors'
            msg += sep_s()
            msg += '\n* 输入CSDN下载页链接下载'
            msg += source_code_tail()
            msg += donate_tail()
            msg += export_tail()
            await bot.send(context, msg)

    download_id = find_csdn_download_id(context['message'])
    if download_id is not None:
        if helper.__already_download(download_id) and db_helper.exist_download(download_id):
            msg = build_download_info(db_helper.get_download(download_id))
            await bot.send(context, msg)
            return

    download_url = find_csdn_download_url(context['message'])
    if download_url is not None:
        can_download, msg = helper.check_download_limit(qq_num, qq_group)
        if not can_download:
            await bot.send(context, msg)
            return

        if helper.is_busy():
            await bot.send(context, '资源正在下载中，请稍后...')
            return
        await bot.send(context, '开始下载...')
        try:
            helper.init()
            download_info = helper.auto_download(download_url, qq_num, qq_name, qq_group)
            msg = download_info['message']
            if download_info['success']:
                result = db_helper.get_download(download_info['info']['id'])
                msg = build_download_info(result)
                last_cmd = '-info'
                last_arg_int = int(result.id)
            elif donate_tail() != '':
                msg += sep_s()
                msg += donate_tail()
            await bot.send(context, msg)
        finally:
            helper.dispose()


def source_code_tail():
    if config.source_code_url != '':
        return '\n* 工具源码 %s' % short_url.get(config.source_code_url)
    return ''


def donate_tail():
    if config.donate_url != '':
        return '\n* 黄鸭捐助 %s' % short_url.get(config.donate_url)
    return ''


def export_tail():
    if config.export_url != '':
        return '\n* 资源导出 %s' % short_url.get(config.export_url)
    return ''


def build_download_detail_info(result: db_helper.Download):
    msg = result.title
    msg += '\n评分\t：{}{}'.format('★' * result.stars, '☆' * (5 - result.stars))
    msg += '\n所需\t：{} 积分/C币'.format(result.coin)
    msg += '\n大小\t：{}'.format(result.size)
    msg += '\n下载\t：{}'.format(build_url(result.id))
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
    if text_size(title) > 20:
        title = text_sub_size(title, 20) + '...'
    msg = title
    msg += '\n评分：{}{}'.format('★' * result.stars, '☆' * (5 - result.stars))
    msg += '\n所需：{} 积分/C币'.format(result.coin)
    msg += '\n大小：{}'.format(result.size)
    msg += '\n下载：{}'.format(build_url(result.id))
    msg += sep_l()
    msg += '\n-more 获取更多信息'
    msg += donate_tail()
    return msg


def build_url(_id):
    url = '{}{}.zip'.format(config.download_server_url, _id)
    return short_url.get(url)


def build_find_msg(result, total, start_index=0):
    if len(result) <= 0:
        return '未找到符合条件的结果。'
    msg = '共{2}条搜索结果（{0}~{1}）：'.format(start_index + 1, start_index + len(result), total)
    for d in result:
        title = d.title
        _len = 16
        if text_size(title) > _len:
            title = text_sub_size(title, _len) + '...'
        _id_sep = '  ' * (8 - len(str(d.id)))
        msg += '\nID({}){}：{}'.format(d.id, _id_sep, title)
    msg += sep_l()
    msg += '\n-more 获取更多信息'
    msg += '\n-info [id] 下载/查看文件信息'
    return msg


def text_sub_size(text, size):
    for i in range(len(text)):
        if text_size(text[0:i]) >= size:
            return text[0:i]
    return text


def text_size(text):
    if text == '':
        return 0
    txt_len = len(text)
    txt_len_utf8 = len(text.encode('utf-8'))
    size = int((txt_len_utf8 - txt_len) / 4 + txt_len / 2)
    return size


def build_rank_msg(result, start_index=0):
    if len(result) <= 0:
        return '没有更多信息了。'
    msg = '排行榜（{}~{}）：'.format(start_index + 1, start_index + len(result))
    index = start_index + 1
    for fo in result:
        name = build_name_str(fo[1]['name'])
        msg += '\n{}.{}\t{}次\t(共消耗{}积分)'.format(index, name, fo[1]['count'], fo[1]['coin'])
        index += 1
    msg += sep_l()
    msg += '\n-more 获取更多信息'
    return msg


def build_name_str(name):
    name = '【{}】{}'.format(name, (10 - text_size(name)) * '　')
    return name


def build_donors(start_index=0):
    if start_index >= len(config.donate_list):
        return '没有更多信息了。'
    _len = min(10, len(config.donate_list) - start_index)
    msg = '捐赠名单 共{}条（{}~{}）：'.format(len(config.donate_list), start_index + 1, start_index + _len)
    total = 0
    for i in range(0, len(config.donate_list)):
        total += float(config.donate_list[i]['money'])
    for i in range(start_index, start_index + _len):
        donor = config.donate_list[i]
        name = build_name_str(donor['name'])
        rmb = donor['money']
        msg += '\n{}\t￥{}'.format(name, rmb)
    msg += sep_l()
    msg += '\n{}\t￥{}'.format(build_name_str('共计'), total)
    msg += '\n-more 获取更多信息'
    return msg


def build_personal(qq_num, qq_group, name):
    msg = '{}'.format(name)
    vip_level = 0
    for donor in config.donate_list:
        if donor['qq'] == qq_num:
            vip_level = int(donor['money'] ** 0.3)
            break

    if vip_level > 0:
        msg += '【VIP%d】' % vip_level
    else:
        msg += '【普通】'

    _d_used = db_helper.count_daily(qq_num, qq_group)
    _d_total = helper.daily_download_count(qq_num)
    msg += '\n本日剩余下载次数：{}/{}次'.format(_d_total - _d_used, _d_total)
    _w_used = db_helper.count_weekly(qq_num, qq_group)
    _w_total = helper.weekly_download_count(qq_num)
    msg += '\n本周剩余下载次数：{}/{}次'.format(_w_total - _w_used, _w_total)
    _m_used = db_helper.count_monthly(qq_num, qq_group)
    _m_total = helper.monthly_download_count(qq_num)
    msg += '\n本月剩余下载次数：{}/{}次'.format(_m_total - _m_used, _m_total)
    return msg


def sep_s():
    return '\n' + '-' * 29


def sep_l():
    return '\n' + '-' * 56


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
@bot.on_request('group')
# 上面这句等价于 @bot.on('request.group', 'request.friend')
async def handle_group_request(context):
    if context['message'] == 'Psyduck~':
        return {'approve': True}
    # 验证信息不符，拒绝
    return {'approve': False, 'reason': '请输入正确的入群口令'}
'''

if __name__ == '__main__':
    bot.run(host='127.0.0.1', port=config.psyduck_port)
