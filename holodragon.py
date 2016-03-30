"""
slap.py - Slap Module
Copyright 2009, Michael Yanovich, yanovich.net
Copyright 2016, Caleb Johnson, calebj.io
http://sopel.chat
"""

import random
import re
from sopel.module import commands

@commands('holodragon')
def holodragon(bot, trigger):
    """.holodragon [target] - Does holodragon things, with optional target"""
    text = trigger.group().split()
    prefix = 'transforms into a holodragon and '
    if len(text) < 2:
        verbs = [
          'flies around',
          'blasts the air with its giant mouth laser',
          'emits an ear-splitting roar',
          'occludes the sun in a menacing fashion'
        ]
        verb = random.choice(verbs)
        action = prefix + verb
    else:
        verbs = [
            'laser blasts {} into a smoking crater',
            'piledrives {} from orbit',
            'emits a roar so loud that {}\'s ears bleed',
            'stares into {}\'s very soul with enormous reptilian eyes'
            ]
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
                action = prefix + verb.format(text[1])
            else:
                action = prefix + verb + ' ' + text[1]
        elif trigger.sender not in bot.channels and bot.users.contains(text[1].lower()):
            bot.say('You and I are the only ones here.', trigger.sender)
            return
        else:
            action = 'looks around, but doesn\'t see {}'.format(text[1])
    bot.action(action, trigger.sender)
