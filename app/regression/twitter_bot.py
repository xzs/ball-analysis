import tweepy
import pprint
import time
from datetime import date, timedelta

from sqlfetch import sportvu_queries, execute_query, player_game_queries

pp = pprint.PrettyPrinter(indent=4)

DATE = date.today()

auth = tweepy.OAuthHandler('Jg0wBggNAGKdAQd9o8knXILfr', 'VV3ak3QeKU7a8LTCaymFZcmB2IayO6AbyQzjVe5E2yB1KLwmav')
auth.set_access_token('725942365567881216-FdBbhbiPIGwkEkEZ4WTSnvEZgTiNAaJ', 'jJrpFpml79ILVW9aa22ERBa3api0srxHOPmEe4067fBQ8')

api = tweepy.API(auth)

GUARD_STATS = ['PULL_UP_3FGA_PER_GAME', 'PULL_UP_FG3_PCT', 'PULL_UP_FGA_PER_GAME', 'PULL_UP_FG_PCT', 'PULL_UP_PTS_PER_GAME',
                'DRIVES_PER_GAME', 'DRIVE_PF_PER_GAME', 'DRIVE_PF_PCT', 'DRIVE_FG_PCT', 'DRIVE_FGA_PER_GAME', 'DRIVE_PTS_PER_GAME',
                'TOUCHES_PER_GAME', 'PTS_PER_TOUCH', 'TIME_OF_POSS_PER_GAME', 'PASSES_RECEIVED_PER_GAME', 'PASSES_MADE_PER_GAME',
                'CATCH_SHOOT_3FGA_PER_GAME', 'CATCH_SHOOT_FG3_PCT','CATCH_SHOOT_FGA_PER_GAME', 'CATCH_SHOOT_FG_PCT']

FORWARD_STATS = ['OREB_PER_GAME','REB_PER_GAME', 'REB_CHANCE_PCT',
                    'FG_AT_RIM_FACED_PER_GAME','FG_AT_RIM_ALLOWED_PER_GAME','DEF_RIM_FG_PCT'
                    'TOUCHES_PER_GAME', 'TIME_OF_POSS_PER_GAME', 'PTS_PER_TOUCH','PASSES_RECEIVED_PER_GAME',
                    'PAINT_TOUCHES_PER_GAME','PAINT_TOUCH_FGA_PER_GAME', 'PAINT_TOUCH_FG_PCT',
                    'POST_TOUCHES_PER_GAME', 'POST_TOUCH_FGA_PER_GAME', 'POST_TOUCH_FG_PCT']

ALL_GUARDS = ['Kyle Lowry', 'DeMar DeRozan', 'DeMarre Carroll', 'Paul George']
ALL_FORWARDS = []

TRANSCRIBE_STAT_DICT = {
    'AST_PTS_CREATED_PER_GAME' : 'pts created off assists per game',
    'OREB_PER_GAME' : 'OREB per game',
    'PULL_UP_3FGA_PER_GAME' : 'pull up 3s per game',
    'AVG_OREB_DIST' : '',
    'POST_TOUCH_FG_PCT' : '% from attempts off of post touches',
    'POST_TOUCHES_PER_GAME' : 'post touches per game',
    'REB_PER_GAME' : 'REB per game',
    'AVG_DREB_DIST' : '',
    'PULL_UP_FGA_PER_GAME' : 'pull up attempt per game',
    'TEAM_NAME' : '',
    'DRIVE_PF_PER_GAME' : 'fouls drawn from drives per game',
    'DRIVES_PER_GAME' : 'drives per game',
    'DEF_RIM_FG_PCT' : '% at the rim',
    'PULL_UP_FG_PCT' : '% from pull ups',
    'DRIVE_FG_PCT' : '% from attempts off of drives',
    'TIME_OF_POSS_PER_GAME' : '',
    'PASSES_RECEIVED_PER_GAME' : 'passes received per game',
    'DREB_CHANCE_PCT' : '% ',
    'AVG_SEC_PER_TOUCH' : '',
    'GP' : '',
    'PAINT_TOUCHES_PER_GAME' : 'paint touches per game',
    'ELBOW_TOUCHES_PER_GAME' : 'elbow touches per game',
    'DREB_PER_GAME' : 'DREB per game',
    'ELBOW_TOUCH_FGA_PER_GAME' : '',
    'DRIVE_PTS_PER_GAME' : 'pts off of drives',
    'PTS_PER_TOUCH' : 'pts per touch',
    'PULL_UP_FG3_PCT' : '% from pull up 3s',
    'TOUCHES_PER_GAME' : 'touches per game',
    'CATCH_SHOOT_FG3_PCT' : '% from catch and shoot 3s',
    'FG_AT_RIM_FACED_PER_GAME' : '',
    'OREB_CHANCE_PCT' : '% of getting a OREB ',
    'CATCH_SHOOT_FG_PCT' : '% from catch and shoot attempts',
    'PAINT_TOUCH_PASSES_PER_GAME' : '',
    'POST_TOUCH_PASSES_PER_GAME' : '',
    'PULL_UP_EFG_PCT' : '% ',
    'AVG_REB_DIST' : '',
    'DRIVE_PF_PCT' : '% chance of getting fouled from drives',
    'ELBOW_TOUCH_PASSES_PER_GAME' : '',
    'DIST_MILES_PER_GAME' : '',
    'PAINT_TOUCH_FGA_PER_GAME' : 'FGA from paint touches per game',
    'NAME' : '',
    'PULL_UP_PTS_PER_GAME' : 'pts from pull ups',
    'PAINT_TOUCH_FG_PCT' : '% ',
    'CATCH_SHOOT_FGA_PER_GAME' : 'catch and shoot attempts per game',
    'CATCH_SHOOT_EFG_PCT' : '% ',
    'POST_TOUCH_FGA_PER_GAME' : '',
    'DRIVE_FGA_PER_GAME' : 'FGA from drives',
    'PASSES_MADE_PER_GAME' : 'passes made per game',
    'REB_CHANCE_PCT' : '% ',
    'AVG_SPEED' : '',
    'CATCH_SHOOT_3FGA_PER_GAME' : 'catch and shoot attempts from 3s per game',
    'FG_AT_RIM_ALLOWED_PER_GAME' : 'FG at the rim',
    'ELBOW_TOUCH_FG_PCT' : '% '
}


def construct_playoffs_tweet(teams):
    tweet_list = []
    results = execute_query(sportvu_queries('player', 0, teams, DATE))

    for stat in results:
        print stat
        if stat['NAME'] in ALL_GUARDS or stat['NAME'] in ALL_FORWARDS:
            for key, value in stat.iteritems():
                print key
                if (stat['NAME'] in ALL_GUARDS and key in GUARD_STATS) or (stat['NAME'] in ALL_FORWARDS and key in FORWARD_STATS):
                    if type(value) is not str and key != 'GP':
                        tweet = 'Per sportvu, %(player)s is averaging %(stat_value)s %(stat_name)s in the playoffs #NBAPlayoffs #%(team_name)s' % {
                            'player': stat['NAME'],
                            'stat_name': key,
                            'stat_value': value,
                            'team_name': stat['TEAM_NAME']
                        }
                        tweet_list.append(tweet)

    for tweet in tweet_list:
        print tweet
        # api.update_status(tweet)
        # yield every 2 minures
        # time.sleep(120)
    return tweet_list


# playoffs
query_result_playoffs = execute_query(player_game_queries('2016-04-15', '2016-04-29', ['TOR', 'IND']))
# regular season
query_result_season = execute_query(player_game_queries('2015-10-27', '2016-04-15', ['TOR', 'IND']))

compare_player_playoff_sportvu_stats(query_result_season, query_result_playoffs)


construct_playoffs_tweet(['TOR', 'IND'])

# the tweets need to be more readable
'''
    To Do:
        - Translations for the column headers (better names)
        - Get players based on their playtimes for the past games
        - Tweet not in particular order (if possible)
        - Dynamically generate the pool of data every day

'''





