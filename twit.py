"""
twitter.py - Sopel Twitter Module
Copyright 2008-10, Michael Yanovich, opensource.osu.edu/~yanovich/wiki/
Copyright 2011, Edward Powell, embolalia.net
Copyright 2016, Caleb Johnson, calebj.io
Licensed under the Eiffel Forum License 2.

http://sopel.chat
"""
import tweepy
import time
import re
from urllib.parse import urlsplit, urlunsplit
from sopel.config import ConfigurationError
from sopel.config.types import StaticSection, ValidatedAttribute
from sopel import tools
from sopel.module import rule, commands, priority, example, require_admin, interval

class TwitterAPIConfig(StaticSection):
    consumer_key = ValidatedAttribute('consumer_key', default=None)
    consumer_secret = ValidatedAttribute('consumer_secret', default=None)
    access_token = ValidatedAttribute('access_token', default=None)
    access_token_secret = ValidatedAttribute('access_token_secret', default=None)
    echo_tweets = ValidatedAttribute('echo_tweets', bool, default=False)
    echo_following = ValidatedAttribute('echo_following', bool, default=True)
    #FIXME poll_interval = ValidatedAttribute('poll_interval', int, default=15)

def configure(config):
    """
    These values are found by signing up your bot at
    [https://dev.twitter.com/apps/new](https://dev.twitter.com/apps/new).

    | [twitter] | example | purpose |
    | --------- | ------- | ------- |
    | consumer_key | 09d8c7b0987cAQc7fge09 | OAuth consumer key |
    | consumer_secret | LIaso6873jI8Yasdlfi76awer76yhasdfi75h6TFJgf | OAuth consumer secret |
    | access_token | 564018348-Alldf7s6598d76tgsadfo9asdf56uUf65aVgdsf6 | OAuth access token |
    | access_token_secret | asdfl7698596KIKJVGvJDcfcvcsfdy85hfddlku67 | OAuth access token secret |
    """

    config.define_section('twitter', TwitterAPIConfig, validate=False)
    config.twitter.configure_setting('consumer_key', 'Consumer key')
    config.twitter.configure_setting('consumer_secret', 'Consumer secret')
    config.twitter.configure_setting('access_token', 'Access token')
    config.twitter.configure_setting('access_token_secret', 'Access token secret')
    config.twitter.configure_setting('echo_tweets', 'Say tweets from followed accounts in IRC')
    config.twitter.configure_setting('echo_following', 'Echo tweets from all followed accounts? If disabled, accounts\n\
                                                     to echo must be manually added on a per-channel basis.')
    #FIXME config.twitter.configure_setting('poll_interval', 'Time (in seconds) to wait between checks for new tweets')

def setup(bot):
    getapi(bot)
    regex = re.compile('twitter.com\/(\S*)\/status\/([\d]+)')
    if not bot.memory.contains('url_callbacks'):
        bot.memory['url_callbacks'] = tools.SopelMemory()
    bot.memory['url_callbacks'][regex] = gettweet

def alreadytest(test, desired, f, args=None, printer=print, action_name=None,
                status_names=None, template = None, state=False):
    """helper function for toggling things
    If test matches desired, then f will not be run. and printer will be called with
    'already' or 'was not', depending on the desired state. If test does not match, 
    f(*args) will be run and printer will indicate it as such. Printer and f can be
    set to None to disable feedback or action.
    Returns true if f would be called."""
    if not action_name:
        action_name = 'in test state'
    if not status_names:
        if state:
            status_names = ('Now', 'Already', 'No longer', 'Wasn\'t')
        else:
            status_names = ('Successfully', 'Already', 'No longer', 'Wasn\'t')
    if not template:
        template = '{status} {action}.'
    if test is not desired:
        i = 0
        if f:
            if hasattr(args, '__getitem__'):
                f(*args)
            else:
                f(args)
    elif test is desired:
        i = 1
    if not desired: # if desired state is False, use opposite description
        i += 2
    if printer:
        printer(template.format(status=status_names[i], action=action_name))
    return test is not desired

def getargs(trigger):
    args = trigger.group(2)
    if args:
        args = str(args)
        args = args.split()
    return args


def getapi(bot):
    """Use a persistent API instead of creating a session for each command"""
    if not bot.memory.contains('tweepyapi'):
        try:
            auth = tweepy.OAuthHandler(bot.config.twitter.consumer_key, bot.config.twitter.consumer_secret)
            auth.set_access_token(bot.config.twitter.access_token, bot.config.twitter.access_token_secret)
            api = tweepy.API(auth)
            bot.memory['tweepyapi'] = api
        except:
            raise ConfigurationError('Could not authenticate with Twitter. Are the'
                                     ' API keys configured properly?')
    else:
        api = bot.memory['tweepyapi']
    return api


def format_thousands(integer):
    """Returns string of integer, with thousands separated by ','"""
    return re.sub(r'(\d{3})(?=\d)', r'\1,', str(integer)[::-1])[::-1]

def tweet_url(status):
    """Returns a URL to Twitter for the given status object"""
    return 'https://twitter.com/' + status.user.screen_name + '/status/' + status.id_str

def following(api, user):
    # TODO needs to check relationship instead of checking list
    if user[0].isdigit():
        user = int(user)
        return user in [f.id for f in api.friends()]
    else:
        if '@' in user:
            user = ''.join([c for c in user if c not in '@'])
        return user.lower() in [f.screen_name.lower() for f in api.friends()]

def favorited(api, statusid):
    # TODO limited to 20 statuses
    statusid = int(statusid)
    return statusid in [t.id for t in api.favorites()]

def _gettweet(api, id, num=None):
    """get status by user (latest or index) or id"""
    if type(id) is int or id.isdigit():
        id = int(id)
        status = api.get_status(id)
    else:
        twituser = id
        twituser = str(twituser)
        if len(api.user_timeline(twituser)) > 0:
            if not num or num is 0:
                status = api.user_timeline(twituser, count=1)[0]
            elif type(num) is int or num[0].isdigit():
                num = int(num)
                numinpage = num % 20
                page = int((num-numinpage)/20)+1
                status = api.user_timeline(twituser, page=page)[numinpage-1]
        else:
            raise IndexError('User has zero tweets.')
    return status

def _saytweet(bot, channel, status):
    twituser = '@' + status.user.screen_name
    bot.say(twituser + ": " + str(status.text) + ' <' + tweet_url(status) + '>', channel)

def isurl(value):
    """Returns bool whether string is a valid URL.
    Simplified version of django.core.validators.URLValidator"""
    ul = '\u00a1-\uffff'  # unicode letters range (must be a unicode string, not a raw string)

    # IP patterns
    ipv4_re = r'(?:25[0-5]|2[0-4]\d|[0-1]?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}'

    # Host patterns
    hostname_re = r'[a-z' + ul + r'0-9](?:[a-z' + ul + r'0-9-]{0,61}[a-z' + ul + r'0-9])?'
    # Max length for domain name labels is 63 characters per RFC 1034 sec. 3.1
    domain_re = r'(?:\.(?!-)[a-z' + ul + r'0-9-]{1,63}(?<!-))*'
    tld_re = (
        '\.'                                # dot
        '(?!-)'                             # can't start with a dash
        '(?:[a-z' + ul + '-]{2,63}'         # domain label
        '|xn--[a-z0-9]{1,59})'              # or punycode label
        '(?<!-)'                            # can't end with a dash
        '\.?'                               # may have a trailing dot
    )
    host_re = '(' + hostname_re + domain_re + tld_re + '|localhost)'

    regex = re.compile(
        r'^(?:[a-z0-9\.\-\+]*)://'  # scheme is validated separately
        r'(?:\S+(?::\S*)?@)?'  # user:pass authentication
        r'(?:' + ipv4_re + '|' + host_re + ')'
        r'(?::\d{2,5})?'  # port
        r'(?:[/?#][^\s]*)?'  # resource path
        r'\Z', re.IGNORECASE)
    message = 'Enter a valid URL.'
    schemes = ['http', 'https', 'ftp', 'ftps']

    value = str(value)
    scheme = value.split('://')[0].lower()
    if scheme not in schemes or len(urlsplit(value).netloc) > 253:
        return False
    elif regex.search(value):
        return True
    else:
        scheme, netloc, path, query, fragment = urlsplit(value)
        try:
            netloc = netloc.encode('idna').decode('ascii')  # IDN -> ACE
        except UnicodeError:  # invalid domain part
            raise e
        url = urlunsplit((scheme, netloc, path, query, fragment))
        return bool(regex.search(url))

###########################################################
### Non-admin commands that query twitter information
###########################################################

@commands('twit')
@priority('medium')
@example('.twit aplusk [tweetNum] or .twit 381982018927853568')
@rule('.*twitter.com\/(\S*)\/status\/([\d]+).*')
def gettweet(bot, trigger, found_match=None):
    """Show the last tweet by the given user or directly displays the given tweet ID"""
    try:
        api=getapi(bot)

        if found_match:
            status = _gettweet(api, found_match.group(2))
        else:
            tweetnum = 0
            args = getargs(trigger)
            if args:
                twituser = args[0]
                if len(args) > 1 and args[1].isdigit(): # should be str, no test for int
                    tweetnum = (args[1])
            else:
                twituser = api.me().screen_name
            status = _gettweet(api, twituser, tweetnum)
        _saytweet(bot, trigger.sender, status)
    except tweepy.TweepError as e:
        if e.api_code == 34:
            bot.reply('No such user.')
        else:
            bot.reply('Error: {}'.format(e.reason))
    except IndexError as e:
        if str(e) != str(IndexError()): # If message isn't the default, use it
            bot.reply(e)
        else:
            bot.reply('No such tweet.')

@commands('twitinfo', 'twinfo')
@priority('medium')
@example('.twitinfo aplsuk')
def f_info(bot, trigger):
    """Show information about the given Twitter account"""
    try:
        api=getapi(bot)
        args = getargs(trigger)
        if args:
            twituser = args[0]
        else:
            twituser = api.me().screen_name
        twituser = str(twituser)
        if '@' in twituser:
            twituser = ''.join([c for c in twituser if c not in '@'])

        info = api.get_user(twituser)
        friendcount = format_thousands(info.friends_count)
        name = info.name
        id = info.id
        favourites = info.favourites_count
        followers = format_thousands(info.followers_count)
        location = info.location
        description = info.description
        bot.reply("@" + str(twituser) + ": " + str(name) + ". " + "ID: " + str(id) + ". Following: " + friendcount + ". Followers: " + followers + ". Favorites: " + str(favourites) + ". Location: " + str(location) + ". Description: " + str(description))
    except tweepy.TweepError as e:
        if e.api_code == 34:
            bot.reply('No such user.')
        else:
            bot.reply('Error: {}'.format(e.reason))


###########################################################
### Commands that post statuses
###########################################################

def _tw_update(api, message, **kwargs):
    mlen = len(message)
    groups = message.split()
    for ss in groups:
        if isurl(ss):
            mlen -= len(ss)
            mlen += 23 # value of short_url_length as of 2016-03-28
    if mlen <= 140:
        api.update_status(message, **kwargs)
    else:
        toofar = len(message) - 140
        raise ValueError('Please shorten the length of your message by %i characters.' % toofar)

@commands('tweet')
@priority('medium')
@example('.tweet Hello World!')
@require_admin()
def f_update(bot, trigger):
    """Tweet with Sopel's account. Admin-only."""
    api=getapi(bot)
    update = str(trigger.group(2))# + " ^" + trigger.nick
    try:
        _tw_update(api, update)
        bot.reply("Successfully posted to my twitter account.")
    except Exception as e:
        bot.reply('Error: {}'.format(e))
    except tweepy.TweepError as e:
        bot.reply('Error: {}'.format(e.reason))


@commands('twreply')
@priority('medium')
@example('.twreply 892379487 I like that idea!')
@require_admin()
def f_reply(bot, trigger):
    """Reply to a tweet with Sopel's account. Admin-only."""
    api = getapi(bot)
    args = getargs(trigger)
    statusid = args[0]
    if statusid.isdigit():
        update = args[1:]
        statusid = int(statusid)
        try:
            status = _gettweet(api, statusid)
            _saytweet(bot, trigger.sender, status)
            message = '@%s ' % status.user.screen_name + ' '.join(update)
            _tw_update(api, message, in_reply_to_status_id=statusid)
            bot.reply("Successfully replied that tweet.")
        except Exception as e:
            bot.reply('Error: {}'.format(e))
        except tweepy.TweepError as e:
            bot.reply('Error: {}'.format(e.reason))

    else:
        bot.reply("Please provide a status ID.")

@commands('retweet')
@priority('medium')
@example('.retweet 892379487')
@require_admin()
def f_retweet(bot, trigger):
    """Retweets a given tweet ID with Sopel's account"""
    api=getapi(bot)
    args = getargs(trigger)
    if args and args[0].isdigit():
        statusid = int(args[0])
        try:
            api.retweet(statusid)
            status = _gettweet(api, statusid)
            _saytweet(bot, trigger.sender, status)
            bot.reply("Successfully retweeted.")
        except tweepy.TweepError as e:
            bot.reply('Error: {}'.format(e.reason))
    else:
        bot.reply("Please provide a status ID.")


###########################################################
### Commands that (un)follow and (un)favorite
###########################################################

@commands('twfav')
@priority('medium')
@example('.twfav 892379487')
@require_admin()
def f_favtweet(bot, trigger):
    """Favorites a given tweet ID with Sopel's account"""
    api=getapi(bot)
    args = getargs(trigger)
    if args and args[0].isdigit():
        statusid = int(args[0])
        fav = favorited(api, statusid)
        if alreadytest(fav, True, api.create_favorite, args=statusid,
                        printer=bot.reply, action_name = 'favorited'):
            status = _gettweet(api, statusid)
            _saytweet(bot, trigger.sender, status)
    else:
        bot.reply("Please provide a status ID.")


@commands('twunfav')
@priority('medium')
@example('.twunfav 892379487')
@require_admin()
def f_unfavtweet(bot, trigger):
    """Unfavorites a given tweet ID with Sopel's account"""
    api=getapi(bot)

    args = getargs(trigger)
    if args and args[0].isdigit():
        statusid = int(args[0])
        fav = favorited(api, statusid)
        if alreadytest(fav, False, api.destroy_favorite, args=statusid,
                        printer=bot.reply, action_name = 'favorited'):
            _saytweet(bot, trigger.sender, status)
    else:
        bot.reply("Please provide a status ID.")


@commands('twfollow')
@priority('medium')
@example('.twfollow aplusk')
@require_admin()
def f_follow(bot, trigger):
    """Follows the given user with Sopel's account"""
    api=getapi(bot)
    args = getargs(trigger)
    if args:
        userid = args[0]
        fol = following(api, userid)
        action = 'following ' + str(userid)
        try:
            alreadytest(fol, True, api.create_friendship, args=(userid, True), 
                        printer=bot.reply, action_name=action, state=True)
        except tweepy.TweepError as e:
            bot.reply('Error: {}'.format(e.reason))
    else:
        bot.reply("Please specify a user to follow.")


@commands('twunfollow')
@priority('medium')
@example('.twunfollow aplusk')
@require_admin()
def f_unfollow(bot, trigger):
    """Unfollows the given user with Sopel's account"""
    api=getapi(bot)
    args = getargs(trigger)
    if args:
        userid = args[0]
        fol = following(api, userid)
        action = 'following ' + str(userid)
        try:
            alreadytest(fol, False, api.destroy_friendship, args=(userid, True), 
                    printer=bot.reply, action_name=action, state=True)
        except tweepy.TweepError as e:
            bot.reply('Error: {}'.format(e.reason))
    else:
        bot.reply("Please specify a user to unfollow.")


#######################################################################
### Functions and commands related to per-channel following
#######################################################################

def channel_user_args(bot, trigger, args):
    """Helper function to get information about channel following"""
    if bot.config.twitter.echo_following:
        bot.reply('Note: echo of all followed accounts is enabled.')
    if args and args[0].startswith('#'):
        channel = args[0]
        cname = channel
        users = args[1:]
    elif trigger.sender.startswith('#'):
        channel = trigger.sender
        cname = 'this channel'
        users = args
    else:
        raise ValueError('Call with #channel as first argument.')

    if users: users = [''.join([c for c in u if c not in '@']) for u in users]

    if channel.lower() in [c.lower() for c in bot.channels]:
        cusers = bot.db.get_channel_value(channel, 'twitter_chan_following')
        if cusers: cusers = set([s.lower() for s in cusers])
        if users: users = set([s.lower() for s in users])
    else:
        raise ValueError('I\'m not in {}'.format(channel))

    return users, channel, cname, cusers


@commands('twchanfollow')
@priority('medium')
@example('.twchanfollow aplusk python (from channel)')
@example('.twchanfollow #channel aplusk python (from privmsg)')
@require_admin()
def f_chan_follow(bot, trigger):
    api=getapi(bot)
    args = getargs(trigger)
    if args:
        try:
            users, channel, cname, cusers = channel_user_args(bot, trigger, args)
            if len(users) is 0:
                raise ValueError('Please specify accounts(s) to follow.')
        except ValueError as e:
            bot.reply(e)
            return
        d = list(users - cusers if cusers else users) # difference
        # check for validity
        for a in d:
            try:
                _gettweet(api, a)
            except tweepy.TweepError as e:
                if e.api_code == 34:
                    bot.reply('Account %s does not exist.' % a)
                else:
                    bot.reply('Error: {}'.format(e.reason))
                users.remove(a)

        d = list(users - cusers if cusers else users) # difference
        u = list(users | cusers if cusers else users) # union
        i = list(users & cusers) if cusers else None # intersection
        if d:
            bot.db.set_channel_value(channel, 'twitter_chan_following', u)
            bot.reply('Now following account(s) {} in {}'.format(', '.join(d), cname))
        if i:
            bot.reply('Was already following account(s) {}'.format(', '.join(i), cname))
    else:
        bot.reply('Missing argument.')


@commands('twchanunfollow')
@priority('medium')
@example('.twchanunfollow aplusk python (from channel)')
@example('.twchanunfollow #channel aplusk python (from privmsg)')
@require_admin()
def f_chan_unfollow(bot, trigger):
    api=getapi(bot)
    args = getargs(trigger)
    if args:
        try:
            users, channel, cname, cusers = channel_user_args(bot, trigger, args)
            if len(users) is 0:
                raise ValueError('Please specify accounts(s) to unfollow.')
        except ValueError as e:
            bot.reply(e)
            return
        d = list(users - cusers if cusers else users) # difference
        id = list(cusers - cusers if cusers else users) # inverted difference
        i = list(users & cusers) if cusers else None # intersection
        if i:
            bot.db.set_channel_value(channel, 'twitter_chan_following', id)
            bot.reply('No longer following account(s) {} in {}'.format(', '.join(i), cname))
        if d:
            bot.reply('Wasn\'t following account(s) {}'.format(', '.join(d), cname))
    else:
        bot.reply('Missing argument.')


@commands('twchanfollowing')
@priority('medium')
@example('.twchanfollowing')
def f_chan_following(bot, trigger):
    args = getargs(trigger)
    try:
        users, channel, cname, cusers = channel_user_args(bot, trigger, args)
    except ValueError as e:
        bot.reply(e)
        return
    if cusers:
        bot.reply('Twitter accounts followed in {}: {}'.format(cname, ' '.join(cusers)))
    else:
        bot.reply('Not following any accounts in ' + cname)


#######################################################################
### Commands that change what is tweets are echoed in a channel
#######################################################################

@commands('twecho')
@priority('medium')
@example('.twecho (to show current setting)')
@example('.twecho [on|off]')
@require_admin()
def f_set_echo(bot, trigger):
    """Changes whether tweets are echoed in IRC, and whether the bot echoes all
    of the accounts it is following or only those enabled in the channel"""
    action = 'echoing tweets'
    re_on = '(?i)(y(es)?|t(rue)?|on)'
    re_off = '(?i)(no?|f(alse)?|off)'

    args = getargs(trigger)
    cur = bot.config.twitter.echo_tweets
    des = not cur

    if args:
        if re.match(re_on + '|' + re_off, args[0]):
            des = True if re.match(re_on, args[0]) else False
        else:
            bot.reply('Unknown argument.')
            return
        if alreadytest(cur, des, None, printer=bot.reply, action_name=action, 
                    state=True):
            bot.config.twitter.echo_tweets = des
            bot.config.save()
    elif cur:
        bot.reply('Currently ' + action)
    else:
        bot.reply('Not ' + action)

@commands('twechomode')
@priority('medium')
@example('.twechomode (to show current setting)')
@example('.twechomode [global|channel]')
@require_admin()
def f_set_echo_mode(bot, trigger):
    """Changes  whether the bot echoes all of the accounts it is following or
    only those enabled in the channel"""
    action = 'echoing tweets from all followed accounts'
    re_all = '(?i)(a(ll)?|g(lobal)?)'
    re_chan = '(?i)(c(han(nel)?)?)'

    args = getargs(trigger)
    cur = bot.config.twitter.echo_following
    des = not cur

    if args:
        if re.match(re_all + '|' + re_chan, args[0]):
            des = True if re.match(re_all, args[0]) else False
        else:
            bot.reply('Unknown argument.')
            return
        if alreadytest(cur, des, None, printer=bot.reply, action_name=action, 
                    state=True):
            bot.config.twitter.echo_following = des
            bot.config.save()
    elif cur:
        bot.reply('Currently ' + action)
    else:
        bot.reply('Not ' + action)


#######################################################################
### Commands and functions related to twitter polling
#######################################################################

@commands('twpoll')
@require_admin()
def manual_poll_tweets(bot, trigger):
    """Force a check for new tweets, circumventing the interval timer"""
    poll_tweets(bot)

# FIXME: Get poll interval from config
@interval(60)
@priority('medium')
def poll_tweets(bot):
    if bot.config.twitter.echo_tweets:
        api=getapi(bot)

        # Build update list from all following or from channel following
        if bot.config.twitter.echo_following:
            pollaccounts = set([f.screen_name.lower() for f in api.friends(count=200)])
        else:
            pollaccounts = set()
            for channel in bot.channels:
                cusers = bot.db.get_channel_value(channel, 'twitter_chan_following')
                if cusers:
                    cusers = set([s.lower() for s in cusers])
                    pollaccounts |= cusers

        # First time run for bot session?
        init = not bot.memory.contains('latesttweets')

        # All account info is "new" on init, else filter newly added
        newaccounts = pollaccounts
        if bot.memory.contains('twitter_pollaccounts'):
            newaccounts = pollaccounts - bot.memory['twitter_pollaccounts'] 
        bot.memory['twitter_pollaccounts'] = pollaccounts

        # Persistent storage of dict with latest tweets
        lt = {} if init else bot.memory['latesttweets']
        # Temp dict with new tweets
        et = {}

        for account in pollaccounts:
            since = None
            # Get status since last remembered update if we haven't just started following
            if account in lt.keys() and not account in newaccounts:
                since = lt[account].id
            latest = api.user_timeline(account, since_id=since, count=1)
            if latest:
                latest = latest[0] # user_timeline returns a dict
                lt[account] = latest
                if account not in newaccounts:
                    et[account] = latest
        bot.memory['latesttweets'] = lt

        for channel in bot.channels:
            if bot.config.twitter.echo_following:
                    sayupdates = et.keys()
            else:
                cusers = bot.db.get_channel_value(channel, 'twitter_chan_following')
                cusers = set([s.lower() for s in cusers])
                sayupdates = set(et.keys()) & cusers
            for account in sayupdates:
                    status = et[account]
                    _saytweet(bot, channel, status)

if __name__ == '__main__':
    print(__doc__.strip())
