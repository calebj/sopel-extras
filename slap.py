"""
slap.py - Slap Module
Copyright 2009, Michael Yanovich, yanovich.net
Copyright 2016, Caleb Johnson, calebj.io
http://sopel.chat
"""

import random
import re
from sopel.module import commands

verbs = [
    'sends {} flying with a robotic tentacle', 
    'bull rushes {}, sending them flying',
    'slashes {} in the face with a razor-sharp robot claw',
    'transforms into a holodragon and laser blasts {} into a smoking crater',
    'transforms into a holodragon and piledrives {} from orbit'
    ]

@commands('slap', 'slaps')
def slap(bot, trigger):
    """.slap <target> - Slaps <target>"""
    text = trigger.group().split()
    if len(text) < 2:
        text.append(trigger.nick)
    text[1] = re.sub(r"\x1f|\x02|\x12|\x0f|\x16|\x03(?:\d{1,2}(?:,\d{1,2})?)?", '', text[1])
    if text[1].startswith('#'):
        return
    if text[1] == 'me' or text[1] == 'myself':
        text[1] = trigger.nick
    if trigger.sender in bot.channels:
        slappable = bot.channels.get(trigger.sender).users
    else:
        slappable = [bot.nick, trigger.nick]
    if text[1].lower() in [s.lower() for s in slappable]:
        if text[1] == bot.nick:
            if trigger.nick not in bot.config.core.admins:
                text[1] = trigger.nick
            else:
                text[1] = 'itself'
        if text[1] in bot.config.core.admins:
            if trigger.nick not in bot.config.core.admins:
                text[1] = trigger.nick
        verb = random.choice(verbs)
        if '{}' in verb:
            action = verb.format(text[1])
        else:
            action = verb + ' ' + text[1]
    elif trigger.sender not in bot.channels and bot.users.contains(text[1].lower()):
        bot.say('You and I are the only ones here.', trigger.sender)
        return
    else:
        action = 'looks around, but doesn\'t see {}'.format(text[1])
    bot.action(action, trigger.sender)
