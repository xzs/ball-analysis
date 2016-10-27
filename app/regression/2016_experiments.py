import MySQLdb
import pprint
import logging
import glob
import pandas as pd
import numpy as np
import sqlfetch
import operator
import json
import csv
from datetime import date, timedelta
import requests

import warnings
# explictly not show warnings
warnings.filterwarnings("ignore")

import urllib2
from bs4 import BeautifulSoup

# this is the standard import if you're using "formula notation" (similar to R)
import statsmodels.formula.api as smf
from sklearn.linear_model import LinearRegression
import MySQLdb.converters

pp = pprint.PrettyPrinter(indent=1)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

YEAR = '2017'
LAST_DATE_REG_SEASON = '2016-04-15'
FIRST_DATE_REG_SEASON = '2015-10-27'
conv = MySQLdb.converters.conversions.copy()
conv[246] = float    # convert decimals to floats
conv[10] = str       # convert dates to strings

DATE_FORMAT_YEAR = str("%Y-%m-%d")
LAST_DATE_REG_SEASON = '2016-04-15'
FIRST_DATE_REG_SEASON = '2015-10-27'

FIRST_DATE_PRE_SEASON = '2016-10-01'
LAST_DATE_PRE_SEASON = '2016-10-15'


def starting_line_query(players, date_1, date_2):
    query = 'SELECT ub.player_name as NAME, '\
    'ROUND(Avg(ub.USG_PCT), 3) as USAGE_PCT, '\
    'ROUND(Avg(tb.MIN), 3) as MIN, '\
    'ROUND(Avg(tb.FG3M), 3) as FG3M, '\
    'ROUND(Avg(tb.REB), 3) as REB, '\
    'ROUND(Avg(tb.AST), 3) as AST, '\
    'ROUND(Avg(tb.STL), 3) as STL, '\
    'ROUND(Avg(tb.BLK), 3) as BLK, '\
    'ROUND(Avg(tb.TO), 3) as TOV, '\
    'ROUND(Avg(tb.PTS), 3) as PTS, '\
    'ROUND(Avg(tb.FG3M * 0.5 + tb.REB * 1.25 + tb.AST * 1.25 + tb.STL * 2 + tb.BLK * '\
    '2 + tb.TO *- 0.5 + tb.PTS * 1), 3) AS DK_POINTS,'\
    'ROUND(Avg(tb.FG3M * 0.5 + tb.REB * 1.25 + tb.AST * 1.25 + tb.STL * 2 + tb.BLK * '\
    '2 + tb.TO *- 0.5 + tb.PTS * 1),3) / ROUND(Avg(tb.MIN), 3) as FP_PER_MIN '\
    'FROM   usage_boxscores AS ub '\
    'LEFT JOIN game_summary AS gs '\
        'ON gs.game_id = ub.game_id '\
    'LEFT JOIN traditional_boxscores AS tb '\
        'ON tb.game_id = ub.game_id '\
            'AND tb.player_id = ub.player_id '\
    'INNER JOIN (SELECT game_id '\
            'FROM   traditional_boxscores) AS tb3 '\
        'ON tb3.game_id = ub.game_id '\
            ' AND Str_to_date(gs.game_date_est, "%(date_format_year)s") >= "%(date_begin)s" '\
            ' AND Str_to_date(gs.game_date_est, "%(date_format_year)s") <= "%(date_end)s" '\
    'WHERE ub.PLAYER_NAME IN ("%(players)s") '\
    'GROUP  BY NAME '\
    'ORDER BY USAGE_PCT DESC' % {'date_format_year': DATE_FORMAT_YEAR, 'players': players, 'date_begin': date_1, 'date_end': date_2,}

    return query
def execute_query(sql_query):
    query_result = None

    try:
        # Open database connection
        db = MySQLdb.connect("127.0.0.1","root","","nba_scrape", conv=conv)

        # prepare a cursor object using cursor() method
        cursor = db.cursor()
        # Execute the SQL command
        cursor.execute(sql_query)
        query_result = [dict(line) for line in [zip([column[0] for column in cursor.description],
                     row) for row in cursor.fetchall()]]
        db.close()

    except:
        print "Error: unable to fetch data"

    return query_result

def get_player_college():
    url = urllib2.urlopen('http://www.basketball-reference.com/players/k/knighbr03/gamelog/2016')
    soup = BeautifulSoup(url, 'html5lib')

    info = soup.find('div', attrs={'itemtype':'http://schema.org/Person'})
    personal_info = info.find_all('a')
    basic_info = {}
    for row in personal_info:
        # parse the link
        link = row.get('href')
        params = link.split('?')
        if link and len(params) > 1:
            params = params[1]
            for param in params.split('&'):
                link_value = param.split('=')
                basic_info[link_value[0]] = link_value[1] if len(link_value) > 1 else None

                return basic_info['college']

'''
    Does DvP affect bottom players more so than top player?

    No, they don't
'''
def get_all_players():
    query = 'SELECT tb.player_name, '\
            'avg(tb.FG3M*0.5 + tb.REB*1.25 + tb.AST*1.25 + tb.STL*2 + tb.BLK*2 + tb.TO*-0.5 + tb.PTS*1) as dk_points '\
            'FROM traditional_boxscores AS tb '\
            'GROUP BY tb.PLAYER_NAME '\
            'ORDER BY dk_points ASC'

    return query

# we use the get_all_players to simply get the rank for dk_points
def categorize_players():
    players = execute_query(get_all_players())
    num_players = len(players)
    # 25, 50, 75, 90,
    player_dict = {}
    step = int(num_players * 0.15)
    for index in range(0,7):

        dict_key = 'Q'+str(index)
        # get the starting block
        next_ = step * index
        # get the ending block (which is one step ahead)
        more_next_ = step * (index + 1)

        for player in players[next_:more_next_:]:
            if dict_key not in player_dict:
                player_dict[dict_key] = []
                player_dict[dict_key].append(player['player_name'])
            else:
                player_dict[dict_key].append(player['player_name'])

    return player_dict

def process_lr(player_dict):
    result_dict = {
        'vs_dvp': {},
        'vs_margin': {}
    }

    ISSUE_NAMES = ['Kelly Oubre Jr.', 'Nene', 'Patty Mills', 'Xavier Munford']

    # For each Q of players
    for file in glob.glob('../scrape/mod_player_logs/'+YEAR+'/*.csv'):
        player_name = file.split('/')[4].split('.c')[0]

        if player_name in player_dict:
            if player_name not in ISSUE_NAMES:
                data = pd.read_csv(file)
                data.columns = ['Rk','G','Date','Age','Tm','isHome','Opp','Margin','GS','MP','FG','FGA',
                'FGPercent','ThreeP','ThreePA','ThreePPercent','FT','FTA','FTPercent','ORB','DRB','TRB','AST','STL','BLK','TOV','PF',
                'PTS','GmSc','+/-','DFS','Pos','OppDvP','OppPace','OppPF','OppFGA','OppDRtg','OppORtg','OppTOVPercent',
                'OppDefgPercent','Opp3PPercentAllowed','OppTRBAllowed','OppASTAllowed','OppPTSPerGAllowed',
                'OppFGPercentAllowed','OppSTLAllowed','OppFTAAllowed','OppBLKAllowed','OppTOVAllowed','TRBPercent','isConference']
                if not data.empty and len(data.index) > 1:
                    try:
                        opp_data = smf.ols(formula='DFS ~ OppDvP', data=data).fit()
                        for key, value in opp_data.pvalues.iteritems():
                            if key != 'Intercept':
                                if value <= 0.05:
                                    result_dict['vs_dvp'][player_name] = value

                        game_data = smf.ols(formula='DFS ~ Margin', data=data).fit()
                        for key, value in game_data.pvalues.iteritems():
                            if key != 'Intercept':
                                if value <= 0.05:
                                    result_dict['vs_margin'][player_name] = value

                    except ValueError:  #raised if `y` is empty.
                        pass

    return result_dict

def experiment_runner():
    RESULT_DICT = {}
    players_quant_dict = categorize_players()
    for quant, players in players_quant_dict.iteritems():
        RESULT_DICT[quant] = process_lr(players)

'''
    How to players perform when facing teams
    # Atlantic: Toronto, Boston, New York, Brooklyn, Philadelphia
    # Central: Cleveland, Indiana, Detroit, Chicago, Milwaukee
    # Southeast: Miami, Atlanta, Charlotte, Washington, Orlando
    # Northwest: Oklahoma City, Portland, Utah, Denver, Minnesota
    # Pacific: Golden State, Los Angeles Clippers, Sacramento, Phoenix, Los Angeles
    # Southwest: San Antonio, Dallas, Memphis, Houston, New Orleans

    # Lets see how many players actually played better (in terms of DFS points) when faced against their division rivals

'''


def set_teams_division():
    # based on sql db
    NBA_DIVISIONS  = {
        'div_atlantic': ['TOR', 'BOS', 'NYK', 'BKN', 'PHI'],
        'div_central': ['CLE', 'IND', 'DET', 'CHI', 'MIL'],
        'div_southeast': ['MIA', 'ATL', 'CHA', 'WAS', 'ORL'],
        'div_northwest': ['OKC', 'POR', 'UTA', 'DEN', 'MIN'],
        'div_pacific': ['GSW', 'LAC', 'SAC', 'PHX', 'LAL'],
        'div_southwest': ['SAS', 'DAL', 'MEM', 'HOU', 'NOP']
    }

    ALL_TEAMS = []
    for key, division in NBA_DIVISIONS.iteritems():
        for team in division:
            ALL_TEAMS.append(team)

    TEAM_RIVALS = {}
    # go through each team and create a dict for each team with its division rivals
    for team in ALL_TEAMS:
        for key, division in NBA_DIVISIONS.iteritems():
            if team in division:
                TEAM_RIVALS[team] = []
                for rival_team in division:
                    if rival_team != team:
                        TEAM_RIVALS[team].append(rival_team)
    return TEAM_RIVALS

TEAM_COUNT = {}
# Get all player logs
def calc_player_division_effort(player_name):
    TEAMS_AGAINST = {}
    player_log = execute_query(sqlfetch.full_player_log(player_name, FIRST_DATE_REG_SEASON, LAST_DATE_REG_SEASON, 0, 0) + 'ORDER BY DK_POINTS DESC')
    rival_count = 0
    half_way = len(player_log)/4 if len(player_log) > 3 else 1
    for game in player_log[:half_way]:

        if game['TEAM_AGAINST'] in TEAMS_AGAINST:
            TEAMS_AGAINST[game['TEAM_AGAINST']] += 1
        else:
            TEAMS_AGAINST[game['TEAM_AGAINST']] = 1

        if game['TEAM_AGAINST'] in TEAM_RIVALS[game['TEAM_NAME']]:
            rival_count += 1

        # let's also keep a count of the team name
        if game['TEAM_AGAINST'] in TEAM_COUNT:
            TEAM_COUNT[game['TEAM_AGAINST']] += 1
        else:
            TEAM_COUNT[game['TEAM_AGAINST']] = 1
    print player_name
    print TEAMS_AGAINST
    # for top players this is not a case? since they are good everywhere?
    return player_name, float(rival_count)/float(half_way) * 100

# TEAM_RIVALS = set_teams_division()
def division_experiment_runner():
    players_quant_dict = categorize_players()

    # for quant, players in players_quant_dict['Q6']:
    for player in players_quant_dict['Q6']:
        calc_player_division_effort(player)

'''
    Based on the number of times each team have occurred in player's top 50%
    what were those team's ranks from the synergy tracking
'''
def team_ranks_from_top():
    test_data = {
        'ATL': 439, 'BKN': 466, 'BOS': 440, 'CHA': 418, 'CHI': 436, 'CLE': 385,
        'DAL': 416, 'DEN': 457, 'DET': 391, 'GSW': 441, 'HOU': 469, 'IND': 409,
        'LAC': 411, 'LAL': 491, 'MEM': 407, 'MIA': 402, 'MIL': 462, 'MIN': 414,
        'NOP': 450, 'NYK': 417, 'OKC': 418, 'ORL': 461, 'PHI': 499, 'PHX': 473,
        'POR': 426, 'SAC': 470, 'SAS': 362, 'TOR': 399, 'UTA': 344, 'WAS': 450
    }

    pace_query = 'select ab.TEAM_ABBREVIATION as TEAM, ROUND(avg(ab.pace), 2) as avgPace FROM `advanced_boxscores_team` as ab GROUP BY TEAM'
    TEAM_PACE = execute_query(pace_query)

    TEAM_DICT = {}
    for team, num_times in test_data.iteritems():
        TEAM_DICT[team] = {
            'occurred': num_times
        }
    for team in TEAM_PACE:
        TEAM_DICT[team['TEAM']]['pace'] = team['avgPace']

    TEAM_SYNERGY_RANKS = execute_query(sqlfetch.get_team_synergy_ranks())

    # print TEAM_SYNERGY_RANKS
    for team in TEAM_SYNERGY_RANKS:
        # print team
        for key, value in team.iteritems():
            if key != 'TEAM_NAME':
                TEAM_DICT[team['TEAM_NAME']][key] = value

'''
    Get a map of the locations and counts and players of where the team got scored on
'''

# Ideally I want to get a map of where players scored at a similar rate
# We need to also leverage this data and see how
def get_location_map():

    query = 'SELECT shots.GAME_ID, PLAYER_NAME, TEAM_NAME, SHOT_TYPE, SHOT_ZONE_AREA, SHOT_ZONE_BASIC, CONCAT(SHOT_ZONE_BASIC, ", ", SHOT_ZONE_AREA) as SHOT_LOCATION '\
        'FROM shots '\
        'INNER JOIN ( '\
            'SELECT tbt.game_id FROM traditional_boxscores_team as tbt '\
                'INNER JOIN (SELECT game_id FROM traditional_boxscores_team) as tbt2 ON tbt.game_id = tbt2.game_id '\
                'WHERE tbt.team_abbreviation = "TOR" ORDER BY game_id '\
        ') as tb3 ON tb3.game_id = shots.game_id '\
        'WHERE TEAM_NAME != "Toronto Raptors" AND SHOT_MADE_FLAG = 1 '\
        'ORDER BY PLAYER_NAME' 
    query_result = execute_query(query)
    shots_against = {
        'location': {}
    }

    # Sort the totals
    for shot in query_result:
        location = shot['SHOT_LOCATION']
        player_name = shot['PLAYER_NAME']
        team_name = shot['TEAM_NAME']
        game_id = shot['GAME_ID']

        if location in shots_against['location']:
            area = shots_against['location'][location]
            area['num_shots'] += 1

            teams = area['teams']

            if game_id not in area['games']:
                area['games'].append(game_id)

            area['num_shots_per'] = area['num_shots'] / len(area['games'])

            if team_name in teams:
                team = teams[team_name]
                team['num_shots'] += 1

                if game_id not in team['games']:
                    team['games'].append(game_id)

                if player_name in team['players']:
                    team_player = team['players'][player_name]
                    team_player['num_shots'] += 1

                    if game_id not in team_player['games']:
                        team_player['games'].append(game_id)

                    team_player['num_shots_per'] = team_player['num_shots'] / len(team_player['games'])

                else:
                    team['players'][player_name] = {
                        'num_shots': 1,
                        'num_shots_per': 1,
                        'games': [game_id]
                    }

                team['num_shots_per'] = team['num_shots'] / len(team['games'])
            else:
                teams[team_name] = {
                    'num_shots': 1,
                    'games': [game_id],
                    'players': {
                        player_name: {
                            'num_shots': 1,
                            'games': [game_id]
                        }
                    }
                }

            players = area['players']
            if player_name in players:
                player = players[player_name]
                player['num_shots'] += 1

                if game_id not in player['games']:
                    player['games'].append(game_id)

                player['num_shots_per'] = player['num_shots'] / len(player['games'])
            else:
                players[player_name] = {
                    'num_shots': 1,
                    'games': [game_id]
                }
        else:
            shots_against['location'][location] = {
                'num_shots': 1,
                'games': [game_id],
                'teams': {
                    team_name: {
                        'num_shots': 1,
                        'games': [game_id],
                        'players': {
                            player_name: {
                                'num_shots': 1,
                                'games': [game_id]
                            }
                        }
                    }
                },
                'players': {
                    player_name: {
                        'num_shots': 1,
                        'games': [game_id]
                    }
                }
            }

    return shots_against


'''

Get the deviation

'''
SORTED_DEVIATION = {}
def calc_standard_deviation(player_name):
    player_log = execute_query(sqlfetch.full_player_log(player_name, FIRST_DATE_REG_SEASON, LAST_DATE_REG_SEASON, 0, 0) + 'AND ub.MIN >= 20 ORDER BY DATE ASC')

    dk_points_list = []
    for game in player_log:
        dk_points_list.append(game['DK_POINTS'])

    # if len(player_log) > 0:
    #     comp_std = np.std(dk_points_list) / player_log[len(player_log) - 1]['DK_POINTS']
    #     print player_name, comp_std
    # else:
    #     print 'n/a'
    if len(player_log) > 0:
        comp_std = np.std(dk_points_list)
        SORTED_DEVIATION[player_name] = comp_std

def deviation_experiment_runner():
    players_quant_dict = categorize_players()

    # for quant, players in players_quant_dict['Q6']:
    for player in players_quant_dict['Q6']:
        calc_standard_deviation(player)
    SORTED_DEVIATION = sorted(SORTED_DEVIATION.items(), key=operator.itemgetter(1))


TEAMS = {
    'ATL':'Atlanta Hawks',
    'BOS':'Boston Celtics',
    'BRK':'Brooklyn Nets',
    'CHO':'Charlotte Hornets',
    'CHI':'Chicago Bulls',
    'CLE':'Cleveland Cavaliers',
    'DAL':'Dallas Mavericks',
    'DEN':'Denver Nuggets',
    'DET':'Detroit Pistons',
    'GSW':'Golden State Warriors',
    'HOU':'Houston Rockets',
    'IND':'Indiana Pacers',
    'LAC':'Los Angeles Clippers',
    'LAL':'Los Angeles Lakers',
    'MEM':'Memphis Grizzlies',
    'MIA':'Miami Heat',
    'MIL':'Milwaukee Bucks',
    'MIN':'Minnesota Timberwolves',
    'NOP':'New Orleans Pelicans',
    'NYK':'New York Knicks',
    'OKC':'Oklahoma City Thunder',
    'ORL':'Orlando Magic',
    'PHI':'Philadelphia 76ers',
    'PHO':'Phoenix Suns',
    'POR':'Portland Trail Blazers',
    'SAC':'Sacramento Kings',
    'SAS':'San Antonio Spurs',
    'TOR':'Toronto Raptors',
    'UTA':'Utah Jazz',
    'WAS':'Washington Wizards'
}


# teams_starters = {}
# all_starters = []
# for team in TEAMS:
#     with open('../scrape/misc/depth_chart/'+team+'.json') as data_file:
#         data = json.load(data_file)
#         positions = ['PG', 'SG', 'SF', 'PF', 'C']
#         for position in positions:
#             if position in teams_starters:
#                 teams_starters[position].append(str(data[position][0]['player']))
#             else:
#                 teams_starters[position] = []
#                 teams_starters[position].append(str(data[position][0]['player']))
#             all_starters.append(str(data[position][0]['player']))


# pp.pprint(teams_starters)

# for position, starters in teams_starters.iteritems():
#     players = '","'.join(starters)
#     starter_defensive_ranks = execute_query(sqlfetch.get_starter_defensive_stats(players))
#     starter_offensive_ranks = execute_query(sqlfetch.get_starter_offensive_stats(players))

# with open('nba_scrape/query_result.json') as data_file:
#     data = json.load(data_file)
#     dk_points_list = []
#     for player in data['data']:
#         dk_points_list.append(player['DK_POINTS'])

#         # for each player how does it compare to their avg?
#     # print np.median(dk_points_list)
#     # print np.average(dk_points_list)

PLAYER_IDS = execute_query(sqlfetch.get_player_names())
PLAYER_OBJ = {}
for player in PLAYER_IDS:
    PLAYER_OBJ[player['PLAYER_ID']] = player['PLAYER_NAME']

def process_player_lineup(data, lineup_obj):
    for row in data:
        lineup = []
        for category, value in row.iteritems():
            if category != 'GAME_ID' and value != None:
                lineup.append(PLAYER_OBJ[value])

        # by line ups
        player_lineup = ', '.join(sorted(lineup))
        if player_lineup in lineup_obj:
            lineup_obj[player_lineup] += 1
        else:
            lineup_obj[player_lineup] = 1

    return lineup_obj

def lineups_from_pbp():

    pbp_actions = {
        '1, 2': 'FGA',
        '4': 'REB'
    }
    player_id_by_team = execute_query(sqlfetch.get_player_id_by_team('TOR'))
    by_lineup_pct = {}


    # for each player calculate the % of contribution for stats based on the lineups
    for player_id in player_id_by_team:
        for action, stat in pbp_actions.iteritems():
            # total lineup
            by_lineup_total = {}
            total_data = execute_query(sqlfetch.get_totals_by_home_lineup('TOR', action))
            by_lineup_total = process_player_lineup(total_data, by_lineup_total)

            by_lineup = {}
            log_data = execute_query(sqlfetch.get_lineups_per_action(player_id['PLAYER_ID'], 'TOR', action))
            by_lineup = process_player_lineup(log_data, by_lineup)

            # i want to know what % of rebounds the player gets on the court for a given lineup
            # i also need to know the # of minutes played per game on avg
            for lineup, player_total in by_lineup.iteritems():
                if lineup in by_lineup_total:

                    player_name = PLAYER_OBJ[player_id['PLAYER_ID']]

                    if lineup in by_lineup_pct:

                        if player_name in by_lineup_pct[lineup]:
                            by_lineup_pct[lineup][player_name][stat] = {
                                'total': float(by_lineup_total[lineup]),
                                'player': float(player_total),
                                'pct': float(player_total) / float(by_lineup_total[lineup]) * 100
                            }
                        else:
                            by_lineup_pct[lineup][player_name] = {
                                stat : {
                                    'total': float(by_lineup_total[lineup]),
                                    'player': float(player_total),
                                    'pct': float(player_total) / float(by_lineup_total[lineup]) * 100
                                }
                            }
                    else:
                        by_lineup_pct[lineup] = {
                            player_name: {
                                stat : {
                                    'total': float(by_lineup_total[lineup]),
                                    'player': float(player_total),
                                    'pct': float(player_total) / float(by_lineup_total[lineup]) * 100
                                }
                            }

                        }

        # i need to also count by most actions
        # pp.pprint(by_lineup_pct)



# lineups_from_pbp()

# CJ McCollum
# Maurice Harkless

def process_playtime(playtime_seconds, record):
    playtime = record.split(':')
    if len(playtime) > 1:
        playtime_seconds += int(playtime[0])*60 + int(playtime[1])
    else:
        playtime_seconds = 0

    return playtime_seconds

TRANSLATE_DICT = {
    'CHO':'CHA',
    'BRK':'BKN'
}

def get_fantasy_lab_news():

    # http://www.fantasylabs.com/api/players/news/2/
    url = 'http://www.fantasylabs.com/api/players/news/2/'
    response = requests.get(url)
    data = response.json()
    fantasy_labs_news = {}
    for news in data:
        # only get the latest news for player
        if news['PlayerName'] not in fantasy_labs_news:
            fantasy_labs_news[news['PlayerName']] = {
                'news': news['News'],
                'status': news['PlayerStatus'],
                'team': news['Team'],
                'title': news['Title'],
            }

    return fantasy_labs_news

# for all players playing in tomorrow's game we are going to get how they played in the preseason
with open('../scrape/json_files/team_schedules/'+YEAR+'/league_schedule.json',) as data_file:
    data = json.load(data_file)
    today_date = date.today()
    formatted_date = today_date.strftime("%a, %b %-d, %Y")

    all_teams = []
    opponents = {}
    fantasy_lab_news = get_fantasy_lab_news()

    for game in data[formatted_date]:

        all_teams.append(game['team'])
        all_teams.append(game['opp'])

        opponents[game['team']] = game['opp']
        opponents[game['opp']] = game['team']

    team_players = {}
    for (team, oppo) in opponents.iteritems():
        team_players[team] = []

        player_news = {}
        with open('../scrape/misc/news/'+team+'.json') as news_file:
            news = json.load(news_file)
            for player in news:

                if player in player_news.iteritems():
                    player_news[player['player']]['report'].append(player['report'])
                    player_news[player['player']]['news'].append(player['impact'])
                else:
                    if player['player'] in fantasy_lab_news:
                        report_list = [fantasy_lab_news[player['player']]['title'], player['report']]
                        news_list = [fantasy_lab_news[player['player']]['news'], player['impact']]
                    else:
                        report_list = [player['report']]
                        news_list = [player['impact']]

                    player_news[player['player']] = {
                        'report': report_list,
                        'news': news_list
                    }

            # player_news[fantasy_lab_news[player['player']]]['title']

        # pp.pprint(player_news)
        with open('../scrape/misc/depth_chart/'+team+'.json') as data_file:
            data = json.load(data_file)
            positions = ['PG', 'SG', 'SF', 'PF', 'C']
            for position in positions:
                depth = data[position]
                for player in depth:
                    team_players[team].append(player['player'])

            players = '","'.join(team_players[team])

            print '{team} vs {oppo}'.format(team=team, oppo=oppo)

            if oppo in TRANSLATE_DICT:
                oppo = TRANSLATE_DICT[oppo]

            player_against_team_logs = execute_query(sqlfetch.get_player_against_team_log(oppo, players))

            player_data = {}
            for game in player_against_team_logs:
                player_name = game['PLAYER_NAME']
                if player_name in player_data:
                    for param in game:
                        if param == 'MIN':
                            game['MIN'] = process_playtime(0, game['MIN']) / 60
                        player_data[player_name][param].append(game[param])
                else:
                    player_data[player_name] = {}
                    for param in game:
                        player_data[player_name][param] = []
                        if param == 'MIN':
                            game['MIN'] = process_playtime(0, game['MIN']) / 60
                        player_data[player_name][param].append(game[param])

            # if they are not in player_data but have news
            for player, param in player_data.iteritems():
                print '{player_name}: {num_games} Games'.format(player_name=player, num_games=len(param['DK_POINTS']))
                if player in player_news:
                    for report in player_news[player]['report']:
                        print report
                    for news in player_news[player]['news']:
                        print news
                # print '\n'
                print 'FP - Max: {max_dk}, Min: {min_dk}, Deviation: {dev}'.format(max_dk=np.max(param['DK_POINTS']), min_dk=np.min(param['DK_POINTS']), dev=np.std(param['DK_POINTS']))
                print 'MIN - Max: {max_min}, Min: {min_min}'.format(max_min=np.max(param['MIN']), min_min=np.min(param['MIN']))
                print 'FP/MIN - Max: {max_fpm}, Min: {min_fpm}, Deviation: {dev_fpm}'.format(max_fpm=np.max(param['FP_PER_MIN']), min_fpm=np.min(param['FP_PER_MIN']), dev_fpm=np.std(param['FP_PER_MIN']))
                print '\n'

            # if they are not in player_data but have news (ie Rookies)
            for player in player_news:
                if player not in player_data:
                    for report in player_news[player]['report']:
                        print report
                    for news in player_news[player]['news']:
                        print news


    # with open('../scrape/csv/'+str(today_date)+'.csv',) as csv_file:
    #     try:
    #         next(csv_file, None)
    #         players = csv.reader(csv_file)
    #         # for player in players:
    #             # print player[2]

        # except csv.Error as e:
            # sys.exit('file %s: %s' % (csv_file, e))
    # finalData['dkPlayers'] = {};
    #     var dataLength = data.length;
    #     for (var i=0; i<dataLength; i++) {
    #         var dataItem = data[i];
    #         // get the team name

    #         var team = common.translateDkDict()[dataItem[5]];
    #         var player = {
    #             name: dataItem[1],
    #             position: dataItem[0],
    #             salary: dataItem[2],
    #             appg: dataItem[4]
    #         }
    #         finalData['dkPlayers'][dataItem[1]] = player;
    #     }
    #     return finalData.dkPlayers;
    # players_string = '","'.join(player_playing_tonight)
    # print players_string
