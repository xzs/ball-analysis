# !/usr/bin/env python
# _*_ coding:utf-8 _*_

import MySQLdb
import pprint
import logging
import glob
import pandas as pd
import numpy as np
import sqlfetch
import nba_scrape_linear_regression
import news_scraper
import operator
import json
import csv
from datetime import date, timedelta, datetime

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
conv = MySQLdb.converters.conversions.copy()
conv[246] = float    # convert decimals to floats
conv[10] = str       # convert dates to strings

DATE_FORMAT_YEAR = str("%Y-%m-%d")
LAST_DATE_REG_SEASON = '2017-04-12'
FIRST_DATE_REG_SEASON = '2016-10-25'

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

def write_to_csv(sql_query, source, name):

    try:
        db = MySQLdb.connect("127.0.0.1","root","","nba_scrape", conv=conv)

        # prepare a cursor object using cursor() method
        cursor = db.cursor()
        # Execute the SQL command
        cursor.execute(sql_query)
        header = []
        for column in cursor.description:
            header.append(column[0])
        rows = cursor.fetchall()

        with open('nba_scrape/'+ source +'/'+ name +'.csv', 'wb') as f:
            myFile = csv.writer(f)
            # write to the header
            myFile.writerow(header)
            myFile.writerows(rows)

    except:
        print "Error: unable to fetch data"

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

DK_TEAMS = {
    'Hou' : 'HOU',
    'NO' : 'NOP',
    'OKC' : 'OKC',
    'SA' : 'SAS',
    'LAC' : 'LAC',
    'Mia' : 'MIA',
    'Det' : 'DET',
    'Ind' : 'IND',
    'Bos' : 'BOS',
    'Uta' : 'UTA',
    'NY' : 'NYK',
    'Dal' : 'DAL',
    'Mem' : 'MEM',
    'Bkn' : 'BRK',
    'Phi' : 'PHI',
    'Orl' : 'ORL',
    'Cle' : 'CLE',
    'Por' : 'POR',
    'Tor' : 'TOR',
    'Min' : 'MIN',
    'Chi' : 'CHI',
    'Cha' : 'CHO',
    'Atl' : 'ATL',
    'LAL' : 'LAL',
    'GS' : 'GSW',
    'Was' : 'WAS',
    'Mil' : 'MIL',
    'Sac' : 'SAV',
    'Pho' : 'PHO',
    'Den' : 'DEN'
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
    'BRK':'BKN',
    'PHO':'PHX',
}

WOWY_TEAMS = {
    'ATL':'Hawks',
    'BOS':'Celtics',
    'BRK':'Nets',
    'CHO':'Hornets',
    'CHI':'Bulls',
    'CLE':'Cavaliers',
    'DAL':'Mavericks',
    'DEN':'Nuggets',
    'DET':'Pistons',
    'GSW':'Warriors',
    'HOU':'Rockets',
    'IND':'Pacers',
    'LAC':'Clippers',
    'LAL':'Lakers',
    'MEM':'Grizzlies',
    'MIA':'Heat',
    'MIL':'Bucks',
    'MIN':'Timberwolves',
    'NOP':'Pelicans',
    'NYK':'Knicks',
    'OKC':'Thunder',
    'ORL':'Magic',
    'PHI':'76ers',
    'PHO':'Suns',
    'POR':'Trail Blazers',
    'SAC':'Kings',
    'SAS':'Spurs',
    'TOR':'Raptors',
    'UTA':'Jazz',
    'WAS':'Wizards'
}

POSITION_TRANSLATE_DICT = {
    1: 'PG',
    2: 'SG',
    3: 'SF',
    4: 'PF',
    5: 'C'
}

def get_daily_snapshot():
    # for all players playing in tomorrow's game we are going to get how they played in the preseason
    with open('../scrape/json_files/team_schedules/'+YEAR+'/league_schedule.json',) as data_file:
        data = json.load(data_file)
        # today_date = date.today()
        today_date = date.today() - timedelta(days=1)
        formatted_date = today_date.strftime("%a, %b %-d, %Y")

        opponents = {}
        fantasy_lab_news = news_scraper.get_fantasy_lab_news()
        # vegas_lines = news_scraper.get_vegas_lines(str(today_date))
        dk_money_obj = {}

        dk_teams_list = []
        with open('../scrape/csv/'+str(today_date)+'-Turbo.csv',) as csv_file:
            try:
                next(csv_file, None)
                players = csv.reader(csv_file)
                for player in players:
                    name = player[1]
                    dk_money_obj[name] = {
                        'positions': player[0].split('/'),
                        'salary': player[2],
                        'fp_avg': player[4],
                        'fp_needed': float(player[2])*0.001*6,
                        'avg_val': float(player[4])/(0.001*float(player[2]))
                    }
                    dk_team_abbrev = DK_TEAMS[player[5]]
                    if dk_team_abbrev not in dk_teams_list:
                        dk_teams_list.append(dk_team_abbrev)

            except csv.Error as e:
                sys.exit('file %s: %s' % (csv_file, e))

        for game in data[formatted_date]:

            if game['team'] in dk_teams_list:
                opponents[game['team']] = game['opp']
                opponents[game['opp']] = game['team']

        all_team_players = {}
        # all_players = []
        player_news = {}
        players_string = ''

        team_synergy_ranks = execute_query(sqlfetch.get_team_synergy_ranks(today_date))
        team_possessions_ranks = execute_query(sqlfetch.get_team_possessions_per_game(today_date))
        team_foul_ranks = execute_query(sqlfetch.get_team_fouls(FIRST_DATE_REG_SEASON))
        team_fga_ranks = execute_query(sqlfetch.get_team_fga_ranking(FIRST_DATE_REG_SEASON))
        team_reb_ranks = execute_query(sqlfetch.get_team_reb_ranking(FIRST_DATE_REG_SEASON))
        team_rating_ranks = execute_query(sqlfetch.get_team_ratings(FIRST_DATE_REG_SEASON))
        player_daily_status = news_scraper.player_daily_status()

        team_last_game_info_obj = {}
        for (team, oppo) in opponents.iteritems():
            all_team_players[team] = {
                'oppo': oppo,
                'players': {},
                'all_players': []
            }
            # reverse read the csv

            with open('../scrape/team_schedules/'+YEAR+'/'+team+'.csv', 'r') as outfile:
                for row in reversed(list(csv.reader(outfile))):
                    if row[6]:
                        # formate the time
                        last_game_date = datetime.strptime(row[0], '%a, %b %d, %Y')
                        last_game_date = last_game_date.strftime("%Y-%m-%d")

                        if row[4] == '':
                            row[4] = 'vs'

                        team_last_game_info_obj[team] = {
                            'date': last_game_date,
                            'location': row[4],
                            'oppo': row[5],
                            'result': row[6],
                            'score': row[8] + ' - ' + row[9],
                            'streak': row[12]
                        }
                        break

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

            with open('../scrape/misc/updated_depth_chart/'+team+'.json') as data_file:
                data = json.load(data_file)
                positions = ['PG', 'SG', 'SF', 'PF', 'C']
                for position in positions:
                    depth = data[position]
                    all_team_players[team]['players'][position] = {}
                    for player in depth:
                        player_name = player['player']
                        player_role = player['role']
                        # translate name appropriately for DK
                        if player_name in news_scraper.DEPTH_TO_DK_TRANSLATE:
                            player_name = news_scraper.DEPTH_TO_DK_TRANSLATE[player_name]

                        # all_team_players[team]['players'][position].append(player_name)
                        all_team_players[team]['players'][position][player_name] = {
                            'name': player_name,
                            'role': player_role
                        }
                        all_team_players[team]['all_players'].append(player_name)

                players_string = '","'.join(all_team_players[team])

        for team, team_players in all_team_players.iteritems():
            oppo = team_players['oppo']

            # last game
            """
                We can now fetch this from the DB
            """
            team_wowy_obj = news_scraper.player_on_off(WOWY_TEAMS[team], 'all', [], [], str(team_last_game_info_obj[team]['date']), str(team_last_game_info_obj[team]['date']))

            oppo_wowy_obj = news_scraper.player_on_off(WOWY_TEAMS[oppo], 'all', [], [], str(team_last_game_info_obj[oppo]['date']), str(team_last_game_info_obj[oppo]['date']))

            last_season_against_team = news_scraper.player_on_off(WOWY_TEAMS[team], [WOWY_TEAMS[oppo]], [], [], '2015-10-26' , str(today_date))

            print 'Team Last Game (Top 5 lineups)'
            print '({result}) ({streak}) {date} {location} {oppo} [{score}]'.format(
                result=team_last_game_info_obj[team]['result'], streak=team_last_game_info_obj[team]['streak'], date=team_last_game_info_obj[team]['date'],\
                location=team_last_game_info_obj[team]['location'], oppo=team_last_game_info_obj[team]['oppo'], score=team_last_game_info_obj[team]['score'])

            temp_lineup_obj = {}
            for lineup in team_wowy_obj['lineups'][0:5:1]:
                print ', '.join(lineup['lineup'])
                print 'Poss: {poss}'.format(poss=lineup['poss'])

            total_possessions = 0
            for lineup in team_wowy_obj['lineups']:
                total_possessions += lineup['poss']
                for idx, player in enumerate(lineup['lineup']):

                    # encode the name from wowy to bypass guys with accents
                    if player in news_scraper.WOWY_TO_DK_TRANSLATE:
                        player_name = news_scraper.WOWY_TO_DK_TRANSLATE[player]
                    else:
                        player_name = player
                    try:
                        player_lineup_position = POSITION_TRANSLATE_DICT[idx+1]

                        if player_name in temp_lineup_obj:
                            temp_player = temp_lineup_obj[player_name]
                            temp_player['num_lineups'] += 1
                            temp_player['poss'] += lineup['poss']
                            temp_player['min'] += lineup['min']

                            # check for additional positions played
                            if player_lineup_position in temp_player['positions']:
                                temp_player['positions'][player_lineup_position] += lineup['poss']
                            else:
                                temp_player['positions'][player_lineup_position] = lineup['poss']
                        else:
                            temp_lineup_obj[player_name] = {
                                'poss': lineup['poss'],
                                'num_lineups': 1,
                                'min': lineup['min'],
                                'positions': {
                                   player_lineup_position: lineup['poss']
                                }
                            }
                    except KeyError:
                        print 'Out of range'

            print '\n'

            # opponent
            print 'Opponent Last Game (Top 5 lineups)'
            print '({result}) ({streak}) {date} {location} {oppo} [{score}]'.format(
                result=team_last_game_info_obj[oppo]['result'], streak=team_last_game_info_obj[oppo]['streak'], date=team_last_game_info_obj[oppo]['date'],\
                location=team_last_game_info_obj[oppo]['location'], oppo=team_last_game_info_obj[oppo]['oppo'], score=team_last_game_info_obj[oppo]['score'])

            for oppo_lineup in oppo_wowy_obj['lineups'][0:5:1]:
                print ', '.join(oppo_lineup['lineup'])
                print 'Poss: {poss}'.format(poss=oppo_lineup['poss'])


            # print '\n'
            # print 'Last Game Lineup Summary (>= 20 poss):'

            # sorted_temp_lineup_obj = sorted(temp_lineup_obj, key=lambda x: (temp_lineup_obj[x]['poss'], temp_lineup_obj[x]['num_lineups']), reverse=True)
            # for player in sorted_temp_lineup_obj:
            #     player_name = player.encode('ascii', 'ignore')
            #     player_obj = temp_lineup_obj[player]
                # if player_obj['poss'] >= 20:
                    # print '{player} Poss: {poss}'.format(player=player_name, poss=player_obj['poss'])

                    # for positon, poss in player_obj['positions'].iteritems():
                    #     poss_pct = float(poss)/float(player_obj['poss'])*100
                    #     print '{positions}: {poss}%'.format(positions=positon, poss=news_scraper.two_decimals(poss_pct))

            print '\n'
            print 'From Last Season vs ' + oppo
            # sort by usg first, then remainder by poss
            sorted_usg_list = sorted(last_season_against_team['players'], key=lambda x: (last_season_against_team['players'][x]['complied_stats']['usg']), reverse=True)
            for player in sorted_usg_list:
                player_name = player.encode("utf-8")
                player_obj = last_season_against_team['players'][player]

                if player_obj['poss'] >= 20:
                    if player in all_team_players[team]['all_players']:
                        print '{player}, POSS: {poss}, USG: {usg}, SI: {si}'.format(
                            player=player_name, poss=player_obj['poss'], usg=player_obj['complied_stats']['usg'],\
                            si=player_obj['complied_stats']['scoring_index'])

            print '\n'

            if oppo in TRANSLATE_DICT:
                oppo = TRANSLATE_DICT[oppo]

            if team in TRANSLATE_DICT:
                team = TRANSLATE_DICT[team]

            team_possession_rank = (item for item in team_possessions_ranks \
                if item["TEAM_ABBREVIATION"] == team).next()
            oppo_possession_rank = (item for item in team_possessions_ranks \
                if item["TEAM_ABBREVIATION"] == oppo).next()
            oppo_foul_rank = (item for item in team_foul_ranks \
                if item["TEAM"] == oppo).next()
            oppo_fga_rank = (item for item in team_fga_ranks \
                if item["TEAM"] == oppo).next()
            oppo_reb_rank = (item for item in team_reb_ranks \
                if item["TEAM"] == oppo).next()
            oppo_rating_rank = (item for item in team_rating_ranks \
                if item["TEAM"] == oppo).next()
            oppo_synergy_rank = (item for item in team_synergy_ranks \
                if item["TEAM_NAME"] == oppo).next()

            print '{team}: {team_poss} ({team_poss_rank}) vs {oppo}: {oppo_poss} ({oppo_poss_rank})'.format(
                    team=team, oppo=oppo, team_poss=team_possession_rank['AVG_NUM_POSS'], \
                    team_poss_rank=team_possession_rank['POSSG_RANK'], \
                    oppo_poss=oppo_possession_rank['AVG_NUM_POSS'], \
                    oppo_poss_rank=oppo_possession_rank['POSSG_RANK'])

            if team == 'BKN':
                vegas_team = 'BK'
            elif team == 'PHX':
                vegas_team = 'PHO'
            elif team == 'CHA':
                vegas_team = 'CHO'
            else:
                vegas_team = team

            # print 'Spread: ' + vegas_lines[vegas_team]['advantage_team'], vegas_lines[vegas_team]['over_under']

            # fouls
            print '{oppo} Fouls: {fouls} ({fouls_rank})'.format(
                    oppo=oppo, fouls=oppo_foul_rank['AVG_FOULS'], \
                    fouls_rank=team_foul_ranks.index(oppo_foul_rank))
            # fga
            print '{oppo} FGA: {fga} ({fga_rank})'.format(
                    oppo=oppo, fga=oppo_fga_rank['AVG_FGA'], \
                    fga_rank=team_fga_ranks.index(oppo_fga_rank))

            # reb
            print '{oppo} REB: {reb} ({reb_rank})'.format(
                    oppo=oppo, reb=oppo_reb_rank['AVG_REB'], \
                    reb_rank=team_reb_ranks.index(oppo_reb_rank))

            # rating
            print '{oppo} Def. Rating: {rating} ({rating_rank})'.format(
                    oppo=oppo, rating=oppo_rating_rank['AVG_DEF_RATING'], \
                    rating_rank=team_rating_ranks.index(oppo_rating_rank))

            print oppo + ' Synergy Ranks'
            print 'PnR Handler: {roll_rank}, PnR Roller: {handler_rank}, SpotUp Shots: {spotup_rank}, ISO: {iso_rank}'.format(
                roll_rank=oppo_synergy_rank['PR_ROLL_RANK'], \
                handler_rank=oppo_synergy_rank['PR_HANDLER_RANK'], \
                spotup_rank=oppo_synergy_rank['SPOTUP_RANK'], \
                iso_rank=oppo_synergy_rank['ISO_RANK'])

            print '{oppo} DvP:'.format(oppo=oppo)
            if oppo == 'BKN':
                oppo = 'BRK'
            elif oppo == 'PHX':
                oppo = 'PHO'
            elif oppo == 'CHA':
                oppo = 'CHO'

            oppo_dvp_obj = {}
            with open('../scrape/misc/fantasy_stats/'+oppo+'.json') as data_file:
                data = json.load(data_file)
                positions = ['G', 'F', 'C']
                for position in positions:
                    fp_against = data[position]
                    oppo_dvp_obj[position] = data[position]

                    print '{position}: {season} ({rank})'.format(
                            position=position, \
                            season=fp_against['Season'], \
                            rank=fp_against['rank'])

            print '\n'

            # all_team_players[team]['players'][position][player_name] = {
            #     'name': player_name,
            #     'role': player_role
            # }

            for position, position_players in team_players['players'].iteritems():
                print position
                for lineup_player, player_info in position_players.iteritems():
                    player = player_info['name']
                    player_role = player_info['role']
                    # set default status
                    player_status = 'Active'

                    if player in dk_money_obj:
                        player_salary = dk_money_obj[player]['salary']
                        fp_needed = dk_money_obj[player]['fp_needed']
                        avg_val = dk_money_obj[player]['avg_val']
                        fp_avg = dk_money_obj[player]['fp_avg']

                        if player in player_daily_status['today'] or player in player_daily_status['all']:
                            if player in player_daily_status['today']:
                                player_status = player_daily_status['today'][player]
                            if player in player_daily_status['all']:
                                player_status = player_daily_status['all'][player]


                            print player + ' Status: ' + player_status

                            # if players are off the same role
                            # we can try to grup them together and send it to the API
                            # see what lineups were played when they are out (by poss)
                            if (player_status == 'Questionable' or \
                                player_status == 'Out' or \
                                player_status == 'Doubtful' or \
                                player_status == 'Injured') \
                                and fp_avg > 0:

                                wow_team = team
                                if team == 'BKN':
                                    wow_team = 'BRK'
                                elif team == 'PHX':
                                    wow_team = 'PHO'
                                elif team == 'CHA':
                                    wow_team = 'CHO'

                                if player in news_scraper.DK_TO_WOWY_TRANSLATE:
                                    wowy_player = news_scraper.DK_TO_WOWY_TRANSLATE[player]
                                else:
                                    wowy_player = player

                                player_off_obj = news_scraper.player_on_off(WOWY_TEAMS[wow_team], 'all', [], [wowy_player], FIRST_DATE_REG_SEASON, str(today_date))

                                sorted_usg_list = sorted(player_off_obj['players'], key=lambda x: (player_off_obj['players'][x]['complied_stats']['usg']), reverse=True)
                                for other_player in sorted_usg_list:
                                    other_player_name = other_player.encode('ascii', 'ignore')
                                    player_off_wowy_obj = player_off_obj['players'][other_player]

                                    if player_off_wowy_obj['poss'] >= 20:
                                        split_name = other_player_name.split('.')
                                        if len(split_name) > 1:
                                            split_other_player_name = "".join(split_name)
                                        else:
                                            split_name = other_player_name


                                        # something wrong here with teh name
                                        # if split_name in news_scraper.WOWY_TO_DK_TRANSLATE:
                                        #     split_name = news_scraper.WOWY_TO_DK_TRANSLATE[split_name]
                                        #     if split_name in news_scraper.DK_TO_SQL_TRANSLATE:
                                        #         split_name = news_scraper.DK_TO_SQL_TRANSLATE[split_name]

                                        # there needs to be a translate here
                                        player_avg_usg = execute_query(sqlfetch.get_player_avg_usg(FIRST_DATE_REG_SEASON, today_date, split_name))
                                        if player_off_wowy_obj['complied_stats']['usg'] >= player_avg_usg[0]['AVG_USG'] and \
                                            player_off_wowy_obj['complied_stats']['usg'] >= 20:

                                            if player in all_team_players[wow_team]['all_players']:
                                                print '{player}, POSS: {poss}, USG: {usg}, SI: {si}'.format(
                                                    player=other_player_name, poss=player_off_wowy_obj['poss'], usg=player_off_wowy_obj['complied_stats']['usg'],\
                                                    si=player_off_wowy_obj['complied_stats']['scoring_index'])

                                print '\n'


                        # if player_status != 'Out':
                        if player in news_scraper.DK_TO_SQL_TRANSLATE:
                            sql_player = news_scraper.DK_TO_SQL_TRANSLATE[player]
                        else:
                            sql_player = player

                        if 'SG' in dk_money_obj[player]['positions'] or \
                            'PG' in dk_money_obj[player]['positions']:
                            dvp_against_player = oppo_dvp_obj['G']
                        elif 'SF' in dk_money_obj[player]['positions'] or \
                            'PF' in dk_money_obj[player]['positions']:
                            dvp_against_player = oppo_dvp_obj['F']
                        else:
                            dvp_against_player = oppo_dvp_obj['C']

                        player_games_log = sqlfetch.execute_query(sqlfetch.get_player_dk_points_log(sql_player, FIRST_DATE_REG_SEASON))
                        num_games_played = len(player_games_log)

                        get_player_avg_min = sqlfetch.execute_query(sqlfetch.get_played_avg_min(sql_player, FIRST_DATE_REG_SEASON))
                        try:
                            played_avg_min = get_player_avg_min[0]['AVG_MIN']
                        except IndexError:
                            played_avg_min = 0

                        print '{player_name} ({player_role}) ({num_games_played}G) ({played_avg_min}M) {position}: {salary}, AVG PTS: {fp_avg}, '\
                                'OPPO DvP: {dvp_against_player} ({dvp_against_player_rank}), '\
                                'VAL: {avg_val}, PTS NEEDED: {fp_needed}'.format(
                                    player_name=player, position=dk_money_obj[player]['positions'], \
                                    player_role=player_role, num_games_played=num_games_played, \
                                    salary=player_salary, dvp_against_player=dvp_against_player['Season'], \
                                    dvp_against_player_rank=dvp_against_player['rank'], fp_avg=fp_avg, \
                                    avg_val=news_scraper.two_decimals(avg_val), fp_needed=fp_needed, played_avg_min=played_avg_min)

                        # have the player ever reached this value? (%)
                        # num games played
                        # how recent were these (what was the latest date?)

                        dk_points_query = sqlfetch.get_player_dk_points_log(sql_player, FIRST_DATE_REG_SEASON) + \
                            'AND tb.FG3M*0.5+tb.REB*1.25+tb.AST*1.25+tb.STL*2+tb.BLK*2+tb.TO*-0.5+tb.PTS*1 >= {fp_needed} '\
                            'ORDER BY DATE'.format(fp_needed=fp_needed)
                        have_reached_value = sqlfetch.execute_query(dk_points_query)
                        num_times_reached_value = len(have_reached_value)

                        if num_times_reached_value >= 1:
                            reached_value_pct = (float(num_times_reached_value) / float(num_games_played)) * 100
                            print 'Reached 6xV {num_times}x ({reached_value_pct}%)'.format(
                                num_times=num_times_reached_value, reached_value_pct=news_scraper.two_decimals(reached_value_pct)
                            )
                        # if not what are the chances that he will
                        news_scraper.test_markov(sql_player)


                        # player matchups
                        if player in news_scraper.DK_TO_WOWY_TRANSLATE:
                            wowy_player = news_scraper.DK_TO_WOWY_TRANSLATE[player]
                        else:
                            wowy_player = player

                        # based on last game's positions
                        player_matchups_list = []
                        if wowy_player in temp_lineup_obj:
                            player_obj = temp_lineup_obj[wowy_player]
                            for player_obj_positon, poss in player_obj['positions'].iteritems():
                                try:
                                    poss_pct = float(poss)/float(player_obj['poss'])*100
                                except ZeroDivisionError:
                                    poss_pct = 0

                                if poss_pct >= 20:
                                    player_matchups_list = player_matchups_list + all_team_players[oppo]['players'][player_obj_positon].keys()
                        else:
                            # based on the natural positions
                            # this can be based on the avg positions
                            for position in dk_money_obj[player]['positions']:
                                player_matchups_list = player_matchups_list + all_team_players[oppo]['players'][position].keys()

                        player_matchups_string = ', '.join(player_matchups_list)

                        print 'Potential Matchups: %s' % player_matchups_string

                        # name things
                        split_name = player.split('.')
                        news_player = ''
                        if len(split_name) > 1:
                            news_player = "".join(split_name)

                        if news_player in player_news:
                            for report in player_news[news_player]['report']:
                                if report:
                                    print report.strip()
                            for news in player_news[news_player]['news']:
                                if news:
                                    print news.strip()

                        if oppo == 'BRK':
                            sql_oppo = 'BKN'
                        elif oppo == 'PHO':
                            sql_oppo = 'PHX'
                        elif oppo == 'CHO':
                            sql_oppo = 'CHA'
                        else:
                            sql_oppo = oppo

                        # # write to player log
                        # player_log = sqlfetch.full_player_log(player, FIRST_DATE_REG_SEASON, today_date, 0, 0)
                        # full_player_log = execute_query(player_log)
                        # write_to_csv(player_log, 'player_logs', player)

                        # # calc simple regression
                        # simple_lr_data = nba_scrape_linear_regression.get_simple_player_log_regression(player)

                        # print simple_lr_data

                        # if player in news_scraper.DK_TO_SQL_TRANSLATE:
                        #     sql_player = news_scraper.DK_TO_SQL_TRANSLATE[player]
                        # else:
                        #     sql_player = player


                        if player in player_daily_status['today'] or player in player_daily_status['all']:
                            if player in player_daily_status['today']:
                                player_status = player_daily_status['today'][player]
                            if player in player_daily_status['all']:
                                player_status = player_daily_status['all'][player]

                            if (player_status == 'Questionable' or \
                                player_status == 'Out' or \
                                player_status == 'Doubtful' or \
                                player_status == 'Injured') \
                                and fp_avg > 0:

                                sql_positions = {
                                    'PG': 'player_1',
                                    'SG': 'player_2',
                                    'SF': 'player_3',
                                    'PF': 'player_4',
                                    'C': 'player_5'
                                }

                                # fetch games missed
                                player_off_lineup = sqlfetch.execute_query(sqlfetch.get_games_not_played_by_player(team, sql_player, FIRST_DATE_REG_SEASON))

                                if len(player_off_lineup) >= 1:
                                    temp_player_replace_obj = {}
                                    for position in dk_money_obj[player]['positions']:
                                        print position
                                        player_off_lineup = sqlfetch.execute_query(sqlfetch.get_player_lineup_stats_from_absence(team, sql_player, sql_positions[position], FIRST_DATE_REG_SEASON))
                                        for replace_player in player_off_lineup:
                                            if replace_player['PLAYER_NAME'] not in temp_player_replace_obj:
                                                temp_player_replace_obj[replace_player['PLAYER_NAME']] = {
                                                    'min': replace_player['TOTAL_MIN_PLAYED'],
                                                    'poss': replace_player['TOTAL_POSS_PLAYED']
                                                }
                                            else:
                                                temp_player_replace_obj[replace_player['PLAYER_NAME']]['min'] += replace_player['TOTAL_MIN_PLAYED']
                                                temp_player_replace_obj[replace_player['PLAYER_NAME']]['poss'] += replace_player['TOTAL_POSS_PLAYED']
                                            # print replace_player['PLAYER_NAME'], replace_player['TOTAL_MIN_PLAYED'], replace_player['TOTAL_POSS_PLAYED']

                                    for replace_player_name, replace_player_info in temp_player_replace_obj.iteritems():
                                        print '{player_name}, MIN: {min} POSS: {poss}'.format(
                                            player_name=replace_player_name, min=replace_player_info['min'], poss=replace_player_info['poss']
                                        )

                        # print player_off_obj
                        # SQL stuff
                        player_pfd = execute_query(sqlfetch.get_player_pfd(FIRST_DATE_REG_SEASON, sql_player))

                        player_pf = execute_query(sqlfetch.get_player_pf(FIRST_DATE_REG_SEASON, sql_player))
                        print 'PFD: {pfd}, PF: {pf}'.format(pfd=player_pfd[0]['AVG_PFD'], pf=player_pf[0]['AVG_PF'])

                        player_against_team_logs = execute_query(sqlfetch.get_player_against_team_log(sql_oppo, sql_player))

                        # since the dict is already translated
                        wowy_player = ''
                        if player in news_scraper.DK_TO_WOWY_TRANSLATE:
                            wowy_player = news_scraper.DK_TO_WOWY_TRANSLATE[player]
                        else:
                            wowy_player = player

                        # print temp_lineup_obj
                        played_last_game = ''
                        if wowy_player in temp_lineup_obj:
                            player_obj = temp_lineup_obj[wowy_player]
                            total_poss_pct = float(player_obj['poss'])/float(total_possessions)*100
                        else:
                            played_last_game = 'DNP'
                            print played_last_game

                        if played_last_game != 'DNP':
                            player_last_game = execute_query(sqlfetch.player_last_game(sql_player, 1, False))

                            # i should probably also try to fetch the last game for the player so i can get # of plays
                            # fga + (0.5 * fta) + stats['tov'] + stats['ast']
                            try:
                                if played_last_game != 'DNP':
                                    last_game = player_last_game[0]
                                    players_plays = last_game['FGA'] + (0.5 * last_game['FTA']) + last_game['TO'] + last_game['AST']
                                    print 'Last Game'
                                    print '{date} vs {team} Min: {min}, Usage: {usg}, FP: {dk}'.format(
                                        date=last_game['DATE'], team=last_game['TEAM_AGAINST'], \
                                        min=last_game['MIN'], usg=last_game['USG_PCT'], \
                                        dk=last_game['DK_POINTS'])
                                    print 'Possessions Played: {poss_played} ({total_poss_pct}%) - {plays} Plays'.format(
                                        poss_played=player_obj['poss'], total_poss_pct=news_scraper.two_decimals(total_poss_pct), plays=players_plays)
                                    for positon, poss in player_obj['positions'].iteritems():
                                        try:
                                            poss_pct = float(poss)/float(player_obj['poss'])*100
                                        except ZeroDivisionError:
                                            poss_pct = 0
                                        print '{positions}: {poss}%'.format(positions=positon, poss=news_scraper.two_decimals(poss_pct))
                            except IndexError:
                                print 'Out of range'


                        player_data = {}
                        if len(player_against_team_logs) >= 1:
                            usg_list = []
                            dk_list = []
                            min_list = []
                            fp_min_list = []
                            for game in player_against_team_logs:
                                usg_list.append(game['USG_PCT'])
                                dk_list.append(game['DK_POINTS'])
                                fp_min_list.append(game['FP_PER_MIN'])

                                player_name = game['PLAYER_NAME']
                                if player_name in player_data:
                                    for param in game:
                                        if param == 'MIN':
                                            game['MIN'] = process_playtime(0, game['MIN']) / 60
                                            min_list.append(game['MIN'])
                                else:
                                    player_data[player_name] = {}
                                    for param in game:
                                        player_data[player_name][param] = []
                                        if param == 'MIN':
                                            game['MIN'] = process_playtime(0, game['MIN']) / 60
                                            min_list.append(game['MIN'])

                            print 'Last Time Against: {oppo}, {num_games} Games'.format(oppo=oppo, num_games=len(player_against_team_logs))
                            print 'USG - Max: {max_usg}, Min: {min_usg}'.format(max_usg=np.max(usg_list), min_usg=np.min(usg_list))
                            print 'FP - Max: {max_dk}, Min: {min_dk}'.format(max_dk=np.max(dk_list), min_dk=np.min(dk_list))
                            print 'MIN - Max: {max_min}, Min: {min_min}'.format(max_min=np.max(min_list), min_min=np.min(min_list))
                            print 'FP/MIN - Max: {max_fpm}, Min: {min_fpm}'.format(max_fpm=np.max(fp_min_list), min_fpm=np.min(fp_min_list))
                        print '\n'

get_daily_snapshot()
