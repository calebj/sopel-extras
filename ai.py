"""
ai.py - Artificial Intelligence Module
Copyright 2009-2011, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

http://sopel.chat
"""
from sopel.module import rule, priority, rate
import random
import time


def setup(bot):
    # Set value to 3 if not configured
    if bot.config.ai and bot.config.ai.frequency:
        bot.memory['frequency'] = bot.config.ai.frequency
    else:
        bot.memory['frequency'] = 3

    random.seed()

# Perhaps these should be decorators
def decide(bot):
    return 0 < random.random() < float(bot.memory['frequency']) / 10

def humansleep():
    time.sleep(random.uniform(3, 7))

@rule('(?i)$nick(bye|goodbye|gtg|seeya|cya|ttyl|g2g|gnight|goodnight)')
@rate(30)
def goodbye(bot, trigger):
    humansleep()
    byemsg = random.choice(('Bye', 'Goodbye', 'Seeya', 'Auf Wiedersehen', 'Au revoir', 'Ttyl'))
    punctuation = random.choice(('!', ' '))
    bot.say(byemsg + ' ' + trigger.nick + punctuation)

@rule('(?i)stupid ((ro)?bot|$nickname).*')
@rate(30)
@priority('high')
def f_stupid(bot, trigger):
    humansleep()
    bot.reply("Stupid human!")

@rule('(?i)(shut up,?\s*((ro)?bot|$nickname).*|$nickshut up)')
@rate(30)
def shut_up(bot, trigger):
    humansleep()
    bot.reply('No, you shut up!')


@rule('(?i)(.*thank(\s*you|s).*$nickname.*$|$nickthank(\s*you|s).*)')
@rate(30)
@priority('high')
def ty(bot, trigger):
    humansleep()
    mystr = trigger.group()
    mystr = str(mystr)
    if (mystr.find(" no ") == -1) and (mystr.find("no ") == -1) and (mystr.find(" no") == -1):
        bot.reply("You're welcome.")


@rule('$nick(yes|no)$')
@rate(15)
def yesno(bot, trigger):
    humansleep()
    rand = random.uniform(0, 5)
    text = trigger.group()
    text = text.split(":")
    text = text[1].split()
    if text[0] == 'yes':
        bot.reply("no")
    elif text[0] == 'no':
        bot.reply("yes")


@rule('(?i)$nick(ping)\s*')
@rate(30)
def ping_reply(bot, trigger):
    text = trigger.group().split(":")
    text = text[1].split()
    if text[0] == 'PING' or text[0] == 'ping':
        bot.reply("PONG")


@rule('(?i)($nicki\s*love\s*you|i.*love.*(sopel|$nickname).*)')
@rate(30)
def love(bot, trigger):
    humansleep()
    bot.reply("I love you too.")

@rule('(?i)($nickyou(.?re|\s*are)\s*((so|really|very)\s+)?awesome.*|.*(sopel|$nickname)\s*is\s*((so|really|very)\s+)?awesome.*)')
@rate(30)
def awesome(bot, trigger):
    humansleep()
    bot.reply("You're not so bad yourself!")

@rule('(?i)($nickyou(.?re|\s*are)\s*((so|really|very)\s+)?cool.*|.*(sopel|$nickname)\s*is\s*((so|really|very)\s+)?cool.*)')
@rate(30)
def cool(bot, trigger):
    humansleep()
    bot.action("dons sunglasses", trigger.sender)

@rule('(?i)^[^\s]*\s*(boops|hugs|p[ea]ts)\s*((a|the)\s+)?(sopel|$nickname)$')
@rate(30)
def hum(bot, trigger):
    humansleep()
    bot.action("hums contentedly")

@rule('(?i)(^|.*\s+)(h(eh)+e?|(ha)+|l([eo]l)+|rofl|kek(ek)*e?|xd+)!?$')
@priority('high')
@rate(30)
def f_lol(bot, trigger):
    if decide(bot):
        humansleep()
        respond = ['haha', 'lol', 'rofl', 'hm', 'XD', 'hmmmm...']
        bot.say(random.choice(respond))


@rule('\s*(([Bb]+([Yy]+[Ee]+(\s*[Bb]+[Yy]+[Ee]+)?)|[Ss]+[Ee]{2,}\s*[Yy]+[Aa]+|[Oo]+[Uu]+)(\s+later)?|cya|ttyl|later|([Gg]2[Gg]|[Gg][Tt][Gg]|(([Gg][Oo]{2,}[Dd]+\s*)?[Gg]?([Bb]+[Yy]+[Ee]+|[Nn]+[Ii]+[Gg]+[Hh]+[Tt]+))))\s*((y?all|guys)\s*)?(!|~|[.])*$')
@priority('high')
@rate(30)
def f_bye(bot, trigger):
    set1 = ['bye', 'byebye', 'see you', 'see ya', 'Good bye', 'have a nice day']
    set2 = ['!', ' :)', ':D', ':P', ':-D', ';)', '(wave)']
    respond = [ str1 + ' ' + str2 for str1 in set1 for str2 in set2]
    humansleep()
    bot.say(random.choice(respond))

@rule('^\s*(([Hh]+([AaEe]+[Ll]{2}[Oo]+|[Ii]+|[Ee]+[Yy]+)+\s*(all|guys)?)|[Yy]+[Oo]+|[Aa]+[Ll]{2}|[Aa]nybody)\s*(!+|\?+|~+|[.]+|[:;][)DPp]+)*$')
@priority('high')
@rate(30)
def f_hello(bot, trigger):
    humansleep()
    set1 = ['yo', 'hey', 'hi', 'Hi', 'hello', 'Hello', 'Welcome']
    set2 = ['!', ' :)', ':D', 'xD', ':P', ':-D', ';)']
    respond = [ str1 + ' ' + str2 for str1 in set1 for str2 in set2]
    bot.say(random.choice(respond))

@rule('^\s*(good\s*)?(morning|afternoon|evening)\s*(all|guys)?\s*(!+|\?+|~+|[.]+|[:;][)DPp]+)*$')
@priority('high')
@rate(30)
def f_morning(bot, trigger):
    f_hello(bot,trigger)

#@rule('(heh!?)$')
#@priority('high')
#@rate(30)
#def f_heh(bot, trigger):
    #if decide(bot):
        #humansleep()
        #respond = ['hm', 'hmmmmmm...', 'heh?']
        #bot.say(random.choice(respond))


@rule('(?i)$nick(really!?)')
@priority('high')
def f_really(bot, trigger):
    humansleep()
    bot.say(str(trigger.nick) + ": " + "Yes, really.")

@rule('(?i).*[.]{3,}\s*yet[.]?$')
@priority('high')
@rate(30)
def f_dundundun(bot, trigger):
    if decide(bot):
        humansleep()
        bot.say('DUN DUN DUUUNNNN')

@rule('(?i)^\s*(w(b|elcome\s*back)[\s:,].*$nickname|$nickw(b|elcome\s*back))')
@rate(30)
def wb(bot, trigger):
    humansleep()
    set1 = ['Thank you', 'thanks']
    set2 = ['!', ' :)', ' :D']
    respond = [ str1 + str2 for str1 in set1 for str2 in set2]
    bot.reply(random.choice(respond))


if __name__ == '__main__':
    print(__doc__.strip())
