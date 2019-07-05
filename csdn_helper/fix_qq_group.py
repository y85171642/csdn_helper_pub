import db_helper
from aiocqhttp import CQHttp

bot = CQHttp(access_token='123',
             secret='abc')


@bot.on_message
# 上面这句等价于 @bot.on('message')
async def handle_msg(context):
    n = 1
    group_id = 747776374
    lst = await bot.call_action(action='get_group_member_list', group_id=group_id)
    for a in db_helper.find_all('', 0, 100000):
        if a.qq_group == '-1':
            for b in lst:
                if str(b['user_id']) == a.qq_num:
                    a.qq_group = str(group_id)
                    a.save()
                    print('save (%s) ==> %d' % (a.id, n))
                    n += 1


bot.run(host='127.0.0.1', port=8761)
