from sopel.module import commands, priority
from sopel.formatting import color, colors
import random

def configure(config):
    pass

NUM_WHEELS = 3

def setup(bot):
    pass

@commands('spin')
@priority('low')
def spin(bot, trigger):
    balance = bot.db.get_nick_value(trigger.nick, 'slots_balance')
    if balance is None:
        balance = 0

    wheel = [
        {'icon':'Crystal', 'color':['white', 'blue']},
        {'icon':'Petal',   'color':['white', 'red']},
        {'icon':'Lilac',   'color':['white', 'purple']},
        {'icon':'Carol',   'color':['black', 'green']},
        {'icon':'Milla',   'color':['white', 'orange']},
        #{'icon':'Zao',     'color':['white', 'red']},
        {'icon':'Timtam',  'color':['white', 'black']}
    ]
    wheel_lastindex = len(wheel)-1

    results = [random.randint(0,wheel_lastindex) for i in range(NUM_WHEELS)]
    if results is [wheel_lastindex for n in range(NUM_WHEELS)]:
        win = 250
    elif results[1] is results[0] and (results[2] is results[0] or results[2] is wheel_lastindex):
        win = (results[0]+1)*4
    elif results.count(0) is 2:
        win = 4
    elif results.count(0) is 1:
        win = 2
    else:
        win = -1

    wheel_results = [wheel[i] for i in results]
    wheel_results = [color(w['icon'], fg=w['color'][0], bg=w['color'][1]) for w in wheel_results]
    vis = ' | '.join(wheel_results)
    if win>0:
        colorwin = color(' +{}'.format(win), fg='green')
    else:
        colorwin = color(' {}'.format(win), fg='red')
    balance += win
    bot.reply(vis + colorwin + ' crystals: %i' % balance)
    bot.db.set_nick_value(trigger.nick, 'slots_balance', balance)
