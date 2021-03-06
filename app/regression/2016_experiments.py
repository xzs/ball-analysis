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
today_date = date.today()
LAST_DATE_REG_SEASON = str(today_date)
FIRST_DATE_REG_SEASON = '2017-09-30'


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
            'avg(tb.FG3M*0.5 + tb.REB*1.25 + tb.AST*1.50 + tb.STL*2 + tb.BLK*2 + tb.TO*-0.5 + tb.PTS*1) as dk_points '\
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
    # print sqlfetch.get_team_synergy_ranks()

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
    'HOU' : 'HOU',
    'NO' : 'NOP',
    'OKC' : 'OKC',
    'SA' : 'SAS',
    'LAC' : 'LAC',
    'Mia' : 'MIA',
    'Det' : 'DET',
    'Ind' : 'IND',
    'BOS' : 'BOS',
    'Uta' : 'UTA',
    'NY' : 'NYK',
    'Dal' : 'DAL',
    'Mem' : 'MEM',
    'Bkn' : 'BRK',
    'Phi' : 'PHI',
    'Orl' : 'ORL',
    'CLE' : 'CLE',
    'Por' : 'POR',
    'TOR' : 'TOR',
    'Min' : 'MIN',
    'Chi' : 'CHI',
    'Cha' : 'CHO',
    'Atl' : 'ATL',
    'LAL' : 'LAL',
    'GS' : 'GSW',
    'Was' : 'WAS',
    'Mil' : 'MIL',
    'Sac' : 'SAC',
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


# PLAYER_IDS = execute_query(sqlfetch.get_player_names())
# PLAYER_OBJ = {}
# for player in PLAYER_IDS:
#     PLAYER_OBJ[player['PLAYER_ID']] = player['PLAYER_NAME']

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

PLAYER_DAILY_STATUS = news_scraper.player_daily_status()
OUT_PLAYERS = []
TEAMS_PLAYING = {}
ALL_TEAM_PLAYERS = {}
def get_team_depth_chart(team):
    ALL_TEAM_PLAYERS[team] = {
        'players': {},
        'all_players': []
    }
    with open('../scrape/misc/updated_depth_chart/'+team+'.json') as data_file:
        data = json.load(data_file)
        positions = ['PG', 'SG', 'SF', 'PF', 'C']
        for position in positions:
            depth = data[position]
            ALL_TEAM_PLAYERS[team]['players'][position] = {}
            for player in depth:
                player_name = player['player']
                player_role = player['role']
                # translate name appropriately for DK
                if player_name in news_scraper.DEPTH_TO_DK_TRANSLATE:
                    player_name = news_scraper.DEPTH_TO_DK_TRANSLATE[player_name]

                # ALL_TEAM_PLAYERS[team]['players'][position].append(player_name)
                ALL_TEAM_PLAYERS[team]['players'][position][player_name] = {
                    'name': player_name,
                    'role': player_role
                }
                ALL_TEAM_PLAYERS[team]['all_players'].append(player_name)

    return ALL_TEAM_PLAYERS

def get_player_daily_status(out_players, player_name, player_role):

    # basketball monster use sql names
    if player_name in PLAYER_DAILY_STATUS['today'] or player_name in PLAYER_DAILY_STATUS['all']:

        if player_name in PLAYER_DAILY_STATUS['today']:
            player_status = PLAYER_DAILY_STATUS['today'][player_name]
        if player_name in PLAYER_DAILY_STATUS['all']:
            player_status = PLAYER_DAILY_STATUS['all'][player_name]
        
        # if the player is not playing
        # check status of depth chart
        if player_role == 'Lim PT' and player_status != 'Playing' and player_status != 'Probable':
            out_players.append(player_name)

        # if players are off the same role
        # we can try to grup them together and send it to the API
        # see what lineups were played when they are out (by poss)
        if (player_status == 'Questionable' or \
            player_status == 'Out' or \
            player_status == 'Doubtful' or \
            player_status == 'Injured'):

            # or if they are not on the roster anymore
            out_players.append(player_name)

def get_possible_lineups(team, oppo):
    today_date = date.today()
    possible_lineups = sqlfetch.execute_query(sqlfetch.get_lineup_from_absence(OUT_PLAYERS, team, 15))

    usg_line_up_summary = {}
    usg_line_up_summary[team] = {}

    last_usg_line_up_summary = {}
    last_usg_line_up_summary[team] = {}

    sql_team = team
    if team in TRANSLATE_DICT:
        sql_team = TRANSLATE_DICT[team]
    if team == 'BKN':
        wowy_team = 'BRK'
        fantasy_team = 'BRK'
    elif team == 'PHX':
        wowy_team = 'PHO'
        fantasy_team = 'PHO'
    elif team == 'CHA':
        wowy_team = 'CHO'
        fantasy_team = 'CHO'
    wowy_team = team
    # call nba_wowy

    player_summary_object = {}
    lineup_summary_object = {}

    last_player_summary_object = {}
    last_lineup_summary_object = {}

    get_team_depth_chart(team)

    # on avg how mnay possessions does the player play per game
    # in the lineups he play what is his usg + reb + stl stats


    # how many possessions did the player play against the opponent last season...
    # overall stats
    last_season_against_team = news_scraper.player_on_off(WOWY_TEAMS[team], [WOWY_TEAMS[oppo]], [], [], '2016-10-26' , str(today_date))
    for (last_usg_player, last_usg_player_stats) in last_season_against_team['players'].iteritems():

        usg = str(last_usg_player_stats['compiled_stats']['usg'])
        dkm = str(last_usg_player_stats['compiled_stats']['dkm'])

        # create the obj for players usg & dkm for each lineups
        if last_usg_player not in last_player_summary_object \
            and last_usg_player in ALL_TEAM_PLAYERS[team]['all_players']:
            last_player_summary_object[last_usg_player] = {
                'usg': usg,
                'dkm': dkm,
                'min': last_usg_player_stats['min']
            }

    pp.pprint(last_player_summary_object)
    for idx, possible_lineup in enumerate(possible_lineups):
        # print possible_lineup
        key_list = ['PLAYER_1', 'PLAYER_2', 'PLAYER_3', 'PLAYER_4', 'PLAYER_5']
        on_players = []

        for key_marker in key_list:
            if possible_lineup[key_marker] in news_scraper.SQL_TO_WOWY_TRANSLATE:
                on_players.append(news_scraper.SQL_TO_WOWY_TRANSLATE[possible_lineup[key_marker]])
            else:
                on_players.append(possible_lineup[key_marker])

        # in general for all opponents
        player_on_obj = news_scraper.player_on_off(WOWY_TEAMS[wowy_team], 'all', on_players, [], FIRST_DATE_REG_SEASON, str(today_date))

        if len(player_on_obj['lineups']) > 0:

            sorted_on_players = sorted(on_players)
            on_players_str = ', '.join(sorted_on_players)

            lineup_summary_object[on_players_str] = {}

            for usg_player in on_players:
                usg = str(player_on_obj['players'][usg_player]['compiled_stats']['usg'])
                dkm = str(player_on_obj['players'][usg_player]['compiled_stats']['dkm'])

                # create the obj for players usg & dkm for each lineups
                if usg_player not in player_summary_object:
                    player_summary_object[usg_player] = {
                        'usg': {},
                        'dkm': {}
                    }

                # instead of by player this is by lineup
                if usg_player not in lineup_summary_object[on_players_str]:
                    lineup_summary_object[on_players_str][usg_player] = {
                        'usg': player_on_obj['players'][usg_player]['compiled_stats']['usg'],
                        'dkm': player_on_obj['players'][usg_player]['compiled_stats']['dkm']
                    }

                player_summary_object[usg_player]['usg'][usg] = sorted_on_players
                player_summary_object[usg_player]['dkm'][dkm] = sorted_on_players

                if usg_player in usg_line_up_summary[team]:
                    for stat_keys in ['usg', 'dkm']:
                        usg_line_up_summary[team][usg_player][stat_keys].append(player_on_obj['players'][usg_player]['compiled_stats'][stat_keys])
                else:
                    usg_line_up_summary[team][usg_player] = {
                        'usg': [player_on_obj['players'][usg_player]['compiled_stats']['usg']],
                        'dkm': [player_on_obj['players'][usg_player]['compiled_stats']['dkm']]
                    }

    # for (lineup_player, stats) in usg_line_up_summary[team].iteritems():

    #     print '{player} USG: {usg}'.format(player=lineup_player, usg=np.max(stats['usg']))
    #     print player_summary_object[lineup_player]['usg'][str(np.max(stats['usg']))]
    #     print '{player} DKM: {dkm}'.format(player=lineup_player, dkm=np.max(stats['dkm']))
    #     print player_summary_object[lineup_player]['dkm'][str(np.max(stats['dkm']))]
    
    #     print '\n'


    # simple forecast based on the last game played?
    # we have to account for you especially if you played possessions last game

    team_last_game_lineup = sqlfetch.execute_query(sqlfetch.get_last_game_lineup(sql_team, FIRST_DATE_REG_SEASON))
    estimate_dk_object = {}
    for last_game_lineup in team_last_game_lineup:
        player_position_keys = ['PLAYER_1', 'PLAYER_2', 'PLAYER_3', 'PLAYER_4', 'PLAYER_5']

        for position_key in player_position_keys:
            # make the wowy name
            if last_game_lineup[position_key] in news_scraper.SQL_TO_WOWY_TRANSLATE:
                last_game_lineup[position_key] = news_scraper.SQL_TO_WOWY_TRANSLATE[last_game_lineup[position_key]]

            # sql name & wowy name

        player_lineup = sorted([last_game_lineup['PLAYER_1'], last_game_lineup['PLAYER_2'], last_game_lineup['PLAYER_3'], last_game_lineup['PLAYER_4'], last_game_lineup['PLAYER_5']])
        player_lineup_str = ', '.join(player_lineup)

        # what if the lineup is a new combination?
        if player_lineup_str in lineup_summary_object:
            # based on common lineup plays and minutes played last game
            for (player, f_stats) in lineup_summary_object[player_lineup_str].iteritems():
                if player not in estimate_dk_object:
                    estimate_dk_object[player] = f_stats['dkm'] * last_game_lineup['MINUTES_PLAYED']
                else:
                    estimate_dk_object[player] += f_stats['dkm'] * last_game_lineup['MINUTES_PLAYED']

    pp.pprint(estimate_dk_object)


    # estimate based on the different line ups and possible minutes (from last game)



    # return temp_player_lineup_usg

# get_possible_lineups('CLE', 'BOS')


def get_dk_money_obj(today_date):
    dk_money_obj = {}
    dk_positions_dict = {
        'PG': [],
        'SG': [],
        'SF': [],
        'PF': [],
        'C': []

    }
    value_games_min = {}
    position_cost_metrics = {}
    greater_than_value_players = []

    with open('../scrape/csv/'+str(today_date)+'.csv',) as csv_file:
        try:
            next(csv_file, None)
            players = csv.reader(csv_file)
            for player in players:
                name = player[1]
                positions = player[0].split('/')
                avg_val = float(player[4])/(0.001*float(player[2]))
                fp_needed = float(player[2])*0.001*6
                dk_money_obj[name] = {
                    'positions': positions,
                    'salary': player[2],
                    'fp_avg': player[4],
                    'fp_needed': float(player[2])*0.001*6,
                    'avg_val': avg_val
                }

                away_team = DK_TEAMS[player[3].split("@")[0]]
                home_team = DK_TEAMS[player[3].split("@")[1].split(" ")[0]]
                player_team = DK_TEAMS[player[5]]

                if player_team == home_team:
                    player_opp = away_team
                else:
                    player_opp = home_team

                if player_team not in TEAMS_PLAYING:
                    TEAMS_PLAYING[player_team] = player_opp

                # add them to the position dict
                for position in positions:
                    dk_positions_dict[position].append(float(avg_val))


                if name in news_scraper.DK_TO_SQL_TRANSLATE:
                    sql_player = news_scraper.DK_TO_SQL_TRANSLATE[name]
                else:
                    sql_player = name
                
                try:
                    player_role = sqlfetch.execute_query(sqlfetch.get_player_roles_by_name(sql_player))[0]['ROLE']                
                except IndexError:
                    # print 'Player is wavied / out'
                    OUT_PLAYERS.append(sql_player)

                get_player_daily_status(OUT_PLAYERS, sql_player, player_role)

            for (position, val) in dk_positions_dict.iteritems():
                
                position_cost_metrics[position] = {
                    'min': np.min(val),
                    'max': np.max(val),
                    'average': np.average(val),
                    'median': np.median(val)
                }

                # # have the player ever reached this value? (%)
                # if name in news_scraper.DK_TO_SQL_TRANSLATE:
                #     sql_player = news_scraper.DK_TO_SQL_TRANSLATE[name]
                # else:
                #     sql_player = name

                # dk_points_query = sqlfetch.get_player_dk_points_log(sql_player, FIRST_DATE_REG_SEASON) + \
                #     'AND tb.FG3M*0.5+tb.REB*1.25+tb.AST*1.50+tb.STL*2+tb.BLK*2+tb.TO*-0.5+tb.PTS*1 >= {fp_needed} '\
                #     'ORDER BY DATE'.format(fp_needed=fp_needed)

                # have_reached_value = sqlfetch.execute_query(dk_points_query)
                # num_times_reached_value = len(have_reached_value)

                # value_games_game_id = []
                # value_games_min[name] = {
                #     'min': []
                # }
                # for reached_value_games in have_reached_value:
                #     # need to explore these games
                #     value_games_game_id.append(reached_value_games['GAME_ID'])
                #     playtime_string = reached_value_games['MIN'].split(':')
                #     if len(playtime_string) > 1:
                #         playtime_in_seconds = int(playtime_string[0])*60 + int(playtime_string[1])
                #         value_games_min[name]['min'].append(playtime_in_seconds)

                # player_games_log = sqlfetch.execute_query(sqlfetch.get_player_dk_points_log(name, FIRST_DATE_REG_SEASON))
                # num_games_played = len(player_games_log)

                # if num_times_reached_value >= 1 and num_games_played >= 1:
                #     reached_value_pct = (float(num_times_reached_value) / float(num_games_played)) * 100
                #     print name
                #     print 'Reached V {num_times}x ({reached_value_pct}%)'.format(
                #         num_times=num_times_reached_value, reached_value_pct=news_scraper.two_decimals(reached_value_pct)
                #     )
            for (team, oppo) in TEAMS_PLAYING.iteritems():
                get_possible_lineups(team, oppo)

        except csv.Error as e:
            sys.exit('file %s: %s' % (csv_file, e))


get_dk_money_obj('2017-10-17')
def get_daily_snapshot():
    # for all players playing in tomorrow's game we are going to get how they played in the preseason
    with open('../scrape/json_files/team_schedules/'+YEAR+'/league_schedule.json',) as data_file:
        data = json.load(data_file)
        today_date = date.today()
        # today_date = date.today() - timedelta(days=4)
        last_two_week_date = date.today() - timedelta(days=14)
        formatted_date = today_date.strftime("%a, %b %-d, %Y")

        opponents = {}
        fantasy_lab_news = news_scraper.get_fantasy_lab_news()
        # fantasy_lab_news = {}
        # vegas_lines = news_scraper.get_vegas_lines(str(today_date))
        dk_money_obj = {}

        dk_teams_list = []
        with open('../scrape/csv/'+str(today_date)+'.csv',) as csv_file:
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
                    # print dk_team_abbrev
                    if dk_team_abbrev not in dk_teams_list:
                        dk_teams_list.append(dk_team_abbrev)

            except csv.Error as e:
                sys.exit('file %s: %s' % (csv_file, e))

        # # its not on the schedule
        # for game in data[formatted_date]:
        #     # print game
        #     if game['team'] in dk_teams_list:
        #         opponents[game['team']] = game['opp']
        #         opponents[game['opp']] = game['team']
  
        all_team_players = {}
        # all_players = []
        player_news = {}
        players_string = ''
        player_value_obj = {}
        value_games_min = {}

        sql_positions = {
            'PG': 'player_1',
            'SG': 'player_2',
            'SF': 'player_3',
            'PF': 'player_4',
            'C': 'player_5'
        }

        # team_synergy_ranks = execute_query(sqlfetch.get_team_synergy_ranks(today_date))
        team_possessions_ranks = execute_query(sqlfetch.get_team_possessions_per_game(today_date))
        team_foul_ranks = execute_query(sqlfetch.get_team_fouls(FIRST_DATE_REG_SEASON))
        team_fga_ranks = execute_query(sqlfetch.get_team_fga_ranking(FIRST_DATE_REG_SEASON))
        team_reb_ranks = execute_query(sqlfetch.get_team_reb_ranking(FIRST_DATE_REG_SEASON))
        team_rating_ranks = execute_query(sqlfetch.get_team_ratings(FIRST_DATE_REG_SEASON))
        player_daily_status = news_scraper.player_daily_status()
        # open the lineup analysis
        with open('../scrape/misc/updated_depth_chart/lineup_analysis.json',) as la:
            team_lineup_analysis = json.load(la)

        team_last_game_info_obj = {}
        dvp_considerations = {}
        oppo_dvp_obj = {}
        usg_line_up_summary = {}
        top_line_up_summary = {}
        dvp_positions = ['PG', 'SG', 'G', 'SF', 'PF', 'F', 'C']
        dvp_considerations_players = []

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

            if team == 'BKN':
                fantasy_team = 'BRK'
            elif team == 'PHX':
                fantasy_team = 'PHO'
            elif team == 'CHA':
                fantasy_team = 'CHO'
            fantasy_team = team

            with open('../scrape/misc/fantasy_stats/'+fantasy_team+'.json') as data_file:
                data = json.load(data_file)
                oppo_dvp_obj[fantasy_team] = {}
                for position in dvp_positions:
                    fp_against = data[position]
                    oppo_dvp_obj[fantasy_team][position] = fp_against

                    # players that you have to consider
                    if fp_against['rank'] < 10:

                        if fantasy_team in dvp_considerations:
                            dvp_considerations[fantasy_team][position] = fp_against
                        else:
                            dvp_considerations[fantasy_team] = {}
                            dvp_considerations[fantasy_team][position] = fp_against
                    
        # players that you have to consider wrt to dvp
        for (dvp_team, dvp_position) in dvp_considerations.iteritems():
            print dvp_team
            dvp_oppo = all_team_players[dvp_team]['oppo']

            for (position, dvp_info) in dvp_position.iteritems():
                if position != 'G' and position != 'F':

                    print '{position}: {season} ({rank})'.format(
                        position=position, \
                        season=dvp_info['Season'], \
                        rank=dvp_info['rank'])

                    # run the query for team to examine what attributes affect the cause
                    # get based on usage
                    print all_team_players[dvp_oppo]['players'][position].keys()
                    dvp_considerations_players += all_team_players[dvp_oppo]['players'][position].keys()

            print '\n'

        # get FGA and fouls

        for team, team_players in all_team_players.iteritems():
            oppo = team_players['oppo']

            if team == 'BKN':
                wowy_team = 'BRK'
                fantasy_team = 'BRK'
            elif team == 'PHX':
                wowy_team = 'PHO'
                fantasy_team = 'PHO'
            elif team == 'CHA':
                wowy_team = 'CHO'
                fantasy_team = 'CHO'
            wowy_team = team
            fantasy_team = team

            if oppo == 'BKN':
                wowy_oppo = 'BRK'
            elif oppo == 'PHX':
                wowy_oppo = 'PHO'
            elif oppo == 'CHA':
                wowy_oppo = 'CHO'
            wowy_oppo = oppo

            if oppo == 'BRK':
                sql_oppo = 'BKN'
            elif oppo == 'PHO':
                sql_oppo = 'PHX'
            elif oppo == 'CHO':
                sql_oppo = 'CHA'
            else:
                sql_oppo = oppo

            if team == 'BKN':
                vegas_team = 'BK'
            elif team == 'PHX':
                vegas_team = 'PHO'
            elif team == 'CHA':
                vegas_team = 'CHO'
            else:
                vegas_team = team

            if oppo == 'BKN':
                fantasy_oppo = 'BRK'
            elif oppo == 'PHX':
                fantasy_oppo = 'PHO'
            elif oppo == 'CHA':
                fantasy_oppo = 'CHO'
            fantasy_oppo = oppo

            sql_oppo = oppo
            if oppo in TRANSLATE_DICT:
                sql_oppo = TRANSLATE_DICT[oppo]
            
            sql_team = team
            if team in TRANSLATE_DICT:
                sql_team = TRANSLATE_DICT[team]
            

            # num_games_played_team = sqlfetch.execute_query(sqlfetch.get_num_games_played(sql_team, FIRST_DATE_REG_SEASON))
            players_played_for_team = sqlfetch.execute_query(sqlfetch.get_players_played_for_team(sql_team, FIRST_DATE_REG_SEASON))
            
            out_players = ['Eric Bledsoe', 'Leandro Barbosa', 'Brandon Knight']
            for players_played in players_played_for_team:
                if players_played['PLAYER_NAME'] in news_scraper.SQL_TO_DK_TRANSLATE:
                    players_played['PLAYER_NAME'] = news_scraper.SQL_TO_DK_TRANSLATE[players_played['PLAYER_NAME']]
                if players_played['PLAYER_NAME'] not in all_team_players[team]['all_players']:                    
                    out_players.append(players_played['PLAYER_NAME'])


            oppo_foul_rank = (item for item in team_foul_ranks \
                if item["TEAM"] == sql_oppo).next()
            oppo_fga_rank = (item for item in team_fga_ranks \
                if item["TEAM"] == sql_oppo).next()
            
            top_reb_pfd_pct = sqlfetch.execute_query(sqlfetch.get_top_reb_pfd_pct(sql_team, FIRST_DATE_REG_SEASON))
            top_reb_pfd_dict = {}
            for top_reb_pfd in top_reb_pfd_pct:
                top_reb_pfd_dict[top_reb_pfd['PLAYER_NAME']] = top_reb_pfd

            # we have to account for you especially if you played possessions last game
            team_last_game_lineup = sqlfetch.execute_query(sqlfetch.get_last_game_lineup(sql_team, FIRST_DATE_REG_SEASON))
            last_game_player_dict = {}
            for last_game_lineup in team_last_game_lineup[0:5:1]:
                player_position_keys = ['PLAYER_1', 'PLAYER_2', 'PLAYER_3', 'PLAYER_4', 'PLAYER_5']
                for player_position in player_position_keys:
                    if player_position in last_game_player_dict:
                        last_game_player_dict[last_game_lineup[player_position]] += last_game_lineup['POSSESSIONS']
                    else:
                        last_game_player_dict[last_game_lineup[player_position]] = last_game_lineup['POSSESSIONS']

            # account for last game players against PFD and REB of opponents
            sorted_top_pfd_dict = sorted(top_reb_pfd_dict, key=lambda x: (top_reb_pfd_dict[x]['PCT_PFD']), reverse=True)
            sorted_top_reb_dict = sorted(top_reb_pfd_dict, key=lambda x: (top_reb_pfd_dict[x]['PCT_REB']), reverse=True)

            if team_foul_ranks.index(oppo_foul_rank) < 10:
                try:
                    print 'Top PFD:'
                    for top_pfd_player in sorted_top_pfd_dict:
                        if top_pfd_player in all_team_players[team]['all_players']:
                            print '{player}: {pct_pfd}'.format(player=top_pfd_player, pct_pfd=top_reb_pfd_dict[top_pfd_player]['PCT_PFD'])
                except KeyError:
                    print 'Out of range'

                print '\n'
            if team_fga_ranks.index(oppo_fga_rank) < 10:
                try:
                    print 'Top REB:'
                    for top_reb_player in sorted_top_reb_dict:
                        if top_reb_player in all_team_players[team]['all_players']:
                            print '{player}: {pct_reb}'.format(player=top_reb_player, pct_reb=top_reb_pfd_dict[top_reb_player]['PCT_REB'])

                except KeyError:
                    print 'Out of range'

                print '\n'

            # last game

            team_wowy_obj = news_scraper.player_on_off(WOWY_TEAMS[team], 'all', [], [], '2017-04-12', str(today_date))
            # team_wowy_obj = news_scraper.player_on_off(WOWY_TEAMS[team], 'all', [], [], str(team_last_game_info_obj[team]['date']), str(team_last_game_info_obj[team]['date']))

            last_season_against_team = news_scraper.player_on_off(WOWY_TEAMS[team], [WOWY_TEAMS[oppo]], [], [], '2015-10-26' , str(today_date))

            print 'Team Last Game (Top 5 lineups)'
            print '({result}) ({streak}) {date} {location} {oppo} [{score}]'.format(
                result=team_last_game_info_obj[team]['result'], streak=team_last_game_info_obj[team]['streak'], date=team_last_game_info_obj[team]['date'],\
                location=team_last_game_info_obj[team]['location'], oppo=team_last_game_info_obj[team]['oppo'], score=team_last_game_info_obj[team]['score'])

            temp_lineup_obj = {}
            yesterday_lineup_obj = {}
            
            for lineup in team_wowy_obj['lineups'][0:5:1]:
                # the line up needs to be formatted in this format
                # ['Matthew Dellavedova', 'Khris Middleton', 'Tony Snell', 'Giannis Antetokounmpo', 'Thon Maker']

                # hit the api to get the USG rate for each lineup
                player_on_obj = news_scraper.player_on_off(WOWY_TEAMS[wowy_team], 'all', lineup['lineup'], [], '2017-04-12', str(today_date))
                # player_on_obj = news_scraper.player_on_off(WOWY_TEAMS[wowy_team], 'all', lineup['lineup'], [], str(team_last_game_info_obj[team]['date']), str(team_last_game_info_obj[team]['date']))

                last_game_player_1 = lineup['lineup'][0]
                last_game_player_2 = lineup['lineup'][1]
                last_game_player_3 = lineup['lineup'][2]
                last_game_player_4 = lineup['lineup'][3]
                last_game_player_5 = lineup['lineup'][4]

                
                print '{player_1} ({p1_usg}) (r{p1_reb}), {player_2} ({p2_usg}) (r{p2_reb}), {player_3} ({p3_usg}) (r{p3_reb}), {player_4} ({p4_usg}) (r{p4_reb}), {player_5} ({p5_usg}) (r{p5_reb})'.format(
                    player_1=last_game_player_1, player_2=last_game_player_2, player_3=last_game_player_3,
                    player_4=last_game_player_4, player_5=last_game_player_5,
                    p1_usg=player_on_obj['players'][last_game_player_1]['compiled_stats']['usg'],
                    p2_usg=player_on_obj['players'][last_game_player_2]['compiled_stats']['usg'],
                    p3_usg=player_on_obj['players'][last_game_player_3]['compiled_stats']['usg'],
                    p4_usg=player_on_obj['players'][last_game_player_4]['compiled_stats']['usg'],
                    p5_usg=player_on_obj['players'][last_game_player_5]['compiled_stats']['usg'],
                    p1_reb=player_on_obj['players'][last_game_player_1]['compiled_stats']['reb_rate'],
                    p2_reb=player_on_obj['players'][last_game_player_2]['compiled_stats']['reb_rate'],
                    p3_reb=player_on_obj['players'][last_game_player_3]['compiled_stats']['reb_rate'],
                    p4_reb=player_on_obj['players'][last_game_player_4]['compiled_stats']['reb_rate'],
                    p5_reb=player_on_obj['players'][last_game_player_5]['compiled_stats']['reb_rate']
                )
                print 'Poss: {poss}'.format(poss=lineup['poss'])

                # summary of this
                player_pos_index = [0, 1, 2, 3, 4]
                for idx in player_pos_index:
                    idx_player = lineup['lineup'][idx]

                    if idx_player in yesterday_lineup_obj:
                        # dont just count the usg
                        # get reb, ast and dkm
                        for stat_keys in ['usg', 'reb_rate', 'ast_rate', 'dkm', 'ts']:
                            yesterday_lineup_obj[idx_player][stat_keys].append(player_on_obj['players'][idx_player]['compiled_stats'][stat_keys])
                    else:
                        yesterday_lineup_obj[idx_player] = {
                            'usg': [player_on_obj['players'][idx_player]['compiled_stats']['usg']],
                            'reb_rate': [player_on_obj['players'][idx_player]['compiled_stats']['reb_rate']],
                            'ast_rate': [player_on_obj['players'][idx_player]['compiled_stats']['ast_rate']],
                            'dkm': [player_on_obj['players'][idx_player]['compiled_stats']['dkm']],
                            'ts': [player_on_obj['players'][idx_player]['compiled_stats']['ts']],
                        }
            print '\n'
            
            # get highest usage rate with who they played with
            process_lineup_usg(dvp_considerations_players, {}, yesterday_lineup_obj)
                        
            print '\n'


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

            # opponent
            print 'Opponent Last Game (Top 5 lineups)'
            print '({result}) ({streak}) {date} {location} {oppo} [{score}]'.format(
                result=team_last_game_info_obj[oppo]['result'], streak=team_last_game_info_obj[oppo]['streak'], date=team_last_game_info_obj[oppo]['date'],\
                location=team_last_game_info_obj[oppo]['location'], oppo=team_last_game_info_obj[oppo]['oppo'], score=team_last_game_info_obj[oppo]['score'])

            
            oppo_last_game_lineup = sqlfetch.execute_query(sqlfetch.get_last_game_lineup(sql_oppo, FIRST_DATE_REG_SEASON))

            for last_game in oppo_last_game_lineup[0:5:1]:
                print '{player_1}, {player_2}, {player_3}, {player_4}, {player_5}'.format(
                    player_1=last_game['PLAYER_1'], player_2=last_game['PLAYER_2'], player_3=last_game['PLAYER_3'],
                    player_4=last_game['PLAYER_4'], player_5=last_game['PLAYER_5']
                )
                print 'Poss: {poss}'.format(poss=last_game['POSSESSIONS'])

            print '\n'
            print 'From Last Season vs ' + oppo
            # sort by usg first, then remainder by poss
            sorted_usg_list = sorted(last_season_against_team['players'], key=lambda x: (last_season_against_team['players'][x]['compiled_stats']['usg']), reverse=True)
            for player in sorted_usg_list:
                player_name = player
                player_obj = last_season_against_team['players'][player]

                if player_obj['compiled_stats']['usg'] >= 20 and player_obj['poss'] >= 20:
                    if player in all_team_players[team]['all_players']:
                        print '{player}, POSS: {poss}, USG: {usg}, SI: {si}'.format(
                            player=player_name, poss=player_obj['poss'], usg=player_obj['compiled_stats']['usg'],\
                            si=player_obj['compiled_stats']['scoring_index'])

            print '\n'

            if oppo in TRANSLATE_DICT:
                oppo = TRANSLATE_DICT[oppo]

            if team in TRANSLATE_DICT:
                team = TRANSLATE_DICT[team]

            team_possession_rank = (item for item in team_possessions_ranks \
                if item["TEAM_ABBREVIATION"] == team).next()
            oppo_possession_rank = (item for item in team_possessions_ranks \
                if item["TEAM_ABBREVIATION"] == oppo).next()
           
            oppo_reb_rank = (item for item in team_reb_ranks \
                if item["TEAM"] == oppo).next()
            oppo_rating_rank = (item for item in team_rating_ranks \
                if item["TEAM"] == oppo).next()
            # oppo_synergy_rank = (item for item in team_synergy_ranks \
            #     if item["TEAM_NAME"] == oppo).next()

            print '{team}: {team_poss} ({team_poss_rank}) vs {oppo}: {oppo_poss} ({oppo_poss_rank})'.format(
                    team=team, oppo=oppo, team_poss=team_possession_rank['AVG_NUM_POSS'], \
                    team_poss_rank=team_possession_rank['POSSG_RANK'], \
                    oppo_poss=oppo_possession_rank['AVG_NUM_POSS'], \
                    oppo_poss_rank=oppo_possession_rank['POSSG_RANK'])


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

            # print oppo + ' Synergy Ranks'
            # print 'PnR Handler: {roll_rank}, PnR Roller: {handler_rank}, SpotUp Shots: {spotup_rank}, ISO: {iso_rank}'.format(
            #     roll_rank=oppo_synergy_rank['PR_ROLL_RANK'], \
            #     handler_rank=oppo_synergy_rank['PR_HANDLER_RANK'], \
            #     spotup_rank=oppo_synergy_rank['SPOTUP_RANK'], \
            #     iso_rank=oppo_synergy_rank['ISO_RANK'])

            print '{oppo} DvP:'.format(oppo=oppo)

            positions = ['G', 'F', 'C']
            for position in positions:
                print '{position}: {season} ({rank})'.format(
                        position=position, \
                        season=oppo_dvp_obj[fantasy_oppo][position]['Season'], \
                        rank=oppo_dvp_obj[fantasy_oppo][position]['rank'])

            print 'Oppo Small Lineup Summary'
            print '% Small Team Lineup (avg): {la_avg}, (median): {la_med}'.format(
                            la_avg=team_lineup_analysis[wowy_oppo]['avg'], \
                            la_med=team_lineup_analysis[wowy_oppo]['median'])

            print '\n'

            for position, position_players in team_players['players'].iteritems():
                for lineup_player, player_info in position_players.iteritems():
                    player = player_info['name']
                    player_role = player_info['role']

                    # set default status
                    player_status = 'Active'

                    if player in news_scraper.DK_TO_SQL_TRANSLATE:
                        sql_player = news_scraper.DK_TO_SQL_TRANSLATE[player]
                    else:
                        sql_player = player

                    wowy_player = ''
                    if player in news_scraper.DK_TO_WOWY_TRANSLATE:
                        wowy_player = news_scraper.DK_TO_WOWY_TRANSLATE[player]
                    else:
                        wowy_player = player

                    played_last_game = ''
                    if wowy_player in temp_lineup_obj:
                        player_obj = temp_lineup_obj[wowy_player]
                        total_poss_pct = float(player_obj['poss'])/float(total_possessions)*100
                    else:
                        played_last_game = 'DNP'

                    

                    if player in dk_money_obj:
                        player_salary = dk_money_obj[player]['salary']
                        fp_needed = dk_money_obj[player]['fp_needed']
                        avg_val = dk_money_obj[player]['avg_val']
                        fp_avg = dk_money_obj[player]['fp_avg']

                        player_games_log = sqlfetch.execute_query(sqlfetch.get_player_dk_points_log(sql_player, FIRST_DATE_REG_SEASON))
                        num_games_played = len(player_games_log)

                        # if they have never played a game
                        if num_games_played <= 0:
                            out_players.append(sql_player)
                        else:
                            # basketball monster use sql names
                            if sql_player in player_daily_status['today'] or sql_player in player_daily_status['all']:

                                print sql_player
                                if sql_player in player_daily_status['today']:
                                    player_status = player_daily_status['today'][sql_player]
                                if sql_player in player_daily_status['all']:
                                    player_status = player_daily_status['all'][sql_player]
                                
                                

                                print player + ' Status: ' + player_status
                                # if the player is not playing
                                # check status of depth chart
                                if player_role == 'Lim PT' and played_last_game == 'DNP' and player_status != 'Playing' and player_status != 'Probable':
                                    out_players.append(sql_player)

                                # if players are off the same role
                                # we can try to grup them together and send it to the API
                                # see what lineups were played when they are out (by poss)
                                if (player_status == 'Questionable' or \
                                    player_status == 'Out' or \
                                    player_status == 'Doubtful' or \
                                    player_status == 'Injured') \
                                    and fp_avg > 0:

                                    # or if they are not on the roster anymore
                                    out_players.append(sql_player)

                                    # player_off_obj = news_scraper.player_on_off(WOWY_TEAMS[wowy_team], 'all', [], [wowy_player], FIRST_DATE_REG_SEASON, str(today_date))

                                    # sorted_usg_list = sorted(player_off_obj['players'], key=lambda x: (player_off_obj['players'][x]['compiled_stats']['usg']), reverse=True)
                                    # for other_player in sorted_usg_list:
                                    #     other_player_name = other_player
                                    #     player_off_wowy_obj = player_off_obj['players'][other_player]

                                    #     if player_off_wowy_obj['compiled_stats']['usg'] >= 20 and player_off_wowy_obj['poss'] >= 20:

                                    #         # only get the current players on that team
                                    #         if other_player_name in all_team_players[fantasy_team]['all_players']:
                                    #             split_name = other_player_name.split('.')
                                    #             if len(split_name) > 1:
                                    #                 split_other_player_name = "".join(split_name)
                                    #             else:
                                    #                 split_name = other_player_name


                                    #         # something wrong here with teh name
                                    #         # if split_name in news_scraper.WOWY_TO_DK_TRANSLATE:
                                    #         #     split_name = news_scraper.WOWY_TO_DK_TRANSLATE[split_name]
                                    #         #     if split_name in news_scraper.DK_TO_SQL_TRANSLATE:
                                    #         #         split_name = news_scraper.DK_TO_SQL_TRANSLATE[split_name]

                                    #         # there needs to be a translate here
                                    #         player_avg_usg = execute_query(sqlfetch.get_player_avg_usg(FIRST_DATE_REG_SEASON, today_date, split_name))
                                    #         if player_off_wowy_obj['compiled_stats']['usg'] >= player_avg_usg[0]['AVG_USG'] and \
                                    #             player_off_wowy_obj['compiled_stats']['usg'] >= 20:

                                    #             if player in all_team_players[wowy_team]['all_players']:
                                    #                 print '{player}, POSS: {poss}, USG: {usg}, SI: {si}'.format(
                                    #                     player=other_player_name, poss=player_off_wowy_obj['poss'], usg=player_off_wowy_obj['compiled_stats']['usg'],\
                                    #                     si=player_off_wowy_obj['compiled_stats']['scoring_index'])


                                    # fetch games missed
                                    player_off_lineup = sqlfetch.execute_query(sqlfetch.get_games_not_played_by_player(team, sql_player, FIRST_DATE_REG_SEASON))

                                    # if len(player_off_lineup) >= 1:
                                    temp_player_replace_obj = {}
                                    for position in dk_money_obj[player]['positions']:
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

                                    sorted_player_replace_obj = sorted(temp_player_replace_obj, key=lambda x: (temp_player_replace_obj[x]['poss']), reverse=True)

                                    print '\n'
                                    print 'Replacement Players'
                                    for replacement_player in sorted_player_replace_obj:
                                        if temp_player_replace_obj[replacement_player]['min'] > 0:
                                            print '{player_name}, MIN: {min} POSS: {poss}'.format(
                                                player_name=replacement_player, min=temp_player_replace_obj[replacement_player]['min'], poss=temp_player_replace_obj[replacement_player]['poss']
                                            )
                                    print '\n'


                            if player_status != 'Out':
                                if 'SG' in dk_money_obj[player]['positions'] or \
                                    'PG' in dk_money_obj[player]['positions']:
                                    dvp_against_player = oppo_dvp_obj[fantasy_oppo]['G']
                                elif 'SF' in dk_money_obj[player]['positions'] or \
                                    'PF' in dk_money_obj[player]['positions']:
                                    dvp_against_player = oppo_dvp_obj[fantasy_oppo]['F']
                                else:
                                    dvp_against_player = oppo_dvp_obj[fantasy_oppo]['C']

                                # player_games_log = sqlfetch.execute_query(sqlfetch.get_player_dk_points_log(sql_player, FIRST_DATE_REG_SEASON))
                                # num_games_played = len(player_games_log)

                                get_player_avg_min = sqlfetch.execute_query(sqlfetch.get_player_avg_min(sql_player, FIRST_DATE_REG_SEASON))
                                get_player_avg_min_last_week = sqlfetch.execute_query(sqlfetch.get_player_avg_min(sql_player, last_two_week_date))

                                try:
                                    played_avg_min = get_player_avg_min[0]['AVG_MIN']
                                except IndexError:
                                    played_avg_min = 0

                                print '{player_name} ({player_role}) ({num_games_played}G) ({played_avg_min}M) {position}: {salary}, AVG: {fp_avg}, '\
                                        'OPPO DvP: {dvp_against_player} ({dvp_against_player_rank}), '\
                                        'V: {avg_val}, PTS NEEDED: {fp_needed}'.format(
                                            player_name=player, position=dk_money_obj[player]['positions'], \
                                            player_role=player_role, num_games_played=num_games_played, \
                                            salary=player_salary, dvp_against_player=dvp_against_player['Season'], \
                                            dvp_against_player_rank=dvp_against_player['rank'], fp_avg=fp_avg, \
                                            avg_val=news_scraper.two_decimals(avg_val), fp_needed=fp_needed, played_avg_min=played_avg_min)

                                # have the player ever reached this value? (%)
                                # num games played
                                # how recent were these (what was the latest date?)
                                dk_points_query = sqlfetch.get_player_dk_points_log(sql_player, FIRST_DATE_REG_SEASON) + \
                                    'AND tb.FG3M*0.5+tb.REB*1.25+tb.AST*1.50+tb.STL*2+tb.BLK*2+tb.TO*-0.5+tb.PTS*1 >= {fp_needed} '\
                                    'ORDER BY DATE'.format(fp_needed=fp_needed)

                                have_reached_value = sqlfetch.execute_query(dk_points_query)
                                num_times_reached_value = len(have_reached_value)

                                value_games_game_id = []
                                value_games_min[player] = {
                                    'min': [],
                                    'avg_min_last_week': get_player_avg_min_last_week[0]['AVG_MIN']
                                }
                                for reached_value_games in have_reached_value:
                                    # need to explore these games
                                    value_games_game_id.append(reached_value_games['GAME_ID'])
                                    playtime_string = reached_value_games['MIN'].split(':')
                                    if len(playtime_string) > 1:
                                        playtime_in_seconds = int(playtime_string[0])*60 + int(playtime_string[1])
                                        value_games_min[player]['min'].append(playtime_in_seconds)


                                if num_times_reached_value >= 1:
                                    reached_value_pct = (float(num_times_reached_value) / float(num_games_played)) * 100
                                    print 'Reached V {num_times}x ({reached_value_pct}%)'.format(
                                        num_times=num_times_reached_value, reached_value_pct=news_scraper.two_decimals(reached_value_pct)
                                    )

                                    # store the reached values 
                                    player_value_obj[player] = news_scraper.two_decimals(reached_value_pct)

                                # based on last game's positions
                                # based on the combination of both last game as well as the DK positions
                                player_matchups_list = []
                                if wowy_player in temp_lineup_obj:
                                    player_obj = temp_lineup_obj[wowy_player]
                                    for player_obj_positon, poss in player_obj['positions'].iteritems():
                                        try:
                                            poss_pct = float(poss)/float(player_obj['poss'])*100
                                        except ZeroDivisionError:
                                            poss_pct = 0

                                        if poss_pct >= 20:
                                            player_matchups_list = player_matchups_list + all_team_players[fantasy_oppo]['players'][player_obj_positon].keys()
                                else:
                                    # based on the natural positions
                                    # this can be based on the avg positions
                                    for position in dk_money_obj[player]['positions']:
                                        player_matchups_list = player_matchups_list + all_team_players[fantasy_oppo]['players'][position].keys()

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


                                # # calc simple regression
                                # simple_lr_data = nba_scrape_linear_regression.get_simple_player_log_regression(player)

                                # print simple_lr_data

                                # print player_off_obj
                                # SQL stuff
                                player_pfd = execute_query(sqlfetch.get_player_pfd(FIRST_DATE_REG_SEASON, sql_player))

                                player_pf = execute_query(sqlfetch.get_player_pf(FIRST_DATE_REG_SEASON, sql_player))
                                print 'PFD: {pfd}, PF: {pf}'.format(pfd=player_pfd[0]['AVG_PFD'], pf=player_pf[0]['AVG_PF'])

                                player_against_team_logs = execute_query(sqlfetch.get_player_against_team_log(sql_oppo, sql_player))


                                if played_last_game != 'DNP':
                                    player_last_game = execute_query(sqlfetch.player_last_game(sql_player, 1, False))

                                    # i should probably also try to fetch the last game for the player so i can get # of plays
                                    # fga + (0.5 * fta) + stats['tov'] + stats['ast']
                                    try:
                                        if played_last_game != 'DNP':
                                            last_game = player_last_game[0]
                                            players_plays = last_game['FGA'] + (0.5 * last_game['FTA']) + last_game['TO'] + last_game['AST']
                                            print
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
                                    print
                                    print 'Last Time Against: {oppo}, {num_games} Games'.format(oppo=oppo, num_games=len(player_against_team_logs))
                                    print 'USG - Max: {max_usg}, Min: {min_usg}'.format(max_usg=np.max(usg_list), min_usg=np.min(usg_list))
                                    print 'FP - Max: {max_dk}, Min: {min_dk}'.format(max_dk=np.max(dk_list), min_dk=np.min(dk_list))
                                    print 'MIN - Max: {max_min}, Min: {min_min}'.format(max_min=np.max(min_list), min_min=np.min(min_list))
                                    print 'FP/MIN - Max: {max_fpm}, Min: {min_fpm}'.format(max_fpm=np.max(fp_min_list), min_fpm=np.min(fp_min_list))
                                print '\n'

            # out players and possible lineups
            out_players = ', '.join(out_players)
            print out_players
            possible_lineups = sqlfetch.execute_query(sqlfetch.get_lineup_from_absence(out_players, team, 10))
            usg_line_up_summary[team] = {}

            # call nba_wowy
            # put percentages
            top_line_up_summary[team] = []

            for idx, possible_lineup in enumerate(possible_lineups):
                # print possible_lineup
                if possible_lineup['PLAYER_1'] in news_scraper.SQL_TO_WOWY_TRANSLATE:
                    player_1 = news_scraper.SQL_TO_WOWY_TRANSLATE[possible_lineup['PLAYER_1']]
                else:
                    player_1 = possible_lineup['PLAYER_1']

                if possible_lineup['PLAYER_2'] in news_scraper.SQL_TO_WOWY_TRANSLATE:
                    player_2 = news_scraper.SQL_TO_WOWY_TRANSLATE[possible_lineup['PLAYER_2']]
                else:
                    player_2 = possible_lineup['PLAYER_2']

                if possible_lineup['PLAYER_3'] in news_scraper.SQL_TO_WOWY_TRANSLATE:
                    player_3 = news_scraper.SQL_TO_WOWY_TRANSLATE[possible_lineup['PLAYER_3']]
                else:
                    player_3 = possible_lineup['PLAYER_3']

                if possible_lineup['PLAYER_4'] in news_scraper.SQL_TO_WOWY_TRANSLATE:
                    player_4 = news_scraper.SQL_TO_WOWY_TRANSLATE[possible_lineup['PLAYER_4']]
                else:
                    player_4 = possible_lineup['PLAYER_4']

                if possible_lineup['PLAYER_5'] in news_scraper.SQL_TO_WOWY_TRANSLATE:
                    player_5 = news_scraper.SQL_TO_WOWY_TRANSLATE[possible_lineup['PLAYER_5']]
                else:
                    player_5 = possible_lineup['PLAYER_5']

                    '''
                    {
                        lineup: {
                            1: {
                                usg:
                                reb:
                            }
                            2:
                            3:
                            4:
                            5:
                        }
                    }
                    '''
                on_players = [player_1, player_2, player_3, player_4, player_5]
                player_on_obj = news_scraper.player_on_off(WOWY_TEAMS[wowy_team], 'all', on_players, [], FIRST_DATE_REG_SEASON, str(today_date))

                if len(player_on_obj['lineups']) > 0:
                    temp_obj = {}
                    for on_player in on_players:
                        temp_obj[on_player] = {
                            'usg': player_on_obj['players'][on_player]['compiled_stats']['usg'],
                            'reb': player_on_obj['players'][on_player]['compiled_stats']['reb_rate']
                        }
                    top_line_up_summary[team].append(temp_obj)
                    print '{player_1} ({p1_usg}) (r{p1_reb}), {player_2} ({p2_usg}) (r{p2_reb}), {player_3} ({p3_usg}) (r{p3_reb}), {player_4} ({p4_usg}) (r{p4_reb}), {player_5} ({p5_usg}) (r{p5_reb})'.format(
                        player_1=possible_lineup['PLAYER_1'], player_2=possible_lineup['PLAYER_2'], player_3=possible_lineup['PLAYER_3'],
                        player_4=possible_lineup['PLAYER_4'], player_5=possible_lineup['PLAYER_5'],
                        p1_usg=player_on_obj['players'][player_1]['compiled_stats']['usg'],
                        p2_usg=player_on_obj['players'][player_2]['compiled_stats']['usg'],
                        p3_usg=player_on_obj['players'][player_3]['compiled_stats']['usg'],
                        p4_usg=player_on_obj['players'][player_4]['compiled_stats']['usg'],
                        p5_usg=player_on_obj['players'][player_5]['compiled_stats']['usg'],
                        p1_reb=player_on_obj['players'][player_1]['compiled_stats']['reb_rate'],
                        p2_reb=player_on_obj['players'][player_2]['compiled_stats']['reb_rate'],
                        p3_reb=player_on_obj['players'][player_3]['compiled_stats']['reb_rate'],
                        p4_reb=player_on_obj['players'][player_4]['compiled_stats']['reb_rate'],
                        p5_reb=player_on_obj['players'][player_5]['compiled_stats']['reb_rate']
                    )
                    print 'Poss: {poss}, Min: {min}'.format(poss=possible_lineup['POSSESSIONS'], min=possible_lineup['MINUTES_PLAYED'])

                    # summary of this
                    for usg_player in on_players:
                        if usg_player in usg_line_up_summary[team]:
                            for stat_keys in ['usg', 'reb_rate', 'ast_rate', 'dkm', 'ts']:
                                usg_line_up_summary[team][usg_player][stat_keys].append(player_on_obj['players'][usg_player]['compiled_stats'][stat_keys])
                        else:
                            usg_line_up_summary[team][usg_player] = {
                            'usg': [player_on_obj['players'][usg_player]['compiled_stats']['usg']],
                            'reb_rate': [player_on_obj['players'][usg_player]['compiled_stats']['reb_rate']],
                            'ast_rate': [player_on_obj['players'][usg_player]['compiled_stats']['ast_rate']],
                            'dkm': [player_on_obj['players'][usg_player]['compiled_stats']['dkm']],
                            'ts': [player_on_obj['players'][usg_player]['compiled_stats']['ts']],
                        }

            print '\n'
            process_lineup_usg(dvp_considerations_players, {}, usg_line_up_summary[team])

            print '\n'

            # # get highest usage rate with who they played with
            # for lineup in top_line_up_summary[team]:
            #     for lineup_player, lineup_player_values in lineup.iteritems():
            #         if lineup_player_values['usg'] < summary_lineup_usg_obj[lineup_player]['median']:
            #             # i have to get the other players on here or just take that whole lineup
            #         print 'here'

        # i need to know that in losses how the team performed

        sorted_player_value_obj = sorted(player_value_obj, key=lambda x: (player_value_obj[x]), reverse=True)
        # obvious this does not apply to top tier players
        for player_value in sorted_player_value_obj:
            # if you are limited playing time then we shouldn't even account for you
            # look @ the last 2 weeks of games minutes vs. the minutes they played when they hit value            
            # get the min median and max for those dates
            if player_value not in out_players:
                if len(value_games_min[player_value]['min']) > 0:
                    if (np.min(value_games_min[player_value]['min'])/60) < value_games_min[player_value]['avg_min_last_week']:
                        print '{player_name}, %: {min}'.format(
                            player_name=player_value, min=player_value_obj[player_value]
                        )                        
                else:
                    print '{player_name}, has never reached value'.format(
                            player_name=player_value, min=value_games_min[player_value]['AVG_MIN']
                        )


def process_temp_obj(temp_obj, results):
    for position_player in results:
        if position_player['PLAYER_NAME'] not in temp_obj:
            temp_obj[position_player['PLAYER_NAME']] = {
                'min': position_player['AVG_MIN'],
                'poss': position_player['AVG_POSS']
            }
        else:
            temp_obj[position_player['PLAYER_NAME']]['min'] += position_player['AVG_MIN']
            temp_obj[position_player['PLAYER_NAME']]['poss'] += position_player['AVG_POSS']

    return temp_obj

# process the possessions
def print_poss_discrepencies(player_obj, num_games):
    for (player, plays) in player_obj.iteritems():
        print player
        print plays['min'] / num_games
        print plays['poss'] / num_games

def process_lineup_usg(dvp_considerations_players, temp_player_lineup_usg, lineup_obj):

    for (lineup_player, usage) in lineup_obj.iteritems():
        if lineup_player in dvp_considerations_players:
            consideration_str = '(IN DVP CONSIDERATION)'
        else:
            consideration_str = ''
            # construct a temp obj in order to sort by the usage
        # print usage
        temp_player_lineup_usg[lineup_player] = {
            'lineups': len(usage['usg']),
            'med_usg': np.median(usage['usg']),
            'med_reb_rate': np.median(usage['reb_rate']),
            'med_ast_rate': np.median(usage['ast_rate']),
            'med_dkm': np.median(usage['dkm']),
            'med_ts': np.median(usage['ts']),
            'consideration_str': consideration_str
        }

    sorted_player_lineup_usg_obj = sorted(temp_player_lineup_usg, key=lambda x: (temp_player_lineup_usg[x]['med_usg']), reverse=True)

    for lineup_player in sorted_player_lineup_usg_obj:
        # print lineup_player
        print lineup_player
        print '{lineups} / u {med_usg} / r {med_reb_rate} / a {med_ast_rate} / dk {med_dkm} / ts {med_ts} {consideration_str}'.format(\
            lineups=temp_player_lineup_usg[lineup_player]['lineups'], \
            med_usg=temp_player_lineup_usg[lineup_player]['med_usg'], \
            med_reb_rate=temp_player_lineup_usg[lineup_player]['med_reb_rate'], \
            med_ast_rate=temp_player_lineup_usg[lineup_player]['med_ast_rate'], \
            med_dkm=temp_player_lineup_usg[lineup_player]['med_dkm'], \
            med_ts=temp_player_lineup_usg[lineup_player]['med_ts'], \
            consideration_str=temp_player_lineup_usg[lineup_player]['consideration_str'])

    return temp_player_lineup_usg

# get_daily_snapshot()
