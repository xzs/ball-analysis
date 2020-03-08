# !/usr/bin/env python
# _*_ coding:utf-8 _*_
import MySQLdb
import pprint
import logging
import numpy as np
import sqlfetch
import news_scraper
import test_classifier
import json
import csv
from datetime import date, timedelta, datetime
from collections import OrderedDict
import urllib

import warnings
# explictly not show warnings
warnings.filterwarnings("ignore")

import urllib2
from bs4 import BeautifulSoup

import MySQLdb.converters

pp = pprint.PrettyPrinter(indent=1)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

today_date = date.today()
LAST_DATE_REG_SEASON = str(today_date)
FIRST_DATE_REG_SEASON = '2018-10-16'

LAST_YEAR_FIRST_DATE_REG_SEASON = '2017-10-17'


# global vars
TEAMS = news_scraper.TEAMS
DK_TEAMS = news_scraper.DK_TEAMS
TRANSLATE_DICT = news_scraper.TRANSLATE_DICT
WOWY_TEAMS = news_scraper.WOWY_TEAMS
POSITION_TRANSLATE_DICT = news_scraper.POSITION_TRANSLATE_DICT
PLAYER_DAILY_STATUS = news_scraper.player_daily_status()
TEAMS_PLAYING = {}
ALL_TEAM_PLAYERS = {}
PLAYER_SIMPLE_PROJECTION_BASIS = {}
DK_MONEY_OBJ = {}
LAST_PLAYER_SUMMARY_OBJ = {}
TEAM_FGA_PACE = {}
LINEUP_BASED_PROJ = {}
PLAYER_AVG_PLAYTIME = {}
PLAYER_ADV_STATS = {}
TEAM_SPORTVU_FGA = {}
LINEUP_RANK = {}
POSSIBLE_GAME_STACKS = {}
OPPORTUNITY_PLAYERS = []
POSSIBLE_LINEUP = {}
FAVOR_OBJ = {
    'PG': {},
    'SG': {},
    'SF': {},
    'PF': {},
    'C': {}
}
TEAM_DEPTH_COUNT = {}
PLAYER_POSITIONS = {}

OBVIOUS_OUTS = {
    'by_position': {},
    'by_team': {},
    'players': []
}
DIRECT_POSITION_REPLACEMENT_PLAYERS = []

# sg = sf & pg
SECONDARY_BENEFITS = {
    'C': ['PF'],
    'PF': ['C', 'SF'],
    'SF': ['PF', 'SG'],
    'SG': ['SF', 'PG'],
    'PG': ['SG', 'SF']
}

OUT_PLAYERS = []
DIFF_INJURY_LINEUPS = {}
THE_CHALK = {}
NUM_AVAIL_PLAYERS = {}
TRADED_LIST = {
    'ATL': ['Jeremy Lin', 'Tyler Dorsey'],
    'BOS': [],
    'BKN': ['Kenneth Faried'],
    'CHA': [],
    'CHI': ['Justin Holiday', 'Jabari Parker', 'Bobby Portis'],
    'CLE': ['Rodney Hood', 'George Hill', 'Cameron Payne', 'Jalen Jones', 'Alec Burks', 'Kyle Korver', 'Andrew Harrison'],
    'DAL': ['Harrison Barnes', 'Dennis Smith Jr.', 'Wesley Matthews', 'DeAndre Jordan'],
    'DEN': [],
    'DET': ['Reggie Bullock', 'Stanley Johnson', 'Henry Ellenson'],
    'GSW': [],
    'HOU': ['Brandon Knight', 'Marquese Chriss', 'James Ennis III', 'Danuel House', 'Michael Carter-Williams', 'Carmelo Anthony'],
    'IND': [],
    'LAC': ['Tobias Harris', 'Mike Scott', 'Boban Marjanovic', 'Avery Bradley'],
    'LAL': ['Ivica Zubac', 'Svi Mykhailiuk', 'Michael Beasley'],
    'MEM': ['Marc Gasol', 'JaMychal Green', 'Shelvin Mack', 'Garrett Temple'],
    'MIA': ['Wayne Ellington', 'Tyler Johnson'],
    'MIL': ['Thon Maker', 'Matthew Dellavedova'],
    'MIN': ['Jimmy Butler', 'Isaiah Canaan'],
    'NOP': ['Nikola Mirotic', 'Tim Frazier'],
    'NYK': ['Tim Hardaway Jr.', 'Courtney Lee', 'Enes Kanter', 'Ron Baker', 'Trey Burke', 'Wesley Matthews', 'Kristaps Porzingis'],
    'OKC': ['Timothe Luwawu-Cabarrot'],
    'ORL': ['Jonathon Simmons'],
    'PHI': ['Dario Saric', 'Wilson Chandler', 'Mike Muscala', 'Markelle Fultz', 'Robert Covington', 'Landry Shamet'],
    'PHX': ['Tyson Chandler', 'Ryan Anderson', 'Trevor Ariza', 'Isaiah Canaan'],
    'POR': ['Nik Stauskas'],
    'SAC': ['Iman Shumpert', 'Ben McLemore', 'Skal Labissiere', 'Justin Jackson'],
    'SAS': ['Pau Gasol'],
    'TOR': ['Jonas Valanciunas', 'Delon Wright', 'CJ Miles', 'Malachi Richardson'],
    'UTA': ['Alec Burks'],
    'WAS': ['Kelly Oubre Jr.', 'Otto Porter Jr.', 'Austin Rivers', 'Markieff Morris', 'John Jenkins', 'Ron Baker']
}



OUT_FOR_SEASON = ['Luc Mbah a Moute', 'Victor Oladipo', 'JR Smith', 'J.J. Barea', 'Michael Porter Jr', 'Kristaps Porzingis', 'Isaiah Briscoe', 'Cameron Payne', 'Danuel House', 'Carmelo Anthony', 'John Wall', 'Gary Payton II', 'Ron Baker', 'Michael Beasley', 'Damian Jones', 'Brandon Ingram', 'Lonzo Ball', 'Malcom Brogdon', 'CJ Miles', 'Tim Hardaway Jr.', 'Kelly Oubre Jr.', 'Jusuf Nurkic', 'Donte DiVincenzo', 'LeBron James', 'Dillon Brooks', 'Kyle Anderson', 'Jaren Jackson Jr', 'Dewayne Dedmon']

# manual injury list
OLD_OUT_LIST = {
    'ATL': ['Omari Spellman', 'Alex Poythress'],
    'BOS': [],
    'BKN': ['Allen Crabbe'],
    'CHA': ['Cody Zeller', 'Marvin Williams'],
    'CHI': ['Wendell Carter Jr.', 'Otto Porter Jr.', 'Zach LaVine', 'Kris Dunn', 'Lauri Markkanen'],
    'CLE': ['Matthew Dellavedova', 'Tristan Thompson', 'Kevin Love'],
    'DAL': ['Luka Doncic'],
    'DEN': ['Jarred Vanderbilt'],
    'DET': [],
    'GSW': ['Kevon Looney', 'Kevin Durant', 'Klay Thompson'],
    'HOU': [],
    'IND': [],
    'LAC': [],
    'LAL': ['Josh Hart', 'Reggie Bullock', 'Kyle Kuzma', 'Rajon Rondo'],
    'MEM': ['Avery Bradley', 'Joakim Noah', 'Mike Conley', 'Jonas Valanciunas', 'Chandler Parsons'],
    'MIA': ['Josh Richardson'], 
    'MIL': [],
    'MIN': ['Robert Covington', 'Luol Deng', 'Jeff Teague', 'Derrick Rose', 'Taj Gibson', 'Karl-Anthony Towns'],
    'NOP': ['Jrue Holiday', "E'Twaun Moore", 'Frank Jackson', 'Anthony Davis', 'Stanley Johnson', 'Julius Randle'],
    'NYK': ['Noah Vonleh', 'Allonzo Trier', 'Frank Ntilikina','Emmanuel Mudiay'],
    'OKC': [],
    'ORL': ['Mohamed Bamba', 'Isaiah Briscoe'],
    'PHI': ['Mike Scott'],
    'PHX': ['TJ Warren', 'Tyler Johnson', 'Deandre Ayton', 'Devin Booker', 'Richaun Holmes'],
    'POR': [],
    'SAC': ['Harry Giles III', 'Kosta Koufos'],
    'SAS': [],
    'TOR': ['OG Anunoby'],
    'UTA': ['Dante Exum'],
    'WAS': ['Trevor Ariza', 'Jabari Parker', 'Jordan McRae']
}


# manual injury list
OUT_LIST = {
    'ATL': ['Omari Spellman', 'Alex Poythress'],
    'BOS': [],
    'BKN': ['Allen Crabbe', 'Ed Davis'],
    'CHA': ['Cody Zeller', 'Marvin Williams'],
    'CHI': ['Wendell Carter Jr.', 'Otto Porter Jr.', 'Zach LaVine', 'Kris Dunn', 'Lauri Markkanen'],
    'CLE': ['Matthew Dellavedova', 'Tristan Thompson', 'Kevin Love'],
    'DAL': ['Luka Doncic'],
    'DEN': ['Jarred Vanderbilt'],
    'DET': [],
    'GSW': ['Kevon Looney', 'Kevin Durant'],
    'HOU': [],
    'IND': [],
    'LAC': [],
    'LAL': ['Josh Hart', 'Reggie Bullock', 'Kyle Kuzma', 'Rajon Rondo'],
    'MEM': ['Avery Bradley', 'Joakim Noah', 'Mike Conley', 'Jonas Valanciunas', 'Chandler Parsons'],
    'MIA': ['Josh Richardson'], 
    'MIL': [],
    'MIN': ['Robert Covington', 'Luol Deng', 'Jeff Teague', 'Derrick Rose', 'Taj Gibson', 'Karl-Anthony Towns'],
    'NOP': ['Jrue Holiday', "E'Twaun Moore", 'Frank Jackson', 'Anthony Davis', 'Stanley Johnson', 'Julius Randle'],
    'NYK': ['Noah Vonleh', 'Allonzo Trier', 'Frank Ntilikina','Emmanuel Mudiay'],
    'OKC': [],
    'ORL': ['Mohamed Bamba', 'Isaiah Briscoe'],
    'PHI': [],
    'PHX': ['TJ Warren', 'Tyler Johnson', 'Deandre Ayton', 'Devin Booker', 'Richaun Holmes'],
    'POR': ['Rodney Hood'],
    'SAC': ['Harry Giles III', 'Kosta Koufos'],
    'SAS': [],
    'TOR': ['OG Anunoby'],
    'UTA': ['Dante Exum'],
    'WAS': ['Trevor Ariza', 'Jabari Parker', 'Jordan McRae']
}


def diff_bw_out_lists():
    diff_obj = {}
    for s, p in zip(OUT_LIST, OLD_OUT_LIST):

        diff_obj[s] = {}
        diff_obj[s]['added'] = np.setdiff1d(OUT_LIST[s], OLD_OUT_LIST[p])
        diff_obj[s]['removed'] = np.setdiff1d(OLD_OUT_LIST[p], OUT_LIST[s])

    return diff_obj

DIFF_OUTS = diff_bw_out_lists()


def init_out_players():
    for player, status in PLAYER_DAILY_STATUS['all'].iteritems():
        OUT_PLAYERS.append(player)

    for team, players in OUT_LIST.iteritems():
        if len(players) >= 1:
            OUT_PLAYERS.extend(players)
    
    for players in OUT_FOR_SEASON:
        OUT_PLAYERS.append(players)


def init_player_advanced(date):
    all_advanced_data = sqlfetch.execute_query(sqlfetch.get_all_players_advanced_data(date))
    for player in all_advanced_data:
        PLAYER_ADV_STATS[player['PLAYER_NAME']] = player

    return PLAYER_ADV_STATS


def init_team_sportvu_fga(date):
    all_team_sportvu_fga = sqlfetch.execute_query(sqlfetch.get_team_sportvu_fga(date))

    for team in all_team_sportvu_fga:
        TEAM_SPORTVU_FGA[team['TEAM']] = team

    return TEAM_SPORTVU_FGA

def get_team_depth_chart(team, out_players):
    ALL_TEAM_PLAYERS[team] = {
        'by_role': {
            'starters':[],
            'rotation':[],
            'limited':[]
        },
        'out_players': {
            'PG':[],
            'SG':[],
            'SF':[],
            'PF':[],
            'C':[]
        },
        'players': {},
        'by_rotation': {
            'C': {
                'starters': {
                    'players': [],
                    'rotation': {
                        'players': [],
                        'limited': {
                            'players': []
                        }
                    }
                }
            },
            'PG': {
                'starters': {
                    'players': [],
                    'rotation': {
                        'players': [],
                        'limited': {
                            'players': []
                        }
                    }
                }
            },
            'SG': {
                'starters': {
                    'players': [],
                    'rotation': {
                        'players': [],
                        'limited': {
                            'players': []
                        }
                    }
                }
            },
            'SF': {
                'starters': {
                    'players': [],
                    'rotation': {
                        'players': [],
                        'limited': {
                            'players': []
                        }
                    }
                }
            },
            'PF': {
                'starters': {
                    'players': [],
                    'rotation': {
                        'players': [],
                        'limited': {
                            'players': []
                        }
                    }
                }
            }
        },
        'all_players': [],
        'sql_players': [],
        'all_rotation_players': [],
    }

    sql_team = team
    if team in TRANSLATE_DICT:
        sql_team = TRANSLATE_DICT[team]

    last_one_playtime = get_last_game(sql_team, 1)

    OBVIOUS_OUTS['by_team'][sql_team] = []
    OBVIOUS_OUTS['by_position'][sql_team] = {}

    # print team
    with open('../scrape/misc/updated_depth_chart/'+team+'.json') as data_file:
        data = json.load(data_file)
        positions = ['PG', 'SG', 'SF', 'PF', 'C']
        for position in positions:
            depth = data[position]
            ALL_TEAM_PLAYERS[team]['players'][position] = {}
            OBVIOUS_OUTS['by_position'][sql_team][position] = []

            for player in depth:
                player_name = player['player']
                player_role = player['role']

                # translate name appropriately for DK
                sql_name = player_name

                if player_name in news_scraper.DEPTH_TO_DK_TRANSLATE:
                    player_name = news_scraper.DEPTH_TO_DK_TRANSLATE[player_name]
                    sql_name = player_name

                if player_name in news_scraper.DK_TO_SQL_TRANSLATE:
                    sql_name = news_scraper.DK_TO_SQL_TRANSLATE[player_name]
    
                # print out_players
                # print sql_name
                if player['role'] == 'Starters' and \
                    sql_name in out_players:
                    OBVIOUS_OUTS['by_team'][sql_team].append(sql_name)
                    OBVIOUS_OUTS['players'].append(sql_name)
                    OBVIOUS_OUTS['by_position'][sql_team][position].append(sql_name)

                if player['role'] == 'Starters' and \
                    sql_name not in out_players:


                    # remove those that are OUT_FOR_SEASON and didn't play last game (assumed already done)
                    # since the depth chart might have not been updated
                    
                    # if they played last game but are now out for season they should still be counted

                    if sql_name in last_one_playtime or sql_name not in OUT_FOR_SEASON:

                        ALL_TEAM_PLAYERS[team]['by_role']['starters'].append(sql_name)
                        ALL_TEAM_PLAYERS[team]['by_rotation'][position]['starters']['players'].append(player_name)
                        ALL_TEAM_PLAYERS[team]['all_rotation_players'].append(sql_name)
                
                if player['role'] == 'Rotation' and \
                    sql_name in out_players:

                    OBVIOUS_OUTS['by_team'][sql_team].append(sql_name)
                    OBVIOUS_OUTS['by_position'][sql_team][position].append(sql_name)

                if player['role'] == 'Rotation' and \
                    sql_name not in out_players:
                    
                    if sql_name in last_one_playtime or sql_name not in OUT_FOR_SEASON:

                        ALL_TEAM_PLAYERS[team]['by_role']['rotation'].append(sql_name)
                        ALL_TEAM_PLAYERS[team]['by_rotation'][position]['starters']['rotation']['players'].append(player_name)
                        ALL_TEAM_PLAYERS[team]['all_rotation_players'].append(sql_name)

                if player['role'] == 'Lim PT' and \
                    sql_name not in out_players:

                    if sql_name in last_one_playtime or sql_name not in OUT_FOR_SEASON:

                        ALL_TEAM_PLAYERS[team]['by_role']['limited'].append(sql_name)
                        ALL_TEAM_PLAYERS[team]['by_rotation'][position]['starters']['rotation']['limited']['players'].append(player_name)

                ALL_TEAM_PLAYERS[team]['players'][position][player_name] = {
                    'name': player_name,
                    'role': player_role
                }

                ALL_TEAM_PLAYERS[team]['all_players'].append(player_name)
                ALL_TEAM_PLAYERS[team]['sql_players'].append(sql_name)

                PLAYER_POSITIONS[sql_name] = position
    # print ALL_TEAM_PLAYERS
    return ALL_TEAM_PLAYERS

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

# number of lineups in, price point and also medium case scenario?

def process_pre_post_injury_depth_chart(team, out_players):
    # right now the difference is in the 'by_rotation' key
    depth_team = team
    if team in news_scraper.REVERSE_TRANSLATE_DICT:
        depth_team = news_scraper.REVERSE_TRANSLATE_DICT[team]

    normal_roster = get_team_depth_chart(depth_team, [])[depth_team]['by_rotation']
    injured_roster = get_team_depth_chart(depth_team, out_players)[depth_team]['by_rotation']

    # pp.pprint(normal_roster)
    # pp.pprint(injured_roster)
    step_up_players = {}
    for position, players in injured_roster.iteritems():
        # lets compares the # of players missing from each rank 
        for secondary_position in SECONDARY_BENEFITS[position]:

        # secondary_position = SECONDARY_BENEFITS[position]
            # print secondary_position
            if len(normal_roster[position]['starters']['players']) != len(players['starters']['players']):

                if len(players['starters']['rotation']['players']) == 0 and \
                    len(players['starters']['players']) == 0:
                    # get the nearest secondary
                    print injured_roster[secondary_position]['starters']['rotation']['players']
                    for rotation_player in injured_roster[secondary_position]['starters']['rotation']['players']:
                        # translate name appropriately for DK
                        sql_name = rotation_player

                        if rotation_player in news_scraper.DEPTH_TO_DK_TRANSLATE:
                            rotation_player = news_scraper.DEPTH_TO_DK_TRANSLATE[rotation_player]
                            sql_name = rotation_player

                        if rotation_player in news_scraper.DK_TO_SQL_TRANSLATE:
                            sql_name = news_scraper.DK_TO_SQL_TRANSLATE[rotation_player]
                        
                        step_up_players[sql_name] = {
                            'player_name': sql_name,
                            'position': position,
                            'diff': 0
                        }

                    for rotation_player in injured_roster[secondary_position]['starters']['players']:
                        # translate name appropriately for DK
                        sql_name = rotation_player

                        if rotation_player in news_scraper.DEPTH_TO_DK_TRANSLATE:
                            rotation_player = news_scraper.DEPTH_TO_DK_TRANSLATE[rotation_player]
                            sql_name = rotation_player

                        if rotation_player in news_scraper.DK_TO_SQL_TRANSLATE:
                            sql_name = news_scraper.DK_TO_SQL_TRANSLATE[rotation_player]
                        
                        step_up_players[sql_name] = {
                            'player_name': sql_name,
                            'position': position,
                            'diff': 0
                        }


                if len(players['starters']['rotation']['players']) >= 1:
                    for rotation_player in players['starters']['rotation']['players']:
                        # translate name appropriately for DK
                        sql_name = rotation_player

                        if rotation_player in news_scraper.DEPTH_TO_DK_TRANSLATE:
                            rotation_player = news_scraper.DEPTH_TO_DK_TRANSLATE[rotation_player]
                            sql_name = rotation_player

                        if rotation_player in news_scraper.DK_TO_SQL_TRANSLATE:
                            sql_name = news_scraper.DK_TO_SQL_TRANSLATE[rotation_player]
                        
                        step_up_players[sql_name] = {
                            'player_name': sql_name,
                            'position': position,
                            'diff': abs(len(normal_roster[position]['starters']['players']) - len(players['starters']['players']))
                        }

                    for rotation_player in injured_roster[secondary_position]['starters']['rotation']['players']:
                        # translate name appropriately for DK
                        sql_name = rotation_player

                        if rotation_player in news_scraper.DEPTH_TO_DK_TRANSLATE:
                            rotation_player = news_scraper.DEPTH_TO_DK_TRANSLATE[rotation_player]
                            sql_name = rotation_player

                        if rotation_player in news_scraper.DK_TO_SQL_TRANSLATE:
                            sql_name = news_scraper.DK_TO_SQL_TRANSLATE[rotation_player]
                        
                        step_up_players[sql_name] = {
                            'player_name': sql_name,
                            'position': position,
                            'diff': 0
                        }

                    for rotation_player in injured_roster[secondary_position]['starters']['players']:
                        # translate name appropriately for DK
                        sql_name = rotation_player

                        if rotation_player in news_scraper.DEPTH_TO_DK_TRANSLATE:
                            rotation_player = news_scraper.DEPTH_TO_DK_TRANSLATE[rotation_player]
                            sql_name = rotation_player

                        if rotation_player in news_scraper.DK_TO_SQL_TRANSLATE:
                            sql_name = news_scraper.DK_TO_SQL_TRANSLATE[rotation_player]
                        
                        step_up_players[sql_name] = {
                            'player_name': sql_name,
                            'position': position,
                            'diff': 0
                        }
                else:
                    for rotation_player in players['starters']['rotation']['limited']['players']:
                        # translate name appropriately for DK
                        sql_name = rotation_player

                        if rotation_player in news_scraper.DEPTH_TO_DK_TRANSLATE:
                            rotation_player = news_scraper.DEPTH_TO_DK_TRANSLATE[rotation_player]
                            sql_name = rotation_player

                        if rotation_player in news_scraper.DK_TO_SQL_TRANSLATE:
                            sql_name = news_scraper.DK_TO_SQL_TRANSLATE[rotation_player]
                        
                        step_up_players[sql_name] = {
                            'player_name': sql_name,
                            'position': position,
                            'diff': abs(len(normal_roster[position]['starters']['rotation']['players']) - len(players['starters']['rotation']['players']))
                        }

        # if a rotation player is missing then we power up the starters
        # if len(normal_roster[position]['starters']['rotation']['players']) != len(players['starters']['rotation']['players']):
            
        #     for starter in players['starters']['players']:
        #         # translate name appropriately for DK
        #         sql_name = starter

        #         if starter in news_scraper.DEPTH_TO_DK_TRANSLATE:
        #             starter = news_scraper.DEPTH_TO_DK_TRANSLATE[starter]
        #             sql_name = starter

        #         if starter in news_scraper.DK_TO_SQL_TRANSLATE:
        #             sql_name = news_scraper.DK_TO_SQL_TRANSLATE[starter]
                
        #         step_up_players[sql_name] = {
        #             'player_name': sql_name,
        #             'position': position,
        #             'diff': abs(len(normal_roster[position]['starters']['rotation']['players']) - len(players['starters']['rotation']['players'])) 
        #         }

    # what is the usg of the guy that is out? then who is the next highest on usg on the team, they will get boosted
    # pp.pprint(step_up_players)
    return step_up_players

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


def lineup_diff_w_l(sql_team):
    lineup_obj = {}

    for result in ['W', 'L']:

        lineup_obj[result] = {}
        # get_game_id_by_result

        game_id_by_result = sqlfetch.execute_query(sqlfetch.get_game_id_by_result(sql_team, FIRST_DATE_REG_SEASON, result))

        for game in game_id_by_result:

            # create a list of players that played that game
            players_played = []

            # but what if the player didn't play, so lets account for that
            lineups_used = sqlfetch.execute_query(sqlfetch.get_lineup_by_team(game['GAME_ID'], sql_team))

            for lineup in lineups_used:
                key_list = ['PLAYER_1', 'PLAYER_2', 'PLAYER_3', 'PLAYER_4', 'PLAYER_5']

                for key_marker in key_list:
                    player = lineup[key_marker]

                    if player not in players_played:
                        players_played.append(player)

                    if player not in lineup_obj[result]:
                        lineup_obj[result][player] = {
                            'possessions': lineup['POSSESSIONS'],
                            'minutes_played': lineup['MINUTES_PLAYED'],
                            'games_played': 0
                        }
                    else:
                        lineup_obj[result][player]['possessions'] += lineup['POSSESSIONS']
                        lineup_obj[result][player]['minutes_played'] += lineup['MINUTES_PLAYED']

            for player in players_played:
                lineup_obj[result][player]['games_played'] += 1



    for result, player in lineup_obj.iteritems():
        for player_name, stats in player.iteritems():
            stats['pct_played'] = news_scraper.two_decimals(float(stats['possessions']) / float(stats['games_played']))

    simp_diff_obj = {}
    # but what if they only played in games that they lost ?
    for player_name, stats in lineup_obj['W'].iteritems():
        if player_name in lineup_obj['L']:
            simp_diff_obj[player_name] = news_scraper.two_decimals(stats['pct_played'] - lineup_obj['L'][player_name]['pct_played'])
        else:
            simp_diff_obj[player_name] = 100

    # simp_diff_obj = sorted(simp_diff_obj.iteritems(), key=lambda x: x[1], reverse=True)

    return simp_diff_obj

def safe_div(x,y):
    if y == 0:
        return 0
    return x / y


def get_simple_projections(team, usg_line_up_summary, this_year_player_summary_object, team_total_poss_played_this_year, games_player_played, min_lineup_by_game):
    # for these players
    team_proj_obj = {}
    sql_team = team
    if team in TRANSLATE_DICT:
        sql_team = TRANSLATE_DICT[team]

    # this is from wowy (usg_line_up_summary)... 
    for player_name, stats in usg_line_up_summary[team].iteritems():

        sql_player = player_name
        dk_player_name = player_name
        if sql_player in news_scraper.WOWY_TO_SQL_TRANSLATE:
            sql_player = news_scraper.WOWY_TO_SQL_TRANSLATE[player_name]

        if dk_player_name in news_scraper.WOWY_TO_DK_TRANSLATE:
            dk_player_name = news_scraper.WOWY_TO_DK_TRANSLATE[player_name]
        # Frank mason
        # print sql_player

        # frank mason III
        # print ALL_TEAM_PLAYERS[team]['all_players']

        # sql to dk
        # only for those that are on the roster
        # checking for DK names
 

        if dk_player_name in ALL_TEAM_PLAYERS[team]['all_players']:

            if player_name in news_scraper.DK_TO_SQL_TRANSLATE:
                sql_player = news_scraper.DK_TO_SQL_TRANSLATE[player_name]

            if player_name in news_scraper.WOWY_TO_SQL_TRANSLATE:
                sql_player = news_scraper.WOWY_TO_SQL_TRANSLATE[player_name]

            if player_name in news_scraper.WOWY_TO_DK_TRANSLATE:
                dk_name = news_scraper.WOWY_TO_DK_TRANSLATE[player_name]
            else:
                dk_name = player_name

            # one to note is that the dkm is only from the top n number of lineups. not ALL of the lineups

            # whats the avg line up distribution for the team?
            num_lineups = len(stats['dkm'])
            projection_based_past_pct = {}
            min_used_pct = {}
            projection_based_past_pct[player_name] = []
            min_used_pct[player_name] = []

            for game_id, min_list in min_lineup_by_game.iteritems():
                # only used the ids for the games the player played
                if game_id in games_player_played[sql_player]:
                    est = 0
                    player_min_used_for_proj = 0
                    for s, p in zip(stats['dkm'], min_list):
                        est += s * p
                        if s != 0:
                            player_min_used_for_proj += p
                    # dkm * minutes played based on approx lineups played
                    projection_based_past_pct[player_name].append(est)
                    min_used_pct[player_name].append(player_min_used_for_proj)

            if player_name in this_year_player_summary_object:
                median_approx = news_scraper.two_decimals(np.median(stats['dkm']) * float(this_year_player_summary_object[player_name]['possessions']) / float(team_total_poss_played_this_year) * 48)
                max_approx = news_scraper.two_decimals(np.max(stats['dkm']) * float(this_year_player_summary_object[player_name]['possessions']) / float(team_total_poss_played_this_year) * 48)


                try:
                    value_goal = float(DK_MONEY_OBJ[dk_name]['salary']) / 1000 * 6
                except KeyError:
                    value_goal = 35
                    print dk_name


                if len(min_used_pct[player_name]) == 0:
                    min_used_pct[player_name] = [0]
                    projection_based_past_pct[player_name] = [0]

                # store the lineup based median approx in a dict
                projection_based_past_pct[player_name] = np.nan_to_num(projection_based_past_pct[player_name])
                min_used_pct[player_name] = np.nan_to_num(min_used_pct[player_name])
                lineup_based_dkm_proj_med = np.median(projection_based_past_pct[player_name])
                min_used_med = np.median(min_used_pct[player_name])
                min_used_max = np.max(min_used_pct[player_name])
                lineup_based_dkm_proj_max = np.max(projection_based_past_pct[player_name])

                # est an avg case for the player where the avg med dkm * avg min played
                approx_avg_time_lineup_med = news_scraper.two_decimals(safe_div(lineup_based_dkm_proj_med, min_used_med) * (48 * PLAYER_AVG_PLAYTIME[sql_player] / 100))
                approx_avg_time_lineup_max = news_scraper.two_decimals(safe_div(lineup_based_dkm_proj_max, min_used_max) * (48 * PLAYER_AVG_PLAYTIME[sql_player] / 100))
                approx_avg_time_lineup_med_36 = news_scraper.two_decimals(safe_div(lineup_based_dkm_proj_max, min_used_max) * 36)

                approx_lineup_max = np.max([lineup_based_dkm_proj_max, approx_avg_time_lineup_max])
                lineup_based_points_basis = value_goal - approx_avg_time_lineup_med


                # pick whichever one is higher for abs max conditions
                if approx_avg_time_lineup_med > 0 or \
                    approx_lineup_max > 0 or \
                    approx_avg_time_lineup_med_36 > 0:

                    team_proj_obj[sql_player] = {
                        'median': approx_avg_time_lineup_med,
                        'median36': approx_avg_time_lineup_med_36,
                        'max': approx_lineup_max,
                        'value_goal': value_goal,
                        'points_basis' : lineup_based_points_basis,
                        'team': sql_team

                    }


                    LINEUP_BASED_PROJ[sql_player] = {
                        'median': approx_avg_time_lineup_med,
                        'median36': approx_avg_time_lineup_med_36,
                        'max': approx_lineup_max,
                        'value_goal': value_goal,
                        'points_basis' : lineup_based_points_basis,
                        'team': sql_team
                    }

    lbp = sorted(team_proj_obj.iteritems(), key=lambda x: x[1]['median'], reverse=True)

    for idx, player in enumerate(lbp):
        print '(+/- 3) MED: {median_approx},  MED36: {median_36},  MAX: {max_approx}  -  NEED: {value_goal}  ({player_name})'.format(\
               player_name=player[0], median_approx=player[1]['median'], median_36=player[1]['median36'], max_approx=player[1]['max'], value_goal=player[1]['value_goal']
            )

        LINEUP_BASED_PROJ[player[0]]['rank']  = idx+1

    return LINEUP_BASED_PROJ

    # we should sort this
# return temp_player_lineup_usg

def process_last_year_team_lineups(team, last_year_lineup_played_against_team, last_year_lineup_summary_object, \
        team_players_obj, team_totals_last_year):
    
    for last_year_lineup in last_year_lineup_played_against_team:
        key_list = ['PLAYER_1', 'PLAYER_2', 'PLAYER_3', 'PLAYER_4', 'PLAYER_5']
        last_year_on_players = []

        for key_marker in key_list:
            if last_year_lineup[key_marker] in news_scraper.SQL_TO_WOWY_TRANSLATE:
                player_key_name = news_scraper.SQL_TO_WOWY_TRANSLATE[last_year_lineup[key_marker]]
            else:
                player_key_name = last_year_lineup[key_marker]
            
            last_year_on_players.append(player_key_name)

            if player_key_name in news_scraper.WOWY_TO_DK_TRANSLATE:
                dk_player_name = news_scraper.WOWY_TO_DK_TRANSLATE[player_key_name]
            else:
                dk_player_name = player_key_name

            if dk_player_name in ALL_TEAM_PLAYERS[team]['all_players'] \
                and dk_player_name in DK_MONEY_OBJ \
                and last_year_lineup[key_marker] not in OUT_PLAYERS:
                if player_key_name not in team_players_obj:
                    team_players_obj[player_key_name] = {
                        'possessions': last_year_lineup['POSSESSIONS'],
                        'minutes_played': last_year_lineup['MINUTES_PLAYED']
                    }

                    if dk_player_name in DK_MONEY_OBJ:
                        team_players_obj[player_key_name]['val'] = news_scraper.two_decimals(DK_MONEY_OBJ[dk_player_name]['avg_val'])
                        team_players_obj[player_key_name]['salary'] = DK_MONEY_OBJ[dk_player_name]['salary']

                else:
                    team_players_obj[player_key_name]['possessions'] += last_year_lineup['POSSESSIONS'] 
                    team_players_obj[player_key_name]['minutes_played'] += last_year_lineup['MINUTES_PLAYED']


        last_year_lineup_str = ', '.join(sorted(last_year_on_players))
        team_totals_last_year['team_total_poss_played'] += last_year_lineup['POSSESSIONS']
        team_totals_last_year['team_total_min_played'] += last_year_lineup['MINUTES_PLAYED']
        # there could be repeated lineups here
        last_year_lineup_summary_object[last_year_lineup_str] = {
            'possessions': last_year_lineup['POSSESSIONS'],
            'minutes_played': last_year_lineup['MINUTES_PLAYED']
        }

        for player_key_name, lineup_stats in team_players_obj.iteritems():
            lineup_stats['pct_poss'] = news_scraper.two_decimals(lineup_stats['possessions'] / team_totals_last_year['team_total_poss_played'] * 100)
            lineup_stats['pct_min'] = news_scraper.two_decimals(lineup_stats['minutes_played'] / team_totals_last_year['team_total_min_played'] * 100)


def process_all_team_lineups(all_possible_lineups, team_totals_this_year):

    # change this to get all lineups
    for possible_lineup in all_possible_lineups:
        key_list = ['PLAYER_1', 'PLAYER_2', 'PLAYER_3', 'PLAYER_4', 'PLAYER_5']
        on_players = []
        for key_marker in key_list:
            # on_players.append(possible_lineup[key_marker])
            if possible_lineup[key_marker] in news_scraper.SQL_TO_WOWY_TRANSLATE:
                on_players.append(news_scraper.SQL_TO_WOWY_TRANSLATE[possible_lineup[key_marker]])
            else:
                on_players.append(possible_lineup[key_marker])

        # for each player whats the total % of possessions they play on avg
        for player in on_players:
            if player not in OUT_PLAYERS:
                if player not in team_totals_this_year['this_year_player_summary_object']:
                    team_totals_this_year['this_year_player_summary_object'][player] = {
                        'possessions': possible_lineup['POSSESSIONS'],
                        'minutes_played': possible_lineup['MINUTES_PLAYED']
                    }
                else:
                    team_totals_this_year['this_year_player_summary_object'][player]['possessions'] += possible_lineup['POSSESSIONS']
                    team_totals_this_year['this_year_player_summary_object'][player]['minutes_played'] += possible_lineup['MINUTES_PLAYED']


        sorted_on_players = sorted(on_players)
        on_players_str = ', '.join(sorted_on_players)
        team_totals_this_year['team_total_poss_played_this_year'] += possible_lineup['POSSESSIONS']
        team_totals_this_year['team_total_min_played_this_year'] += possible_lineup['MINUTES_PLAYED']

        if on_players_str not in team_totals_this_year['this_year_lineup_summary_object']:
            team_totals_this_year['this_year_lineup_summary_object'][on_players_str] = {
                'possessions': possible_lineup['POSSESSIONS'],
                'minutes_played': possible_lineup['MINUTES_PLAYED']
            }
        else:
            team_totals_this_year['this_year_lineup_summary_object'][on_players_str]['possessions'] += possible_lineup['POSSESSIONS']
            team_totals_this_year['this_year_lineup_summary_object'][on_players_str]['minutes_played'] += possible_lineup['MINUTES_PLAYED']


def get_projection_last_game_lineup(sql_team, lineup_summary_object):

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
    
    estimate_dk_object = sorted(estimate_dk_object.iteritems(), key=lambda x: x[1], reverse=True)

    return estimate_dk_object

def get_last_year_matchups(team, sql_team, sql_oppo):
    team_last_year_games = sqlfetch.execute_query(sqlfetch.get_team_faced(sql_team, sql_oppo, LAST_YEAR_FIRST_DATE_REG_SEASON))

    # print team_last_game_id
    game_ids = []
    for game in team_last_year_games:
        game_ids.append(game['GAME_ID'])

    game_ids = '", "'.join(game_ids)
    last_year_lineup_played_against_team = sqlfetch.execute_query(sqlfetch.get_lineup_played_against_team(game_ids, sql_oppo, '2016'))
    last_year_lineup_summary_object = {}
    team_totals_last_year = {
        'team_total_poss_played': 0,
        'team_total_min_played' : 0,
    }

    team_players_obj = {}

    # process last years lineups
    process_last_year_team_lineups(team, last_year_lineup_played_against_team, last_year_lineup_summary_object, \
        team_players_obj, team_totals_last_year)

    sorted_last_year_player_summary_object = sorted(team_players_obj.iteritems(), key=lambda x: x[1]['pct_min'], reverse=True)

    print 'FROM LAST YEARS MATCHUPS VS %s' % sql_oppo

    for obj in sorted_last_year_player_summary_object:
        print '{player} - {pct_min}% / {minutes_played}m'.format(\
            player=obj[0], pct_min=obj[1]['pct_min'], minutes_played=obj[1]['minutes_played'])

def process_playtime(record):
    playtime = record.split(':')

    return news_scraper.two_decimals(float((float(playtime[0])*60 + float(playtime[1])) / 60))

def get_last_n_game_dk(player_name, n):

    # dk_pts_list = []
    dk_game_obj = []
        # 'dk_points': [],
        # 'diff': []
    # }
    # print sqlfetch.player_last_game(player_name, n, False)
    last_n_games = sqlfetch.execute_query(sqlfetch.player_last_game(player_name, n, False))
    for game in last_n_games:
        # dk_game_obj['dk_points'].append(game['DK_POINTS'])
        # dk_game_obj['diff'].append(game['PLUS_MINUS'])
        dk_game_obj.append({
            'dk_points': game['DK_POINTS'],
            'diff': game['PLUS_MINUS'],
            'usg': game['USG_PCT'],
            'min': game['MIN']
        })
    return dk_game_obj

# print get_last_n_game_dk('Dennis Schroder', 3)

def get_last_n_game_usg(team, player_name, n):


    game_id_by_result = sqlfetch.execute_query(sqlfetch.get_player_games_played(player_name, team, FIRST_DATE_REG_SEASON, n))
    usg_list = []
    for game in game_id_by_result:
        player = sqlfetch.execute_query(sqlfetch.get_game_usg(game['GAME_ID'], team, player_name))
        try:
            usg_list.append(player[0]['USG_PCT']*100)
        except IndexError:
            pass

    return usg_list

def get_last_game_starters(team):

    last_game_starters = {}
    game_id_by_result = sqlfetch.execute_query(sqlfetch.get_last_n_game_id(team, 1))
    lineup_obj = {}
    for game in game_id_by_result:
        starters = sqlfetch.execute_query(sqlfetch.get_game_starters(game['game_id'], team))

        for starter in starters:
            last_game_starters[starter['PLAYER_NAME']] = {
                'name': starter['PLAYER_NAME'],
                'minutes_played': process_playtime(starter['MIN']),
                'usg_pct': news_scraper.two_decimals(float(starter['USG_PCT']) * 100)
            }
            
    return last_game_starters


def get_last_game(team, n):

    last_game_starters = {}
    game_id_by_result = sqlfetch.execute_query(sqlfetch.get_last_n_game_id(team, n))
    player_obj = {}
    for game in game_id_by_result:
        players = sqlfetch.execute_query(sqlfetch.get_game_usg_team(game['game_id'], team))

        for player in players:

            if player['PLAYER_NAME'] not in player_obj:
                player_obj[player['PLAYER_NAME']] = {
                    'name': player['PLAYER_NAME'],
                    'minutes_played': [process_playtime(player['MIN'])],
                    'minutes_played_raw': [process_playtime(player['MIN'])],
                }
            else:
                player_obj[player['PLAYER_NAME']]['minutes_played'].append(process_playtime(player['MIN']))
                player_obj[player['PLAYER_NAME']]['minutes_played_raw'].append(process_playtime(player['MIN']))

    for player_name, minutes_played in player_obj.iteritems():
        player_obj[player_name]['minutes_played'] = news_scraper.two_decimals(np.median(minutes_played['minutes_played']))

    return player_obj

def get_games_from_inactives(team):
    # init_out_players()

    out_from_team = OUT_LIST[team] + TRADED_LIST[team] + OUT_FOR_SEASON
    games_from_inactives = sqlfetch.execute_query(sqlfetch.get_games_from_inactives(out_from_team, team))
    game_played = []

    for game in games_from_inactives:

        if game["NUM_GAMES"] == len(OUT_LIST[team]) or game["NUM_GAMES"] == len(OUT_LIST[team]) - 1:

            players = sqlfetch.execute_query(sqlfetch.get_game_usg_team(game['GAME_ID'], team))
            game_obj = {}
            for player in players:
                if player['START_POSITION'] != '':
                    # by game?
                    game_obj[player['PLAYER_NAME']] = {
                        'name': player['PLAYER_NAME'],
                        'usg_pct': news_scraper.two_decimals(float(player['USG_PCT']) * 100),
                        'minutes_played': process_playtime(player['MIN'])
                    }
            game_played.append(game_obj)

    return game_played



def print_depth_chart(sql_team):

    depth_team = sql_team
    if sql_team in news_scraper.REVERSE_TRANSLATE_DICT:
        depth_team = news_scraper.REVERSE_TRANSLATE_DICT[sql_team]

    TEAM_DEPTH_COUNT[sql_team] = {}

    starting_players = []
    for position, role in ALL_TEAM_PLAYERS[depth_team]['by_rotation'].iteritems():
        TEAM_DEPTH_COUNT[sql_team][position] = []

        depth_starters = role['starters']
        rotations = depth_starters['rotation']
        if len(depth_starters['players']) >= 1:
            starting_players.append(depth_starters['players'][0])
            TEAM_DEPTH_COUNT[sql_team][position].append(depth_starters['players'][0])
            
            print '{position}: {role}'.format(position=position, role=depth_starters['players'][0])

        elif (len(rotations['players']) >= 1):
            starting_players.append(rotations['players'][0])
            TEAM_DEPTH_COUNT[sql_team][position].append(rotations['players'][0])

            DIRECT_POSITION_REPLACEMENT_PLAYERS.append(rotations['players'][0])
            print '{position}: {role}'.format(position=position, role=rotations['players'][0])
        else:
            try: 
                starting_players.append(rotations['limited']['players'][0])
                TEAM_DEPTH_COUNT[sql_team][position].append(rotations['limited']['players'][0])

                DIRECT_POSITION_REPLACEMENT_PLAYERS.append(rotations['players'][0])
                print '{position}: {role}'.format(position=position, role=rotations['limited']['players'][0])

            except IndexError:
                print '{position}: N/A'.format(position=position)

        if len(rotations['players']) >= 1:
            for player in rotations['players']:
                if player not in starting_players:
                    starting_players.append(player)

                if player not in TEAM_DEPTH_COUNT[sql_team][position]:
                    TEAM_DEPTH_COUNT[sql_team][position].append(player)

                    print '- %s' % player
        if len(rotations['limited']['players']) >= 1:
            for player in rotations['limited']['players']:
                if player not in TEAM_DEPTH_COUNT[sql_team][position]:
                    TEAM_DEPTH_COUNT[sql_team][position].append(player)
                    print '-- %s' % player
                
    print '\n'

    return list(set(starting_players))

# 
def get_possible_lineups(team, oppo):

    sql_team = team
    sql_oppo = oppo
    if team in TRANSLATE_DICT:
        sql_team = TRANSLATE_DICT[team]
    if oppo in TRANSLATE_DICT:
        sql_oppo = TRANSLATE_DICT[oppo]

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

    # lineups
    key_list = ['PLAYER_1', 'PLAYER_2', 'PLAYER_3', 'PLAYER_4', 'PLAYER_5']

    # replacement lineups
    top_lineup = sqlfetch.execute_query(sqlfetch.get_lineup_from_absence([], sql_team, 2))
                
    num_line_ups = 10

    out_from_team = OUT_PLAYERS + TRADED_LIST[sql_team]
    DIFF_INJURY_LINEUPS[sql_team] = get_lineup_diff(out_from_team, sql_team)
    
    # print out_from_team
    possible_lineups = sqlfetch.execute_query(sqlfetch.get_lineup_from_absence(out_from_team, sql_team, num_line_ups))
    all_possible_lineups = sqlfetch.execute_query(sqlfetch.get_lineup_from_absence([], sql_team, None))
    team_lineup_game_logs = sqlfetch.execute_query(sqlfetch.get_team_lineup_game_logs(sql_team))

    min_lineup_by_game = {}

    for lineup_data in team_lineup_game_logs:
        game_id = lineup_data['GAME_ID']

        if game_id not in min_lineup_by_game:
            min_lineup_by_game[game_id] = [int(lineup_data['MINUTES_PLAYED'])]
        else:
            min_lineup_by_game[game_id].append(int(lineup_data['MINUTES_PLAYED']))

    top_players = []
    replacement_players = []
    for top, replacement in zip(top_lineup, possible_lineups[0:2:1]):
        for key_marker in key_list:

            if top[key_marker] not in top_players:
                top_players.append(top[key_marker])

            if replacement[key_marker] not in replacement_players:
                replacement_players.append(replacement[key_marker])

    diff_lineup = list(set(top_players).symmetric_difference(set(replacement_players)))


    global OPPORTUNITY_PLAYERS
    OPPORTUNITY_PLAYERS += diff_lineup

    print '%s Data' % sql_team

    # simp_diff_obj = lineup_diff_w_l(sql_team)
    usg_line_up_summary = {}
    usg_line_up_summary[team] = {}

    last_usg_line_up_summary = {}
    last_usg_line_up_summary[team] = {}

    player_summary_object = {}
    last_lineup_summary_object = {}
    player_matchups_list = []


    # last years matchups
    # get_last_year_matchups(team, sql_team, sql_oppo)


    # # get all current players on the team who aren't Injured
    # wowy_off_players = []
    games_player_played = {}
    for position, position_players in ALL_TEAM_PLAYERS[team]['players'].iteritems():
        for player_name, job in position_players.iteritems():
            if player_name in news_scraper.DK_TO_SQL_TRANSLATE:
                player_name = news_scraper.DK_TO_SQL_TRANSLATE[player_name]
            
            games_player_played[player_name] = {}

            # get all games played by player
            games_played = sqlfetch.execute_query(sqlfetch.get_player_games_played(player_name, sql_team, FIRST_DATE_REG_SEASON, 0))

            for each_game in games_played:
                games_player_played[player_name][each_game['GAME_ID']] = each_game

            # if player_name in OUT_PLAYERS:
            #     if player_name in news_scraper.SQL_TO_WOWY_TRANSLATE:
            #         wowy_off_players.append(news_scraper.SQL_TO_WOWY_TRANSLATE[player_name])
            #     else:
            #         wowy_off_players.append(player_name)

    # to get it accurate need also previous team
    # last_season_against_team = news_scraper.player_on_off(WOWY_TEAMS[team], [WOWY_TEAMS[oppo]], [], wowy_off_players, '2016-10-26', LAST_DATE_REG_SEASON)
   

    # if there is a difference its when there is an injured starter
    if len(diff_lineup) >= 1:
        POSSIBLE_LINEUP[sql_team] = ', '.join(replacement_players)
    else:
        POSSIBLE_LINEUP[sql_team] = ', '.join(top_players)    

    # for the last player_summary_object add some information to this years
    print '\n'
    print 'LINEUPS (ALL)'

    # need to account for only the games that the player played in
    team_totals_this_year = {
        'team_total_poss_played_this_year': 0,
        'team_total_min_played_this_year' : 0,
        'this_year_lineup_summary_object' : {},
        'this_year_player_summary_object' : {}
    }

    # process all the lineups
    process_all_team_lineups(all_possible_lineups, team_totals_this_year)

    sorted_this_year_player_summary_object = sorted(team_totals_this_year['this_year_player_summary_object'].iteritems(), key=lambda x: x[1]['possessions'], reverse=True)
    for player in sorted_this_year_player_summary_object:
        dk_player_name = player[0]
        sql_player = player[0]
        wowy_name = player[0]
        depth_name = player[0]

        if wowy_name in news_scraper.WOWY_TO_DK_TRANSLATE:
            dk_player_name = news_scraper.WOWY_TO_DK_TRANSLATE[wowy_name]

        if wowy_name in news_scraper.WOWY_TO_SQL_TRANSLATE:
            sql_player = news_scraper.WOWY_TO_SQL_TRANSLATE[wowy_name]

        if dk_player_name in ALL_TEAM_PLAYERS[team]['all_players']:
            # print "name in all team"
            player_pf = sqlfetch.execute_query(sqlfetch.get_player_pf(FIRST_DATE_REG_SEASON, sql_player))

            poss_played = news_scraper.two_decimals(float(player[1]['possessions']) / float(team_totals_this_year['team_total_poss_played_this_year']) * 100)
            # min_played = news_scraper.two_decimals(float(player[1]['minutes_played']) / float(team_total_min_played_this_year) * 100)
            PLAYER_AVG_PLAYTIME[sql_player] = poss_played

            # if sql_player in simp_diff_obj:
            #     wvl = simp_diff_obj[sql_player]
            # else:
            #     wvl = 'N/A' 

            if poss_played >= 5:
                print '{player} POSS: {poss_played}%'.format(player=sql_player, poss_played=poss_played)
                print 'PFD: {pfd}, PF: {pf}'.format(pfd=player_pf[0]['AVG_PFD'], pf=player_pf[0]['AVG_PF'])

                if dk_player_name in DK_MONEY_OBJ:
                    for position in DK_MONEY_OBJ[dk_player_name]['positions']:
                        player_matchups_list = ', '.join(ALL_TEAM_PLAYERS[oppo]['players'][position].keys())

                        avg_rating_faced = []
                        for player in ALL_TEAM_PLAYERS[oppo]['players'][position].keys():
                            sql_name = player
                            if player in news_scraper.DEPTH_TO_DK_TRANSLATE:
                                player = news_scraper.DEPTH_TO_DK_TRANSLATE[player]

                            if player in news_scraper.DK_TO_SQL_TRANSLATE:
                                sql_name = news_scraper.DK_TO_SQL_TRANSLATE[player]
                            # get the sql names
                            try:
                                opp_role = sqlfetch.execute_query(sqlfetch.get_player_roles_by_name(sql_name))[0]['ROLE']

                                if opp_role == 'Starters' or opp_role == 'Rotation':
                                    if sql_name in PLAYER_ADV_STATS and sql_name not in OUT_PLAYERS:
                                        opp_pf = sqlfetch.execute_query(sqlfetch.get_player_pf(FIRST_DATE_REG_SEASON, sql_name))
                                        avg_rating_faced.append(PLAYER_ADV_STATS[sql_name]['DEF_RATING'])
                            
                                        print '@ {position}  -  ({opp_pfd}, {opp_pf}) {sql_name} ({rating})'.format(position=position, sql_name=sql_name, \
                                            rating=PLAYER_ADV_STATS[sql_name]['DEF_RATING'], opp_pf=opp_pf[0]['AVG_PF'], opp_pfd=opp_pf[0]['AVG_PFD'])
                            except IndexError:
                                pass

                    print '\n'

    print '\n'


    player_on_obj = {}
    lineup_summary_object = {}
    print 'LINEUPS (ACCOUNTING FOR INJURY)'


    player_depth = sqlfetch.execute_query(sqlfetch.get_player_roles_by_team(sql_team))
    
    for team_player in player_depth:
        team_player_name = team_player['PLAYER_NAME']
        if team_player_name in news_scraper.SQL_TO_WOWY_TRANSLATE:
            team_player_name = news_scraper.SQL_TO_WOWY_TRANSLATE[team_player_name]

        usg_line_up_summary[team][team_player_name] = {
            'usg': [],
            'dkm': []
        }


    for possible_lineup in possible_lineups[0:num_line_ups:1]:
        # possible_starters
        on_players = []
        for key_marker in key_list:
            if possible_lineup[key_marker] in news_scraper.SQL_TO_WOWY_TRANSLATE:
                on_players.append(news_scraper.SQL_TO_WOWY_TRANSLATE[possible_lineup[key_marker]])
            else:
                on_players.append(possible_lineup[key_marker])

        sorted_on_players = sorted(on_players)
        on_players_str = ', '.join(sorted_on_players)


        if on_players_str not in lineup_summary_object:
            # in general for all opponents
            player_on_obj = news_scraper.player_on_off(WOWY_TEAMS[wowy_team], 'all', on_players, [], FIRST_DATE_REG_SEASON, LAST_DATE_REG_SEASON)

            if len(player_on_obj['lineups']) > 0:

                lineup_summary_object[on_players_str] = {}

                poss_played = news_scraper.two_decimals(float(team_totals_this_year['this_year_lineup_summary_object'][on_players_str]['possessions']) / float(team_totals_this_year['team_total_poss_played_this_year']) * 100)
                min_played = news_scraper.two_decimals(float(team_totals_this_year['this_year_lineup_summary_object'][on_players_str]['minutes_played']) / float(team_totals_this_year['team_total_min_played_this_year']) * 100)

                print 'POSS: {poss_played}%'.format(poss_played=poss_played)

                for usg_player in on_players:
                    print '{player} DKM: {dkm}'.format(player=usg_player, dkm=player_on_obj['players'][usg_player]['compiled_stats']['dkm'])
                    usg = str(player_on_obj['players'][usg_player]['compiled_stats']['usg'])
                    dkm = str(player_on_obj['players'][usg_player]['compiled_stats']['dkm'])

                    # create the obj for players usg & dkm for each lineups
                    if usg_player not in player_summary_object:
                        player_summary_object[usg_player] = {
                            'usg': {},
                            'dkm': {},
                            'num_lineups': 1,
                            'poss_played': poss_played
                        }
                    else:
                        player_summary_object[usg_player]['num_lineups'] += 1
                        player_summary_object[usg_player]['poss_played'] += poss_played

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


                    sql_player = usg_player
                    if sql_player in news_scraper.WOWY_TO_SQL_TRANSLATE:
                        sql_player = news_scraper.WOWY_TO_SQL_TRANSLATE[usg_player]


                    # also get player's score from last year from database
                    player_against_team_log = sqlfetch.execute_query(sqlfetch.get_player_against_team_log(sql_oppo, sql_player, False))
                    player_against_team_obj = {
                        'dkm': [],
                        'usg': [],
                        'pfd': [],
                        'min': [],
                        'dkpt': [],
                        'fga': []
                    }

                    for game_played in player_against_team_log:
                        player_against_team_obj['dkm'].append(game_played['FP_PER_MIN'])
                        player_against_team_obj['usg'].append(game_played['USG_PCT'])
                        player_against_team_obj['pfd'].append(game_played['PFD'])
                        player_against_team_obj['fga'].append(game_played['FGA'])
                        player_against_team_obj['min'].append(game_played['MIN'])
                        player_against_team_obj['dkpt'].append(game_played['DK_POINTS'])


                    # # create the obj for players usg & dkm for each lineups
                    # # or if they played recently
                    # if sql_player not in LAST_PLAYER_SUMMARY_OBJ \
                    #     and sql_player in ALL_TEAM_PLAYERS[team]['sql_players']:
                        
                    #     past_dkm = np.median(player_against_team_obj['dkm']) if len(player_against_team_obj['min']) > 0 else 0
                    #     past_dkm_max = np.max(player_against_team_obj['dkm']) if len(player_against_team_obj['min']) > 0 else 0
                    #     past_dkm_min = np.min(player_against_team_obj['dkm']) if len(player_against_team_obj['min']) > 0 else 0

                    #     LAST_PLAYER_SUMMARY_OBJ[sql_player] = {
                    #         'usg': news_scraper.two_decimals(np.average(player_against_team_obj['usg'])),
                    #         'dkm': news_scraper.two_decimals(past_dkm),
                    #         'min_dkm': news_scraper.two_decimals(past_dkm_min),
                    #         'max_dkm': news_scraper.two_decimals(past_dkm_max),
                    #         'min': player_against_team_obj['min'][0] if len(player_against_team_obj['min']) > 0 else 0,
                    #         'sql_log': {
                    #             'dkm': news_scraper.two_decimals(past_dkm),
                    #             'min_dkm': news_scraper.two_decimals(past_dkm_min),
                    #             'max_dkm': news_scraper.two_decimals(past_dkm_max),
                    #             'pfd': news_scraper.two_decimals(np.average(player_against_team_obj['pfd'])),
                    #             'min': player_against_team_obj['min'][0] if len(player_against_team_obj['min']) > 0 else 0 ,
                    #             'dkpt': news_scraper.two_decimals(np.average(player_against_team_obj['dkpt'])),
                    #             'fga': news_scraper.two_decimals(np.average(player_against_team_obj['fga']))
                    #         }
                    #     }

                for usg_player, stats in usg_line_up_summary[team].iteritems():

                    if usg_player not in on_players:
                        if usg_player in usg_line_up_summary[team]:
                            for stat_keys in ['usg', 'dkm']:
                                usg_line_up_summary[team][usg_player][stat_keys].append(0)
                        else:
                            # create this object for all players
                            usg_line_up_summary[team][usg_player] = {
                                'usg': [0],
                                'dkm': [0]
                            }
                print '\n'

    player_summary_object = sorted(player_summary_object.iteritems(), key=lambda x: x[1]['num_lineups'], reverse=True)
    for idx, obj in enumerate(player_summary_object):
        sql_player = obj[0]
        if sql_player in news_scraper.WOWY_TO_SQL_TRANSLATE:
            sql_player = news_scraper.WOWY_TO_SQL_TRANSLATE[obj[0]]
        
        LINEUP_RANK[sql_player] = idx+1

        print '{player} : {num_lineups} - {poss_played}'.format(player=obj[0], num_lineups=obj[1]['num_lineups'], poss_played=obj[1]['poss_played'])

    print '\n'

    print 'BASED ON LINEUP %'
    get_simple_projections(team, usg_line_up_summary, team_totals_this_year['this_year_player_summary_object'], team_totals_this_year['team_total_poss_played_this_year'], games_player_played, min_lineup_by_game)
    print '\n'


def get_price_fluc(sql_player):
    # process salary things
    price_fluc = 0
    try:
        player_salary = sqlfetch.execute_query(sqlfetch.get_player_salary(sql_player))

        num_occur = len(player_salary)
        price_fluc = int(player_salary[num_occur-1]['SALARY']) - int(player_salary[num_occur-2]['SALARY'])

        if price_fluc == 0:
            price_fluc = '---'
    except IndexError:
        pass

    return price_fluc


def get_reb_chance_projection(teams, TEAM_FGA_PACE):
    by_reb_chances_team = {}
    for (team, oppo) in teams.iteritems():
        sql_team = team
        sql_oppo = oppo
        if team in TRANSLATE_DICT:
            sql_team = TRANSLATE_DICT[team]
        if oppo in TRANSLATE_DICT:
            sql_oppo = TRANSLATE_DICT[oppo]

        fga_predict = test_classifier.rebound_classifier(sql_team, \
            TEAM_FGA_PACE[sql_oppo]['fga'], TEAM_FGA_PACE[sql_oppo]['fg_pct'], TEAM_FGA_PACE[sql_oppo]['pace'])

        by_reb_chances_team[sql_team] = {
            'reb': fga_predict[0][0],
            'reb_chances': fga_predict[0][1]
        }

    return by_reb_chances_team

def get_lineup_diff(out_from_team, sql_team):
    possible_lineups_b4 = sqlfetch.execute_query(sqlfetch.get_lineup_from_absence([], sql_team, 30))
    possible_lineups = sqlfetch.execute_query(sqlfetch.get_lineup_from_absence(out_from_team, sql_team, 30))
    key_list = ['PLAYER_1', 'PLAYER_2', 'PLAYER_3', 'PLAYER_4', 'PLAYER_5']
    temp_obj = {}

    for possible_lineup in possible_lineups_b4:
        # possible_starters
        on_players = []
        for key_marker in key_list:
            on_players.append(possible_lineup[key_marker])

        for usg_player in on_players:
            # create the obj for players usg & dkm for each lineups
            if usg_player not in temp_obj:
                temp_obj[usg_player] = {
                    'num_lineups': 1,
                    'post_num_lineups': 0,
                    'diff': 0,
                }
            else:
                temp_obj[usg_player]['num_lineups'] += 1

    for possible_lineup in possible_lineups:
        # possible_starters
        on_players = []
        for key_marker in key_list:
            on_players.append(possible_lineup[key_marker])

        for usg_player in on_players:
            # create the obj for players usg & dkm for each lineups
            if usg_player not in temp_obj:
                temp_obj[usg_player] = {
                    'num_lineups': 0,
                    'post_num_lineups': 1,
                    'diff': 0
                }
            else:
                temp_obj[usg_player]['post_num_lineups'] += 1
                temp_obj[usg_player]['diff'] = temp_obj[usg_player]['post_num_lineups'] - temp_obj[usg_player]['num_lineups']

    return temp_obj

def get_player_reb_chance_projection(sql_oppo, player_name, TEAM_SPORTVU_FGA):
    by_reb_chances_player = {}

    condensed_fga_obj = {
        'OPP_AVG_DRIVE_FGA': TEAM_SPORTVU_FGA[sql_oppo]['AVG_DRIVE_FGA'],
        'OPP_AVG_CATCH_SHOOT_FGA': TEAM_SPORTVU_FGA[sql_oppo]['AVG_CATCH_SHOOT_FGA'],
        'OPP_AVG_CATCH_SHOOT_FG3A': TEAM_SPORTVU_FGA[sql_oppo]['AVG_CATCH_SHOOT_FG3A'],
        'OPP_AVG_ELBOW_TOUCH_FGA': TEAM_SPORTVU_FGA[sql_oppo]['AVG_ELBOW_TOUCH_FGA'],
        'OPP_AVG_PAINT_TOUCH_FGA': TEAM_SPORTVU_FGA[sql_oppo]['AVG_PAINT_TOUCH_FGA'],
        'OPP_AVG_PULL_UP_FGA': TEAM_SPORTVU_FGA[sql_oppo]['AVG_PULL_UP_FGA'],
        'OPP_AVG_POST_TOUCH_FGA': TEAM_SPORTVU_FGA[sql_oppo]['AVG_POST_TOUCH_FGA'],
    }


    fga_predict = test_classifier.improve_rebound_classifier(player_name, condensed_fga_obj)
    if len(fga_predict) >= 1:
        reb = fga_predict[0][0]
        reb_chances = fga_predict[0][1]
    else:
        reb = 0
        reb_chances = 0

    by_reb_chances_player[player_name] = {
        'reb': reb,
        'reb_chances': reb_chances
    }

    return by_reb_chances_player


def get_price_fluc_by_player(sql_player, player, dk_obj_by_position):

    price_fluc = get_price_fluc(sql_player)
    name = player[2]
    salary = player[5]
    positions = player[0].split('/')
    fp_needed = float(salary)*0.001*6
    avg_val = float(player[8])/(0.001*float(salary))

    try:
        max_salary = sqlfetch.execute_query(sqlfetch.get_player_max_salary(sql_player))[0]['SALARY']
    except IndexError:
        max_salary = 0

    try:

        min_salary = sqlfetch.execute_query(sqlfetch.get_player_min_salary(sql_player))[0]['SALARY']
    except IndexError:
        min_salary = 0

    for position in positions:
        # keep repated players for now
        dk_obj_by_position[position][name] = {
            'avg_val': avg_val,
            'salary': salary,
            'fp_needed': fp_needed,
            'price_fluc': price_fluc,
            'max_salary': max_salary,
            'min_salary': min_salary
        }

        if name not in dk_obj_by_position['all']: 
            dk_obj_by_position['all'][name] = {
                'avg_val': avg_val,
                'salary': salary,
                'fp_needed': fp_needed,
                'price_fluc': price_fluc,
                'max_salary': max_salary,
                'min_salary': min_salary
            }

    return dk_obj_by_position

def avg_vs_vegas(todays_date, sql_teams_playing):
    VEGAS_LINES = news_scraper.get_vegas_lines()
    team_point_avgs = sqlfetch.execute_query(sqlfetch.get_base_team_avg(FIRST_DATE_REG_SEASON))
    team_proj_pts_obj = {}
    for team in team_point_avgs:
        team_name = team['TEAM']

        if team_name in VEGAS_LINES and team_name in sql_teams_playing:
            team_avg = float(team['AVG_PTS'])
            if VEGAS_LINES[team_name]['proj_points'] != 'N/A':
                vegas_proj = float(VEGAS_LINES[team_name]['proj_points'])
                team_proj_pts_obj[team_name] = {
                    'team_name': team_name,
                    'proj_diff': news_scraper.two_decimals(vegas_proj - team_avg),
                    'team_avg': team_avg,
                    'vegas_proj': vegas_proj,
                    'ou' : VEGAS_LINES[team_name]['ou'],
                    'line' : VEGAS_LINES[team_name]['line'],
                    'oppo' : VEGAS_LINES[team_name]['oppo']
                }

    return team_proj_pts_obj

def print_vegas_lines(todays_date, sql_teams_playing):
    
    print 'VEGAS LINES'
    vegas_diff = avg_vs_vegas(todays_date, sql_teams_playing)

    # print vegas_diff

    vds = sorted(vegas_diff.iteritems(), key=lambda x: (x[1]['ou'], abs(float(x[1]['line']))), reverse=True)
    vds_line = sorted(vegas_diff.iteritems(), key=lambda x: abs(float(x[1]['line'])), reverse=False)
    vds_diff = sorted(vegas_diff.iteritems(), key=lambda x: float(x[1]['proj_diff']), reverse=True)

    weighted_obj = {}
    ou_count = 0


    for idx, team in enumerate(vds):
        print '{team_name} - {vegas_proj}/{ou} ({proj_diff}) {line}'.format(team_name=team[0], \
            vegas_proj=team[1]['vegas_proj'], ou=team[1]['ou'], proj_diff=team[1]['proj_diff'], line=team[1]['line'])
        
        weighted_obj[team[0]] = {
            'ou_score': 0,
            'line_score': 0,
            'diff_score': 0
        }


        try:
            if team[1]['ou'] == vds[idx - 1][1]['ou'] and idx - 1 > 0:
                weighted_obj[team[0]]['ou_score'] = ou_count
                weighted_obj[vds[idx - 1][0]]['ou_score'] = ou_count
            else:
                ou_count += 1

        except IndexError:
            pass

    # line score should be weighted more than the ou score?... regression weighted?
    line_count = 0

    for idx, team in enumerate(vds_line):
        try:

            if abs(float(team[1]['line'])) == abs(float(vds_line[idx - 1][1]['line'])):

                weighted_obj[team[0]]['line_score'] = line_count
                weighted_obj[vds_line[idx - 1][0]]['line_score'] = line_count
            else:
                line_count += 1

        except IndexError:
            pass
    print '\n'

    # proj_diff rank
    diff_count = 0

    for idx, team in enumerate(vds_diff):

        try:

            if abs(float(team[1]['proj_diff'])) == abs(float(vds_diff[idx - 1][1]['proj_diff'])):

                weighted_obj[team[0]]['diff_score'] = diff_count
                weighted_obj[vds_diff[idx - 1][0]]['diff_score'] = diff_count
            else:
                diff_count += 1
                weighted_obj[team[0]]['diff_score'] = diff_count

        except IndexError:
            pass
    print '\n'

    for team_name, scores in weighted_obj.iteritems():

        vegas_diff[team_name]['line_score'] = scores['line_score']
        vegas_diff[team_name]['ou_score'] = scores['ou_score']
        vegas_diff[team_name]['diff_score'] = scores['diff_score']
        vegas_diff[team_name]['reg_weighted_score'] = news_scraper.two_decimals(float(1/(news_scraper.two_decimals(scores['diff_score'] * 0.2 + scores['line_score'] * 0.3 + scores['ou_score'] * 0.5))) * 100)

    return vegas_diff

def days_between(d1, d2):
    d1 = datetime.strptime(d1, "%Y-%m-%d")
    d2 = datetime.strptime(d2, "%Y-%m-%d")
    return abs((d2 - d1).days)



def get_dk_money_obj(today_date, suffix):

    value_games_min = {}
    position_cost_metrics = {}
    greater_than_value_players = []

    get_team_fga_pace = sqlfetch.execute_query(sqlfetch.get_team_fga_pace(FIRST_DATE_REG_SEASON))

    for team in get_team_fga_pace:
        TEAM_FGA_PACE[team['TEAM']] = {
            'fga': team['AVG_FGA'],
            'reb': team['AVG_REB'],
            'fg_pct': team['AVG_FG_PCT'],
            'pace': team['AVG_PACE']
        }

    # money obj by position
    dk_obj_by_position = {
        'PG': {},
        'SG': {},
        'SF': {},
        'PF': {},
        'C': {},
        'all': {}
    }

    sql_players_obj = {}
    sql_teams_playing = {}

    if suffix != '':
        filename = str(today_date)+'-'+str(suffix)
    else:
        filename = str(today_date)

    with open('../scrape/csv/'+filename+'.csv',) as csv_file:
        try:
            next(csv_file, None)
            players = csv.reader(csv_file)
            for player in players:
                name = player[2]
                salary = player[5]
                positions = player[0].split('/')
                fp_needed = float(salary)*0.001*6
                avg_val = float(player[8])/(0.001*float(salary))

                away_team = DK_TEAMS[player[6].split("@")[0]]
                home_team = DK_TEAMS[player[6].split("@")[1].split(" ")[0]]
                player_team = DK_TEAMS[player[7]]

                if player_team == home_team:
                    player_opp = away_team
                else:
                    player_opp = home_team

                if player_team not in TEAMS_PLAYING:

                    sql_team = player_team
                    sql_oppo = player_opp
                    if player_team in TRANSLATE_DICT:
                        sql_team = TRANSLATE_DICT[player_team]
                    if player_opp in TRANSLATE_DICT:
                        sql_oppo = TRANSLATE_DICT[player_opp]
                
                    TEAMS_PLAYING[player_team] = player_opp

                    sql_teams_playing[sql_team] = sql_oppo


                if name in news_scraper.DK_TO_SQL_TRANSLATE:
                    sql_player = news_scraper.DK_TO_SQL_TRANSLATE[name]
                else:
                    sql_player = name

                try:
                    player_role = sqlfetch.execute_query(sqlfetch.get_player_roles_by_name(sql_player))[0]['ROLE']                
                except IndexError:
                    OUT_PLAYERS.append(sql_player)

                # get_player_daily_status(OUT_PLAYERS, sql_player, player_role)
                get_price_fluc_by_player(sql_player, player, dk_obj_by_position)


                DK_MONEY_OBJ[name] = {
                    'positions': positions,
                    'salary': salary,
                    'fp_avg': player[8],
                    'fp_needed': fp_needed,
                    'avg_val': avg_val
                }

                # get the guys that are 4200 - 5500 and see if they are in the replacement players
                # for those guys check the guys that are drawing 20+min last free games

            team_summary = {}
            changed_team = {};
            for (team, oppo) in TEAMS_PLAYING.iteritems():
                                
                sql_team = team
                sql_oppo = oppo
                if team in TRANSLATE_DICT:
                    sql_team = TRANSLATE_DICT[team]
                if oppo in TRANSLATE_DICT:
                    sql_oppo = TRANSLATE_DICT[oppo]
                # print sql_team
                # print DIFF_OUTS[sql_team]['added']
                # print DIFF_OUTS[sql_team]['removed']
                if len(DIFF_OUTS[sql_team]['added']) >= 1 or len(DIFF_OUTS[sql_team]['removed']) >= 1:
                    # POSSIBLE_GAME_STACKS[sql_team] = sql_team
                    print sql_team + " CHANGED"
                    changed_team[sql_team] = True;
                    if len(DIFF_OUTS[sql_team]['added']) >= 1:
                        print 'Added:'
                        print DIFF_OUTS[sql_team]['added']
                    if len(DIFF_OUTS[sql_team]['removed']) >= 1:
                        print 'Removed:'
                        print DIFF_OUTS[sql_team]['removed']


                get_team_depth_chart(team, OUT_PLAYERS)
                # injury_depth_chart = process_pre_post_injury_depth_chart(team, OUT_PLAYERS)

                team_summary[sql_team] = {}
                # date_last_game_played = sqlfetch.execute_query(sqlfetch.get_date_last_game_played(sql_team, FIRST_DATE_REG_SEASON))[0]['DATE']

                # get defensive rating & offensive rating
                # team_summary[sql_team]['days_rested'] = days_between(date_last_game_played, today_date) - 1
                team_summary[sql_team]['out_players'] = ", ".join(OUT_LIST[sql_team])

                
                # # get the reb_chances 
                # playing_players = ALL_TEAM_PLAYERS[team]['by_role']['starters'] + ALL_TEAM_PLAYERS[team]['by_role']['rotation']
                # sql_players_obj[team] = {}
                # for player_name in playing_players:
                #     # get the reb_chances and the PFD and PF
                #     # depth to sql
                #     sql_name = player_name
                #     if player_name in news_scraper.DEPTH_TO_DK_TRANSLATE:
                #         player_name = news_scraper.DEPTH_TO_DK_TRANSLATE[player_name]

                #     if player_name in news_scraper.DK_TO_SQL_TRANSLATE:
                #         sql_name = news_scraper.DK_TO_SQL_TRANSLATE[player_name]

                #     try:
                #         fouls = sqlfetch.execute_query(sqlfetch.get_player_pf(FIRST_DATE_REG_SEASON, sql_name))[0]
                #         pfd = fouls['AVG_PFD']
                #         pf = fouls['AVG_PF']
                #     except IndexError:
                #         pfd = 0
                #         pf = 0
                #     sql_players_obj[team][player_name] = {
                #         'pfd': pfd,
                #         'pf': pf
                #     }
        
                    # by_reb_chances_player = get_player_reb_chance_projection(sql_oppo, sql_name, TEAM_SPORTVU_FGA)

                    # try:
                    #     rebound_chances = sqlfetch.execute_query(sqlfetch.get_reb_chances_by_player(sql_name))[0]['REB_CHANCES']
                    # except IndexError:
                    #     rebound_chances = 0

                    # sql_players_obj[team][player_name]['reb_chances'] = rebound_chances
                    # sql_players_obj[team][player_name]['proj_reb'] = by_reb_chances_player[sql_name]['reb']

    
            # print 'REB CHANCE PROJECTION'
            # by_reb_chances_team = get_reb_chance_projection(TEAMS_PLAYING, TEAM_FGA_PACE)

            # brct = sorted(by_reb_chances_team.iteritems(), key=lambda x: x[1]['reb_chances'], reverse=True)

            # for reb_team in brct:
            #     team = reb_team[0]
            #     if team in news_scraper.REVERSE_TRANSLATE_DICT:
            #         team = news_scraper.REVERSE_TRANSLATE_DICT[team]

            #     by_rebound = sorted(sql_players_obj[team].iteritems(), key=lambda x: x[1]['proj_reb'], reverse=True)

            #     temp_players = []
            #     for stats in by_rebound:
            #         temp_players.append(stats[0] + '(' + str(stats[1]['proj_reb']) + ')')
            #         # temp_players.append(stats[0] + '(' + str(stats[1]['reb_chances']) + ')')

            #     players_string = ', '.join(temp_players)

            #     print '{reb_team} - {reb_chances}  ({temp_players})'.format(reb_team=team, reb_chances=reb_team[1]['reb_chances'], temp_players=players_string)

            # print '\n'

            # team_fouls = sqlfetch.execute_query(sqlfetch.get_team_fouls(FIRST_DATE_REG_SEASON))

            # print 'FOULS'
            # for f_team in team_fouls:
            #     team = f_team['TEAM']
            #     if team in news_scraper.REVERSE_TRANSLATE_DICT:
            #         team = news_scraper.REVERSE_TRANSLATE_DICT[team]

            #     if team in TEAMS_PLAYING:
            #         by_fouls = sorted(sql_players_obj[team].iteritems(), key=lambda x: x[1]['pf'], reverse=True)

            #         temp_players = []
            #         for stats in by_fouls:
            #             temp_players.append(stats[0] + '(' + str(stats[1]['pf']) + ')')
                    
            #         players_string = ', '.join(temp_players)

            #         print '{f_team} - {fouls}'.format(f_team=team, fouls=f_team['AVG_FOULS'])
            #         print '({temp_players})'.format(temp_players=players_string)


            # print '\n'

            # team_fouls_drawn = sqlfetch.execute_query(sqlfetch.get_team_fouls_drawn(FIRST_DATE_REG_SEASON))
            
            # print 'FOULS PFD'
            # for f_team in team_fouls_drawn:
            #     team = f_team['TEAM']
            #     if team in news_scraper.REVERSE_TRANSLATE_DICT:
            #         team = news_scraper.REVERSE_TRANSLATE_DICT[team]

            #     if team in TEAMS_PLAYING:
            #         # for the players on that team get the highest reb_rate players (that are on rotation or starting)
            #         by_fouls_d = sorted(sql_players_obj[team].iteritems(), key=lambda x: x[1]['pfd'], reverse=True)

            #         temp_players = []
            #         for stats in by_fouls_d:
            #             temp_players.append(stats[0] + '(' + str(stats[1]['pfd']) + ')')
                    
            #         players_string = ', '.join(temp_players)

            #         print '{f_team} - {fouls}'.format(f_team=team, fouls=f_team['AVG_FOULS_DRAWN'])
            #         print '({temp_players})'.format(temp_players=players_string)


 
            # for (team, oppo) in TEAMS_PLAYING.iteritems():
            #     # get_possible_lineups(team, oppo)
                
            #     sql_team = team
            #     sql_oppo = oppo
            #     if team in TRANSLATE_DICT:
            #         sql_team = TRANSLATE_DICT[team]
            #     if oppo in TRANSLATE_DICT:
            #         sql_oppo = TRANSLATE_DICT[oppo]
            #     out_from_team = OUT_PLAYERS + TRADED_LIST[sql_team]
            #     DIFF_INJURY_LINEUPS[sql_team] = get_lineup_diff(out_from_team, sql_team)
            
            #     sorted_num_lineups = sorted(DIFF_INJURY_LINEUPS[sql_team].iteritems(), key=lambda x: x[1]['post_num_lineups'], reverse=True)
            #     for idx, obj in enumerate(sorted_num_lineups):
            #         sql_player = obj[0]
            #         if sql_player in news_scraper.WOWY_TO_SQL_TRANSLATE:
            #             sql_player = news_scraper.WOWY_TO_SQL_TRANSLATE[obj[0]]
                    
            #         LINEUP_RANK[sql_player] = idx+1


            # USE DK NAMES HERE BRK, PHO, CHO
            # get_possible_lineups('NYK', 'MIL')


            # player_summary_obj = sorted(LAST_PLAYER_SUMMARY_OBJ.iteritems(), key=lambda x: x[1]['dkm'], reverse=True)
            # print '\n'

            # print 'BASED ON LAST SEASON STATS'
            # for obj in player_summary_obj:

            #     if obj[1]['sql_log']['min'] != 0:

            #         print '{player} - {dkm}dkm / {min}m'.format(player=obj[0], dkm=obj[1]['dkm'], min=obj[1]['min'])
            #         print '{min}min - {dkm}dkm - {dkpt}dkpt - {fga}fga - {pfd}pfd'.format(\
            #             min=obj[1]['sql_log']['min'], dkm=obj[1]['sql_log']['dkm'], \
            #             dkpt=obj[1]['sql_log']['dkpt'], fga=obj[1]['sql_log']['fga'], pfd=obj[1]['sql_log']['pfd'])
            #     else:
            #         print '{player} - DNP'.format(player=obj[0])


            # print '\n'

            # pspb = sorted(LINEUP_BASED_PROJ.iteritems(), key=lambda x: x[1]['points_basis'], reverse=True)

            # opp_pspb = {}
            # all_pspb = {}

            # print 'PROJECTION BASIS'
            # for obj in pspb:
            #     opp = ''
            #     price_fluc = ''
            #     avg_val = ''
            #     salary = ''
            #     player_name = obj[0]
            #     team = obj[1]['team']

            #     historical = None

            #     poss_played = PLAYER_AVG_PLAYTIME[player_name]

            #     if player_name in OPPORTUNITY_PLAYERS:
            #         opp = '**'


            #     dk_name = player_name
            #     if player_name in news_scraper.SQL_TO_DK_TRANSLATE:
            #         dk_name = news_scraper.SQL_TO_DK_TRANSLATE[player_name]


            #     if dk_name in dk_obj_by_position['all']:
            #         salary_obj = dk_obj_by_position['all'][dk_name]
            #         price_fluc = salary_obj['price_fluc']
            #         avg_val = news_scraper.two_decimals(salary_obj['avg_val'])
            #         salary = salary_obj['salary']

            #         if salary == salary_obj['max_salary'] and salary == salary_obj['min_salary']:
            #             pass
            #         elif salary == salary_obj['max_salary']:
            #             historical = 'ATH'
            #         elif salary == salary_obj['min_salary']:
            #             historical = 'ATL'

            #     if team not in all_pspb:
            #         all_pspb[team] = {}

            #     if player_name not in OUT_PLAYERS:                    
            #         # store opportunity players in a separate list as well
            #         if team not in opp_pspb:
            #             opp_pspb[team] = {}
            #             opp_pspb[team][player_name] = {
            #                 'historical': historical,
            #                 'price_fluc': price_fluc,
            #                 'avg_val': avg_val,
            #                 'salary': int(salary) if salary != '' else '',
            #                 'points_basis': obj[1]['points_basis'],
            #                 'median': obj[1]['median'],
            #                 'value_goal': obj[1]['value_goal'],
            #                 'poss_played': poss_played,
            #                 'team': team
            #             }
            #         else:
            #             opp_pspb[team][player_name] = {
            #                 'historical': historical,
            #                 'price_fluc': price_fluc,
            #                 'avg_val': avg_val,
            #                 'salary': int(salary) if salary != '' else '',
            #                 'points_basis': obj[1]['points_basis'],
            #                 'median': obj[1]['median'],
            #                 'value_goal': obj[1]['value_goal'],
            #                 'poss_played': poss_played,
            #                 'team': team
            #             }

            #         all_pspb[team][player_name] = {
            #             'historical': historical,
            #             'price_fluc': price_fluc,
            #             'avg_val': avg_val,
            #             'salary': int(salary) if salary != '' else '',
            #             'points_basis': obj[1]['points_basis'],
            #             'median': obj[1]['median'],
            #             'value_goal': obj[1]['value_goal'],
            #             'poss_played': poss_played,
            #             'team': team
            #         }


            #         if historical != None:
            #             print '({historical} {price_fluc}) {avg_val} @ {salary}'.format(\
            #                 historical=historical, price_fluc=price_fluc, avg_val=avg_val, salary=salary)
            #             print '{player}  -  {points_basis}pb ({median} / {value_goal})  -  {poss_played}% {opp}'.format(\
            #                 player=player_name, points_basis=obj[1]['points_basis'], \
            #                 median=obj[1]['median'], value_goal=obj[1]['value_goal'], \
            #                 opp=opp, poss_played=poss_played)
            #         else:
            #             print '({price_fluc}) {avg_val} @ {salary}'.format(\
            #                 price_fluc=price_fluc, avg_val=avg_val, salary=salary)
            #             print '{player}  -  {points_basis}pb ({median} / {value_goal})  -  {poss_played}% {opp}'.format(\
            #                 player=player_name, points_basis=obj[1]['points_basis'], \
            #                 median=obj[1]['median'], value_goal=obj[1]['value_goal'], \
            #                 opp=opp, poss_played=poss_played)

            # print '\n'


            # print 'NOT_FAV_THROW_INS'

            # for team, players in all_pspb.iteritems():
            #     for player_name, player_obj in players.iteritems():

            #         if (player_obj['price_fluc'] < 0 or \
            #             player_obj['price_fluc'] == '---') \
            #             and player_obj['median'] >= 29:

            #                 print '({price_fluc}) {avg_val} @ {salary}'.format(\
            #                 price_fluc=player_obj['price_fluc'], avg_val=player_obj['avg_val'], \
            #                 salary=player_obj['salary'])
            #                 print '{player}  -  {points_basis}pb ({median} / {value_goal})  -  {poss_played}%'.format(\
            #                     player=player_name, points_basis=player_obj['points_basis'], \
            #                     median=player_obj['median'], value_goal=player_obj['value_goal'], \
            #                     poss_played=player_obj['poss_played'])

            # print '\n'

            # print 'FAV_THROW_INS'

            # for team, players in all_pspb.iteritems():
            #     for player_name, player_obj in players.iteritems():
            #         if (player_obj['price_fluc'] > 0) \
            #             and player_obj['median'] >= 29:

            #                 print '({price_fluc}) {avg_val} @ {salary}'.format(\
            #                 price_fluc=player_obj['price_fluc'], avg_val=player_obj['avg_val'], \
            #                 salary=player_obj['salary'])
            #                 print '{player}  -  {points_basis}pb ({median} / {value_goal})  -  {poss_played}%'.format(\
            #                     player=player_name, points_basis=player_obj['points_basis'], \
            #                     median=player_obj['median'], value_goal=player_obj['value_goal'], \
            #                     poss_played=player_obj['poss_played'])

            # print '\n'

            thin_depth_obj = {}
            last_n_playtime = {}
            pre_post_injury_depth_chart = {}
            for team, stats in team_summary.iteritems():
                
                print '\n'
                # depth chart print out
                print_depth_chart(team)
                out_from_team = OUT_PLAYERS + TRADED_LIST[team]
                # get last game playtime
                last_n_playtime = get_last_game(team, 3)
                # last_one_playtime = get_last_game(team, 1)

                # last_game_starters = get_last_game_starters(team)

                print '{team} - Out players: {players}'.format(\
                    team=team, players=stats['out_players'])
                print '\n'
                # print 'Team Depth'
                # print 'PG: {pg} SG: {sg} SF: {sf} PF: {pf} C: {c}'.format(\
                #     pg=len(TEAM_DEPTH_COUNT[team]['PG']),\
                #     sg=len(TEAM_DEPTH_COUNT[team]['SG']),\
                #     sf=len(TEAM_DEPTH_COUNT[team]['SF']),\
                #     pf=len(TEAM_DEPTH_COUNT[team]['PF']),\
                #     c=len(TEAM_DEPTH_COUNT[team]['C']))

                # ALL_TEAM_PLAYERS[team]['out_players'][position]

                sql_oppo = sql_teams_playing[team]
                
                team_chalk_bonus = 0
                pre_post_injury_depth_chart[team] = process_pre_post_injury_depth_chart(team, out_from_team)

                for position_name in ['PG', 'SG', 'SF', 'PF', 'C']:
                    players_in_position = len(TEAM_DEPTH_COUNT[team][position_name])

                    if players_in_position <= 1:
                        
                        if players_in_position == 0:
                            print 'No player @ {position} position / New rotations'.format(position=position_name)
                        else:
                            lone_starter = ''.join(TEAM_DEPTH_COUNT[team][position_name])

                            thin_depth_obj[lone_starter] = {
                                'position': position_name,
                                'team': team,
                                'name': lone_starter
                            }

                            print 'Lone player @ {position} position: {player}'.format(position=position_name, player=lone_starter)

                        team_chalk_bonus += 1
                # for the remaining players
                # check for last year's match up status get the avg dkpt +
                # check for the lineup % who plays the most
                chalk_obj = {}

                dk_team = team
                if team in news_scraper.REVERSE_TRANSLATE_DICT:
                    dk_team = news_scraper.REVERSE_TRANSLATE_DICT[team]

                NUM_AVAIL_PLAYERS[team] = len(ALL_TEAM_PLAYERS[dk_team]['all_rotation_players'])
                temp_list = []
                for player_name in ALL_TEAM_PLAYERS[dk_team]['all_players'] + TRADED_LIST[team]:
                    sql_name = str(player_name)
                    if player_name in news_scraper.DEPTH_TO_DK_TRANSLATE:
                        player_name = news_scraper.DEPTH_TO_DK_TRANSLATE[player_name]
                        sql_name = str(player_name)

                    # player_name

                    if player_name in news_scraper.DK_TO_SQL_TRANSLATE:
                        sql_name = str(news_scraper.DK_TO_SQL_TRANSLATE[player_name])
                    
                    # if sql_name not in OBVIOUS_OUTS['by_team'][team] \
                    #     and sql_name not in out_from_team:

                    # only get the players that have played (safe assumption as new players wont be chalk)
                    # if player_name in DK_MONEY_OBJ:
                    # print sql_name
                    player_general = sqlfetch.execute_query(sqlfetch.get_player_general(sql_name))
                    if player_general:
                        if sql_name in out_from_team:
                            temp_list.append(player_general[0]['PLAYER_ID'])
                        else:
                            if player_general[0]['TEAM_ABBREVIATION'] == team:
                                temp_team_id = player_general[0]['TEAM_ID']
    
                        # print player_general[0]['PLAYER_ID']
                        chalk_obj[sql_name] = {
                            'id': player_general[0]['PLAYER_ID'],
                            'boosted': False,
                            # value_when_true if condition else value_when_false
                            'median': LINEUP_BASED_PROJ[sql_name]['median'] if sql_name in LINEUP_BASED_PROJ else 0,
                            'median36': LINEUP_BASED_PROJ[sql_name]['median36'] if sql_name in LINEUP_BASED_PROJ else 0,
                            'max': LINEUP_BASED_PROJ[sql_name]['max'] if sql_name in LINEUP_BASED_PROJ else 0,
                            'value_goal': LINEUP_BASED_PROJ[sql_name]['value_goal'] if sql_name in LINEUP_BASED_PROJ else 0,
                            'avg_fp': 0,
                            'points_basis' : LINEUP_BASED_PROJ[sql_name]['points_basis'] if sql_name in LINEUP_BASED_PROJ else 0,
                            'rank' : LINEUP_BASED_PROJ[sql_name]['rank'] if sql_name in LINEUP_BASED_PROJ else 100,
                            # 'lineup_rank' : LINEUP_RANK[sql_name] if sql_name in LINEUP_RANK else 100,
                            'poss_played': PLAYER_AVG_PLAYTIME[sql_name] if sql_name in PLAYER_AVG_PLAYTIME else 0,
                            'fp_per_hundred': 0,
                            'pfd': 0,
                            'pf': 0,
                            'min': float(player_general[0]['MIN']) if len(player_general) >= 1 else 0
                        }


                        
                        # # cgheck for CHA
                        # if sql_name not in LAST_PLAYER_SUMMARY_OBJ:

                        #     # also get player's score from last year from database
                        #     player_against_team_log = sqlfetch.execute_query(sqlfetch.get_player_against_team_log(sql_oppo, sql_name, False))
                        #     player_against_team_obj = {
                        #         'dkm': [],
                        #         'usg': [],
                        #         'pfd': [],
                        #         'min': [],
                        #         'dkpt': [],
                        #         'fga': []
                        #     }

                        #     for game_played in player_against_team_log:
                        #         player_against_team_obj['dkm'].append(game_played['FP_PER_MIN'])
                        #         player_against_team_obj['usg'].append(game_played['USG_PCT'])
                        #         player_against_team_obj['pfd'].append(game_played['PFD'])
                        #         player_against_team_obj['fga'].append(game_played['FGA'])
                        #         player_against_team_obj['min'].append(game_played['MIN'])
                        #         player_against_team_obj['dkpt'].append(game_played['DK_POINTS'])


                        #     # create the obj for players usg & dkm for each lineups
                        #     # or if they played recently
                        #     if sql_name not in LAST_PLAYER_SUMMARY_OBJ \
                        #         and sql_name in ALL_TEAM_PLAYERS[dk_team]['sql_players']:
                                
                        #         past_dkm = np.median(player_against_team_obj['dkm']) if len(player_against_team_obj['min']) > 0 else 0
                        #         past_dkm_max = np.max(player_against_team_obj['dkm']) if len(player_against_team_obj['min']) > 0 else 0
                        #         past_dkm_min = np.min(player_against_team_obj['dkm']) if len(player_against_team_obj['min']) > 0 else 0

                        #         LAST_PLAYER_SUMMARY_OBJ[sql_name] = {
                        #             'usg': news_scraper.two_decimals(np.average(player_against_team_obj['usg'])),
                        #             'dkm': news_scraper.two_decimals(past_dkm),
                        #             'min_dkm': news_scraper.two_decimals(past_dkm_min),
                        #             'max_dkm': news_scraper.two_decimals(past_dkm_max),
                        #             'min': player_against_team_obj['min'][0] if len(player_against_team_obj['min']) > 0 else 0,
                        #             'sql_log': {
                        #                 'dkm': news_scraper.two_decimals(past_dkm),
                        #                 'min_dkm': news_scraper.two_decimals(past_dkm_min),
                        #                 'max_dkm': news_scraper.two_decimals(past_dkm_max),
                        #                 'pfd': news_scraper.two_decimals(np.average(player_against_team_obj['pfd'])),
                        #                 'min': player_against_team_obj['min'][0] if len(player_against_team_obj['min']) > 0 else 0 ,
                        #                 'dkpt': news_scraper.two_decimals(np.average(player_against_team_obj['dkpt'])),
                        #                 'fga': news_scraper.two_decimals(np.average(player_against_team_obj['fga']))
                        #             }
                        #         }

                        # if sql_name in LAST_PLAYER_SUMMARY_OBJ and LAST_PLAYER_SUMMARY_OBJ[sql_name]['dkm']:
                        #     chalk_obj[sql_name]['past_dkm'] = LAST_PLAYER_SUMMARY_OBJ[sql_name]['dkm']
                        # else:
                        #     chalk_obj[sql_name]['past_dkm'] = 0
                        # if sql_name in LAST_PLAYER_SUMMARY_OBJ and LAST_PLAYER_SUMMARY_OBJ[sql_name]['max_dkm']:
                        #     chalk_obj[sql_name]['max_dkm'] = LAST_PLAYER_SUMMARY_OBJ[sql_name]['max_dkm']
                        # else:
                        #     chalk_obj[sql_name]['max_dkm'] = 0
                        # if sql_name in LAST_PLAYER_SUMMARY_OBJ and LAST_PLAYER_SUMMARY_OBJ[sql_name]['min_dkm']:
                        #     chalk_obj[sql_name]['min_dkm'] = LAST_PLAYER_SUMMARY_OBJ[sql_name]['min_dkm']
                        # else:

                        chalk_obj[sql_name]['max_dkm'] = 0
                        chalk_obj[sql_name]['min_dkm'] = 0
                        chalk_obj[sql_name]['past_dkm'] = 0

                if (len(temp_list) > 1):
                    temp_str = ''
                    for idx, player_id in enumerate(temp_list):
                        temp_str = temp_str+str(idx)+'Exactly1OffFloor='+str(player_id)+'&'

                    # link_str = 'https://api.pbpstats.com/get-wowy-stats/nba?'+str(temp_str)+'TeamId='+str(temp_team_id)+'&Season=2018-19&SeasonType=Regular%2BSeason&Type=Player'
                    link_str = 'https://api.pbpstats.com/get-wowy-stats/nba?'+str(temp_str)+'TeamId='+str(temp_team_id)+'&Season=2018-19&SeasonType=Playoffs&Type=Player'
                elif (len(temp_list) == 1):
                    # link_str = 'https://api.pbpstats.com/get-wowy-stats/nba?0Exactly1OffFloor='+str(temp_list[0])+'&TeamId='+str(temp_team_id)+'&Season=2018-19&SeasonType=Regular%2BSeason&Type=Player'
                    link_str = 'https://api.pbpstats.com/get-wowy-stats/nba?0Exactly1OffFloor='+str(temp_list[0])+'&TeamId='+str(temp_team_id)+'&Season=2018-19&SeasonType=Playoffs&Type=Player'
                else:
                    link_str = ''

                if link_str != '':
                    wowy_obj = news_scraper.new_wowy(link_str)

                    wowy_obj_sorted = sorted(wowy_obj.iteritems(), key=lambda x: (x[1]['possessions_played'], x[1]['usage']), reverse=True)
                    for obj in wowy_obj_sorted:
                        player_name = obj[0]
                        values = obj[1]

                        print '{player_name} {possessions_played} ({usage})'.format(player_name=player_name, \
                            possessions_played=values['possessions_played'], usage=values['usage'])

                # if team in opp_pspb:

                #     all_opp_players = []
                #     accessed_players = []
                #     for player_names in POSSIBLE_LINEUP[team].split(', '):
                #         all_opp_players.append(player_names)

                #     player_stats_snapshot = sqlfetch.execute_query(sqlfetch.get_stats_snapshot_by_team(team, '2018-01-18'))

                #     for stats in player_stats_snapshot:
                #         if stats['PLAYER_NAME'] in chalk_obj:
                #             chalk_obj[stats['PLAYER_NAME']]['fp_per_hundred'] = stats['NBA_FANTASY_PTS'] if 'NBA_FANTASY_PTS' in stats else 0
                #             chalk_obj[stats['PLAYER_NAME']]['pf'] = stats['PF'] if 'PF' in stats else 0
                #             chalk_obj[stats['PLAYER_NAME']]['pfd'] = stats['PFD'] if 'PFD' in stats else 0

                print '\n'
                #  ~ 1 since absolute numbers
                oppo_allowed = sqlfetch.execute_query(sqlfetch.get_team_against_oppo_ranks(news_scraper.SQL_TEAMS_DICT[sql_oppo]))[0]
                oppo_allowed_advanced = sqlfetch.execute_query(sqlfetch.get_team_against_oppo_advanced_ranks(news_scraper.SQL_TEAMS_DICT[sql_oppo]))[0]

                print 'Facing {sql_oppo}'.format(sql_oppo=sql_oppo)
                print '{sql_oppo} is giving up {OPP_REB} REB per game (Rank: {OPP_REB_RANK})'.format(\
                    sql_oppo=sql_oppo, OPP_REB_RANK=int(oppo_allowed['OPP_REB_RANK']),OPP_REB=oppo_allowed['OPP_REB'])
                print '{sql_oppo} is giving up {OPP_FG3M} 3PM per game (Rank: {OPP_FG3M_RANK})'.format(\
                    sql_oppo=sql_oppo, OPP_FG3M_RANK=int(oppo_allowed['OPP_FG3M_RANK']),OPP_FG3M=oppo_allowed['OPP_FG3M'])
                print '{sql_oppo} is forcing {OPP_TOV} TOV per game (Rank: {OPP_TOV_RANK})'.format(\
                    sql_oppo=sql_oppo, OPP_TOV_RANK=int(oppo_allowed['OPP_TOV_RANK']),OPP_TOV=oppo_allowed['OPP_TOV'])
                print '{sql_oppo} is drawing {OPP_PF} FOULS per game (Rank: {OPP_PF_RANK})'.format(\
                    sql_oppo=sql_oppo, OPP_PF_RANK=abs(int(oppo_allowed['OPP_PF_RANK']) - 29),OPP_PF=oppo_allowed['OPP_PF'])
                print '{sql_oppo} commits {OPP_PFD} fouls per game (Rank: {OPP_PFD_RANK})'.format(\
                    sql_oppo=sql_oppo, OPP_PFD_RANK=abs(int(oppo_allowed['OPP_PFD_RANK']) - 29),OPP_PFD=oppo_allowed['OPP_PFD'])
                print '{sql_oppo} is giving up {OPP_DEF_RATING} points per game (Rank: {OPP_DEF_RANK})'.format(\
                    sql_oppo=sql_oppo, OPP_DEF_RANK=abs(int(oppo_allowed_advanced['DEF_RATING_RANK'])), OPP_DEF_RATING=oppo_allowed_advanced['DEF_RATING'])
                
                print '\n'

                # print '{oppo} is missing {num_out} player(s)'.format(oppo=sql_oppo, num_out=len(OBVIOUS_OUTS['by_team'][sql_oppo]))

                # for position in ['PG', 'SG', 'SF', 'PF', 'C']:

                #     if len(OBVIOUS_OUTS['by_position'][sql_oppo][position]) > 0:
                #         out_position_players = ', '.join(OBVIOUS_OUTS['by_position'][sql_oppo][position])
                        
                #         print '{position}: {num_out}'.format(position=position, \
                #             num_out=out_position_players)

                        
                #         print 'Consideration players'
                #         print ', '.join(TEAM_DEPTH_COUNT[team][position])
                #         print '\n'


                # if len(OBVIOUS_OUTS['by_team'][team]) > 0:
                #     team_chalk_bonus += len(OBVIOUS_OUTS['by_team'][team])

                
                # print '\n'

                # print 'AVG PLAYTIME LAST 3 GAMES'
                # last_n_playtime_sorted = sorted(last_n_playtime.iteritems(), key=lambda x: x[1]['minutes_played'], reverse=True)

                # last_n_playtime_top_five = []
                    
                # for obj in last_n_playtime_sorted[:4:]:
                #     last_n_playtime_top_five.append(obj[0])

                # for obj in last_n_playtime_sorted:
                #     player_name = obj[0]
                #     player_playtime = obj[1]['minutes_played']

                #     print '{player_name}, {player_playtime}'.format(player_name=player_name, player_playtime=player_playtime)
                
                # print '\n'

                # print 'LAST GAME STARTERS'

                # for player_name, player_info in last_game_starters.iteritems():

                #     print '{player_name} ({player_usg}), {player_playtime} '.format(\
                #         player_name=player_info['name'], player_usg=player_info['usg_pct'], player_playtime=player_info['minutes_played'])
                
                # print '\n'
                
                # print 'PROBABLE STARTERS'
                # probable_starters = {}
                # starters_from_inactives = get_games_from_inactives(team)

                # if len(OUT_LIST[team]) >= 1 and len(starters_from_inactives) >= 1:
                #     starters_from_inactives_obj = {}
                #     for game in starters_from_inactives:

                #         # if in the game there was an injured player then skip it
                #         skip_game = False

                #         for player in out_from_team:
                #             if player in game:
                #                 skip_game = True

                #         if skip_game == False:
                #             for player_name, player_info in game.iteritems():

                #                 if player_name not in starters_from_inactives_obj:
                #                     starters_from_inactives_obj[player_name] = {
                #                         'minutes_played': [player_info['minutes_played']],
                #                         'usg_pct': [player_info['usg_pct']]
                                
                #                     }
                #                 else:
                #                     starters_from_inactives_obj[player_name]['minutes_played'].append(player_info['minutes_played'])
                #                     starters_from_inactives_obj[player_name]['usg_pct'].append(player_info['usg_pct'])   

                #     probable_starters = starters_from_inactives[0]
                #     for player_name, player_info in starters_from_inactives[0].iteritems():

                #         print '{player_name} ({player_usg}), {player_playtime} '.format(\
                #             player_name=player_info['name'], player_usg=player_info['usg_pct'], player_playtime=player_info['minutes_played'])
                    
                #     print '\n'
                # else:
                #     probable_starters = last_game_starters
                #     for player_name, player_info in last_game_starters.iteritems():

                #         print '{player_name} ({player_usg}), {player_playtime} '.format(\
                #             player_name=player_info['name'], player_usg=player_info['usg_pct'], player_playtime=player_info['minutes_played'])
                

                # sort by the median so we can get the rankings
                # chalk_obj_sorted = sorted(chalk_obj.iteritems(), key=lambda x: x[1]['median'], reverse=True)
                # pp.pprint(chalk_obj)
                for player_name, chalk_stats in chalk_obj.iteritems():
                    # player_name = obj[0]
                    # chalk_stats = obj[1]

                    if player_name not in out_from_team:
                        dk_name = player_name
                        if player_name in news_scraper.SQL_TO_DK_TRANSLATE:
                            dk_name = news_scraper.SQL_TO_DK_TRANSLATE[player_name]


                        if dk_name in dk_obj_by_position['all']:
                            salary_obj = dk_obj_by_position['all'][dk_name]
                            price_fluc = salary_obj['price_fluc']
                            avg_val = news_scraper.two_decimals(salary_obj['avg_val'])
                            salary = int(salary_obj['salary'])


                        # print '({price_fluc}) {avg_val} @ {salary}  -  {player}  -  {points_basis}pb ({median} / {value_goal})  -  {poss_played}%'.format(\
                        #     player=player_name, points_basis=chalk_stats['points_basis'], \
                        #     median=chalk_stats['median'], value_goal=chalk_stats['value_goal'], \
                        #     poss_played=chalk_stats['poss_played'], price_fluc=price_fluc, \
                        #     avg_val=avg_val, salary=salary)

                        # print 'PFD: {pfd}, PF: {pf}  -  {NBA_FANTASY_PTS}'.format(\
                        #     NBA_FANTASY_PTS=chalk_stats['fp_per_hundred'], \
                        #     pf=chalk_stats['pf'], pfd=chalk_stats['pfd'])

                        # if np.isnan(chalk_stats['past_dkm']):
                        #     print 'DNP'
                        # else:
                        #     print 'Last Match Up DKM: {past_dkm}'.format(\
                        #         past_dkm=chalk_stats['past_dkm'])


                            player_position = PLAYER_POSITIONS[player_name]
                            if  avg_val >= 2 and \
                                (chalk_stats['past_dkm'] >= 0.8 or \
                                # player_name in probable_starters or \
                                player_name in thin_depth_obj or \
                                # player_name in last_n_playtime_top_five or \
                                chalk_stats['min'] >= 25 or \
                                chalk_stats['rank'] <= 5 or \
                                # chalk_stats['lineup_rank'] <= 5 or \
                                player_name in pre_post_injury_depth_chart[team] or \
                                (player_name in last_n_playtime and last_n_playtime[player_name]['minutes_played'] >= 22)):
                                
                                num_recent = 3

                                # ordered by latest first @ [0]
                                last_n_game_usg = get_last_n_game_usg(team, player_name, num_recent)
                                
                                try:
                                    avg_fp_min = chalk_stats['avg_fp'] / chalk_stats['min']
                                except ZeroDivisionError:
                                    avg_fp_min = 0
                                
                                risk_count = 0

                                # if player_name in last_n_playtime:

                                    # med_min_last_three = last_n_playtime[player_name]['minutes_played']

                                    # proj_last_dkm = news_scraper.two_decimals(float(med_min_last_three) * float(chalk_stats['past_dkm']))
                                    # proj_avg_dkm = news_scraper.two_decimals(float(med_min_last_three) * float(avg_fp_min))
                                    # proj_last_dkm_max = news_scraper.two_decimals(float(med_min_last_three) * float(chalk_stats['max_dkm']))
                                    # proj_last_dkm_min = news_scraper.two_decimals(float(med_min_last_three) * float(chalk_stats['min_dkm']))
                                    # if med_min_last_three < 25:
                                    #     less_than_tf = True
                                    #     added_risk = '(<25)'
                                    #     risk_count -= 1
                                    # else:
                                    #     less_than_tf = False
                                    #     added_risk = ''
                                    #     risk_count = 0
                                # else:
                                proj_last_dkm = 0
                                proj_last_dkm_max = 0
                                proj_last_dkm_min = 0
                                # med_min_last_three = 0
                                less_than_tf = True
                                added_risk = ''
                                risk_count = 0
                                
                                super_boosted = False
                                boosted = False
                                
                                if player_name in pre_post_injury_depth_chart[team]:
                                    if pre_post_injury_depth_chart[team][player_name]['diff'] >= 1:
                                        super_boosted = True
                                    else:
                                        boosted = True
                                else:
                                    super_boosted = False
                                    boosted = False


                                FAVOR_OBJ[player_position][player_name] = {
                                    'player' : player_name,
                                    'points_basis' : chalk_stats['points_basis'],
                                    'median' : chalk_stats['median'],
                                    'value_goal' : chalk_stats['value_goal'],
                                    'poss_played' : chalk_stats['poss_played'],
                                    'price_fluc' : price_fluc,
                                    'avg_val' : avg_val,
                                    # 'dkm_ranking': idx+1,
                                    'salary' : salary,
                                    'avg_min' : chalk_stats['min'],
                                    # 'med_min_last_three' : med_min_last_three,
                                    'avg_fp_min': avg_fp_min,
                                    'dkm' : chalk_stats['past_dkm'],
                                    'max_dkm' : chalk_stats['max_dkm'],
                                    'rank' : chalk_stats['rank'],
                                    # 'lineup_rank' : chalk_stats['lineup_rank'],
                                    'oppo' : sql_oppo,
                                    'team' : team,
                                    'super_boosted': super_boosted,
                                    'med_usg': np.median(last_n_game_usg),
                                    'boosted': boosted,
                                    'less_than_tf': less_than_tf,
                                    # 'proj_avg_dkm': proj_avg_dkm,
                                    # 'proj_last_dkm': proj_last_dkm,
                                    # 'proj_last_dkm_max': proj_last_dkm_max,
                                    # 'proj_last_dkm_min': proj_last_dkm_min,
                                    'added_risk' : added_risk,
                                    'risk_count' : risk_count,
                                    # 'proj_val' : news_scraper.two_decimals(float(proj_last_dkm)/(0.001*float(salary))),
                                    'oppo_def_rank': abs(int(oppo_allowed_advanced['DEF_RATING_RANK'])),
                                    # 'last_starter' : '^' if player_name in last_game_starters else '',
                                    # 'proj_last_dkm_start' : news_scraper.two_decimals(float(last_one_playtime[player_name]['minutes_played']) * float(chalk_stats['past_dkm'])) if player_name in last_one_playtime else 0,
                                    # 'proj_last_dkm_start_max' : news_scraper.two_decimals(float(last_one_playtime[player_name]['minutes_played']) * float(chalk_stats['max_dkm'])) if player_name in last_one_playtime else 0,
                                    # 'proj_last_dkm_start_min' : news_scraper.two_decimals(float(last_one_playtime[player_name]['minutes_played']) * float(chalk_stats['min_dkm']) if player_name in last_one_playtime else 0)
                                }

            
            print 'Weak / Forced Position Players:'
            
            for player_name, player_info in thin_depth_obj.iteritems():
                print '{team} {position}: {player_name}'.format(player_name=player_name, \
                    position=player_info['position'], team=player_info['team'])

            print '\n'

            # vegas_lines = print_vegas_lines(today_date, sql_teams_playing)
            csv_obj = {}

            # vegas_weighted_score_list = []
            # for position, position_players in FAVOR_OBJ.iteritems():

            #     for player_name, player_info in position_players.iteritems():
            #         player_info['vegas_diff'] = vegas_lines[player_info['team']]['proj_diff'] if player_info['team'] in vegas_lines else 0
            #         player_info['vegas_reg_weighted_score'] = vegas_lines[player_info['team']]['reg_weighted_score'] if player_info['team'] in vegas_lines else 0
            #         player_info['ou_score'] = vegas_lines[player_info['team']]['ou_score'] if player_info['team'] in vegas_lines else 0

            #         if player_info['vegas_reg_weighted_score'] not in vegas_weighted_score_list:
            #             vegas_weighted_score_list.append(player_info['vegas_reg_weighted_score'])
            
            # vegas_weighted_score_list = sorted(vegas_weighted_score_list)

            csv_position = {}
            for position, position_players in FAVOR_OBJ.iteritems():
                csv_position[position] = {}
                # print position_players
                # chalk_obj_sorted = sorted(position_players.iteritems(), key=lambda x: (x[1]['super_boosted'], x[1]['boosted'], x[1]['vegas_reg_weighted_score']), reverse=True)

                # for obj in chalk_obj_sorted:
                for player_name, player_info in position_players.iteritems():
                    # player_name = obj[0]
                    # player_info = obj[1]

                    num_recent = 3

                    # last_one_playtime = get_last_game(player_info['team'], 1)

                    bypass_game = []
                    # ordered by latest first @ [0]
                    last_n_game_usg = get_last_n_game_usg(player_info['team'], player_name, num_recent)
                    # string.join connects elements inside list of strings, not ints.
                    filtered_last_n_game_usg = []
                    for idx, usage in enumerate(last_n_game_usg):
                        if usage > np.median(last_n_game_usg) * 1.5:
                            bypass_game.append(idx)
                            continue
                        else:
                            filtered_last_n_game_usg.append(usage)

                    last_n_game_usg_str = ', '.join(str(v) for v in filtered_last_n_game_usg)


                    last_n_game_dk = get_last_n_game_dk(player_name, num_recent)
                    filtered_last_n_dk = []
                    for idx, game in enumerate(last_n_game_dk):

                        if idx in bypass_game:
                            continue
                        else:
                            filtered_last_n_dk.append(game['dk_points'])
                    avg_val_n = news_scraper.two_decimals(float(np.average(filtered_last_n_dk))/(0.001*float(player_info['salary'])))

                    # last_n_game_dk_str = ', '.join(str(v) for v in filtered_last_n_dk)
                    # if player_info['team'] in DIFF_OUTS and len(DIFF_OUTS[player_info['team']]['removed']) >= 1:
                    #     removed_injury_str = ', '.join(str(v) for v in DIFF_OUTS[player_info['team']]['removed'])
                    # else:
                    #     removed_injury_str = ''

                    # if player_info['team'] in DIFF_OUTS and len(DIFF_OUTS[player_info['team']]['added']) >= 1:
                    #     added_injury_str = ', '.join(str(v) for v in DIFF_OUTS[player_info['team']]['added'])
                    # else:
                    #     added_injury_str = ''

                    #  how many minutes do they need to play to make value based on past dkm mid&max
                    
                    # and that the roster have no injuries and is not a limited player
                    depth_team = player_info['team']
                    if player_info['team'] in news_scraper.REVERSE_TRANSLATE_DICT:
                        depth_team = news_scraper.REVERSE_TRANSLATE_DICT[player_info['team']]

                    # vegas_diff = player_info['vegas_diff']
                    # vegas_reg_weighted_score = player_info['vegas_reg_weighted_score']
                    # # vegas_reg_weighted_score = 20
                    # ou_score = player_info['ou_score']

                    # playing_players = ALL_TEAM_PLAYERS[depth_team]['by_role']['starters'] + ALL_TEAM_PLAYERS[depth_team]['by_role']['rotation']
                    
                    # # if (player_name not in pre_post_injury_depth_chart[player_info['team']] or player_info['rank'] > 5) and \
                    # #     (player_info['less_than_tf'] == True and \
                    # #     np.median(last_n_game_usg) <= 5):
                    # #     continue

                    # proj_val_max = news_scraper.two_decimals(float(player_info['proj_last_dkm_max'])/(0.001*float(player_info['salary'])))
                    # proj_val_start = news_scraper.two_decimals(float(player_info['proj_last_dkm_start'])/(0.001*float(player_info['salary'])))
                    # proj_val_start_max = news_scraper.two_decimals(float(player_info['proj_last_dkm_start_max'])/(0.001*float(player_info['salary'])))
                    
                    # if player_info['dkm'] > 0:
                    #     min_need = news_scraper.two_decimals(float(player_info['value_goal'])/(float(player_info['dkm'])))
                    # elif player_info['avg_fp_min'] > 0 and player_info['dkm'] == 0 and player_info['max_dkm'] == 0:
                    #     min_need = news_scraper.two_decimals(float(player_info['value_goal'])/(float(player_info['avg_fp_min'])))
                    # else:
                    #     min_need = '---'

                    # # if your OU is last then no matter what it cannot be greater than 15

                    # min_need_max = news_scraper.two_decimals(float(player_info['value_goal'])/(float(player_info['max_dkm']))) if player_info['max_dkm'] > 0 else '---'

                    # if player_info['last_starter'] != '':
                    #     default_exposure = 100
                    # elif player_name in last_one_playtime and last_one_playtime[player_name]['minutes_played'] >= 30:
                    #     default_exposure = 60
                    # else:
                    #     player_info['risk_count'] -= 1
                    #     default_exposure = 40
                    
                    # if player_info['last_starter'] != '' and (player_name in last_one_playtime and last_one_playtime[player_name]['minutes_played'] < 25):
                    #     default_exposure = 40

                    # additional_stars = ''
                    # if player_info['super_boosted'] == True:                        
                    #     additional_stars += '*****/{num_players}'.format(num_players=NUM_AVAIL_PLAYERS[player_info['team']])
                    # if player_info['boosted'] == True:
                    #     additional_stars += '**/{num_players}'.format(num_players=NUM_AVAIL_PLAYERS[player_info['team']])


                    # if player_info['avg_val'] >= 5.2 or avg_val_n >= 5.2:
                    #     additional_stars += '$$$$$'

                    # if player_info['oppo_def_rank'] >= 20:
                    #     additional_stars += '!'

                    # if vegas_reg_weighted_score < np.median(vegas_weighted_score_list):

                    #     if player_info['last_starter'] != '':
                    #         default_exposure = 30
                    #     else:
                    #         default_exposure = 20

                    #     if player_info['super_boosted'] == True:
                    #         default_exposure = 100

                    #     if player_info['less_than_tf'] == True and (player_info['super_boosted'] != True or player_info['boosted'] != True):
                    #         default_exposure -= 10

                    #     # if player_info['salary'] < 6700:
                    #     #     default_exposure -= 5
                    #     #     # meaning you avg at least 30 you have to be considered
                    #     #     # player_info['added_risk'] += '(<10)'
                    #     #     player_info['risk_count'] -= 1
                        
                    #     # if starter_missing:
                    #         # you have to be somewhat considered
                    #     if player_info['avg_val'] < 4:
                    #         player_info['risk_count'] -= 1

                    #     if max(proj_val_start, player_info['proj_val']) < 5:
                    #         default_exposure -= 5


                    # else:
                    #     if player_info['super_boosted'] == True:
                    #         default_exposure = 100

                    #     if player_info['less_than_tf'] == True and player_info['super_boosted'] != True:
                    #         default_exposure -= 30

                    #     if max(proj_val_start, player_info['proj_val']) < 5:
                    #         default_exposure -= 10

                    #     if player_info['avg_val'] < 4:
                    #         player_info['risk_count'] -= 1
                    #         default_exposure -= 15


                    # if min_need_max > player_info['med_min_last_three']:
                    #     player_info['risk_count'] -= 1
                    #     default_exposure -= 10

                    # if player_info['super_boosted'] == True:
                    #     default_exposure += 10


                    # if np.median(filtered_last_n_dk) < (player_info['salary'] * 5 / 1000):
                    #     # but the most recent is greater than six
                    #     # possible TRAP
                    #     player_info['risk_count'] -= 1

                    #     if filtered_last_n_dk[0] <= (player_info['salary'] * 6 / 1000):
                    #         default_exposure -= 15
                    #         # player_info['added_risk'] += '(<10)'
                    #     else:
                    #         default_exposure -= 5
                    #         player_info['added_risk'] += 'TRAPPP?!?!'

                    # if player_info['dkm'] < 0.8:
                    #     default_exposure -= 10

                    # if player_info['med_usg'] <= 18:
                    #     default_exposure -= 10

                    avg_usg = sqlfetch.execute_query(sqlfetch.get_player_avg_usg(FIRST_DATE_REG_SEASON, LAST_DATE_REG_SEASON, player_name))[0]['AVG_USG']
                    # if len(filtered_last_n_game_usg) >= 1:
                    #     usg_pct_diff = abs((1 - (filtered_last_n_game_usg[0] / player_info['med_usg'])) * 100)

                    #     if usg_pct_diff >= 39.5:
                    #         player_info['risk_count'] -= 1
                    #         player_info['added_risk'] += 'TRAPPP?!?!'

                    #         if abs((1 - (filtered_last_n_game_usg[0] /avg_usg) * 100)) >= 39.5:
                    #             default_exposure -= 15

                    
                    
                    # if player_info['last_starter'] != '' and player_info['avg_val'] >= 5.2:
                    #     default_exposure += 10

                    # if min_need <= player_info['med_min_last_three'] or (player_name in last_one_playtime and min_need <= last_one_playtime[player_name]['minutes_played']):
                    #     default_exposure += 15
                    #     additional_stars += '@@'


                    # if player_info['super_boosted'] == True and player_info['lineup_rank'] <= 3:
                    #     if default_exposure <= 10:
                    #         default_exposure = 25           
                    # elif player_info['boosted'] == True and player_info['lineup_rank'] <= 3:
                    #     if default_exposure <= 10:
                    #         default_exposure = 15  

                    # if he hasnt hit that projection (within a 20% tolerance) pick the lowest one
                    # defensive ranking hit

                    csv_position[position][player_name] = {
                        # 'vegas_reg_weighted_score': vegas_reg_weighted_score,
                        'projection': 0,
                        'position': position,
                        'risk_count': player_info['risk_count'],
                        'usg': player_info['med_usg'] if (avg_val_n >= 2 or player_info['super_boosted'] == True or player_info['boosted'] == True) else avg_usg,
                        'starter': True if player_name in ALL_TEAM_PLAYERS[depth_team]['by_role']['starters'] else False,
                        'dkm': player_info['dkm'],
                        'rank': player_info['rank'],
                        'oppo_def_rank':player_info['oppo_def_rank'],
                        # 'lineup_rank': player_info['lineup_rank']
                    }
                    fouls = sqlfetch.execute_query(sqlfetch.get_player_pf(FIRST_DATE_REG_SEASON, player_name))[0]
                    pfd = fouls['AVG_PFD']
                    csv_obj[player_name] = {
                        # 'vegas_reg_weighted_score': vegas_reg_weighted_score,
                        'projection': 0,
                        'position': position,
                        'risk_count': player_info['risk_count'],
                        'avg_val': player_info['avg_val'],
                        'avg_val_n': avg_val_n,
                        'starter': True if player_name in ALL_TEAM_PLAYERS[depth_team]['by_role']['starters'] else False,
                        'team': player_info['team'],
                        'changed': True if player_info['team'] in changed_team else False,
                        'pfd': pfd,
                        'oppo_def_rank':player_info['oppo_def_rank'],
                        'usg': player_info['med_usg'] if (avg_val_n >= 2 or player_info['super_boosted'] == True or player_info['boosted'] == True) else avg_usg,
                        'dkm': player_info['dkm'],
                        'rank': player_info['rank'],
                        'salary': player_info['salary']
                        # 'lineup_rank': player_info['lineup_rank']
                    }
                    # smallest_estimate = min(player_info['proj_last_dkm'], player_info['proj_last_dkm_max'], player_info['proj_last_dkm_start'], player_info['proj_last_dkm_start_max'])
                    # highest_estimate = max(player_info['proj_last_dkm'], player_info['proj_last_dkm_max'], player_info['proj_last_dkm_start'], player_info['proj_last_dkm_start_max'])

                    # a = (player_info['proj_last_dkm'] + player_info['proj_last_dkm_max']) / 2
                    # b = (player_info['proj_last_dkm_start'] + player_info['proj_last_dkm_start_max']) / 2

                    # bigger_estimate = max(a, b)
                    # smaller_estimate = min(a, b)

                    
                    # if len(filtered_last_n_game_usg) >= 1:
                    #     if bigger_estimate == 0  and smaller_estimate == 0:
                    #         csv_obj[player_name]['projection'] = np.median(filtered_last_n_dk)
                    #     elif a != 0 and b == 0:
                    #         csv_obj[player_name]['projection'] = a
                    #     elif a == 0 and b != 0:
                    #         csv_obj[player_name]['projection'] = b
                    #     else:
                    #         pct_diff = abs((1 - (bigger_estimate / smaller_estimate)) * 100)

                    #         if pct_diff <= 25:
                    #             if player_info['med_usg'] <= 15:
                    #                 csv_obj[player_name]['projection'] = smallest_estimate
                    #             else:
                    #                 csv_obj[player_name]['projection'] = bigger_estimate

                    #         else:
                    #             if player_info['med_usg'] <= 15:
                    #                 csv_obj[player_name]['projection'] = smallest_estimate
                    #             else:
                    #                 csv_obj[player_name]['projection'] = smaller_estimate

                    
                    # if player_name in pre_post_injury_depth_chart[player_info['team']]:
                    #     # take the highest celing with accordance to the max of this season if it surpasses it
                    #     csv_obj[player_name]['projection'] = highest_estimate

                    # if it hasn't reached for ANY of the recent games
                    # not_reached_count = 0
                    # reached_count = 0
                    # for dk_score in filtered_last_n_dk:
                    #     if csv_obj[player_name]['projection'] > dk_score:
                    #         not_reached_count +=1
                    #     # if it did reached for the median of the recent games
                    #     if csv_obj[player_name]['projection'] <= dk_score:
                    #         reached_count +=1
                        
                        # if (player_info['salary'] * 6 / 1000) <= dk_score:
                        #     csv_obj[player_name]['exposure'] += 5
                        #     csv_position[position][player_name]['exposure'] += 5

                    # # if you havent been reaching value and 
                    # if not_reached_count == num_recent:
                    #     csv_obj[player_name]['projection'] = np.median(filtered_last_n_dk)

                    # if not_reached_count == num_recent or reached_count == num_recent:
                    #     bigger_score = max(csv_obj[player_name]['projection'], np.median(filtered_last_n_dk))
                    #     smaller_score = min(csv_obj[player_name]['projection'], np.median(filtered_last_n_dk))

                    #     try:
                    #         pct_diff = abs((1 - (bigger_score / smaller_score)) * 100)
                    #     except ZeroDivisionError:
                    #         pct_diff = 0

                    #     if pct_diff > 17:
                    #         player_info['risk_count'] -= 1

                    #         # if reached_count == num_recent:
                    #         csv_obj[player_name]['projection'] = np.median(filtered_last_n_dk)
                            
                            # if player_name not in pre_post_injury_depth_chart[player_info['team']]:
                            #     csv_obj[player_name]['exposure'] -= 10
                            #     csv_position[position][player_name]['exposure'] -= 10
                        

                    # game boost?
                    # if vegas_reg_weighted_score > np.median(vegas_weighted_score_list):
                    #     boost_list = [4,2,1]

                    #     boost_index = vegas_weighted_score_list.index(vegas_reg_weighted_score)

                    #     if boost_index <= 2 and player_info['med_usg'] > 15:
                    #         csv_obj[player_name]['projection'] += boost_list[boost_index]


                    # csv_position[position][player_name]['projection'] = csv_obj[player_name]['projection']

                    # value based on projection
                    # projected_value = news_scraper.two_decimals(float(csv_obj[player_name]['projection'])/(0.001*float(player_info['salary'])))
                    # csv_position[position][player_name]['projected_value'] = projected_value
                    # if projected_value >= 5.2 and player_info['med_usg'] >= 20:
                    #     additional_stars += '~~~~~'


                    # incororate the matchups code that i had previously

                    # print default_exposure
                    # if len(DIFF_OUTS[player_info['team']]['added']) > 1 and len(DIFF_OUTS[player_info['oppo']]['added']) > 1:

                    # check for the value positions

                    # later on in the season playoff contention matters. 
                    # compare with the new/old out lists and also display who is out 
                    # lineup_add = ''
                    # if player_info['team'] in DIFF_INJURY_LINEUPS \
                    #     and player_name in DIFF_INJURY_LINEUPS[player_info['team']] \
                    #     and DIFF_INJURY_LINEUPS[player_info['team']][player_name]['diff'] > 0:
                    #     lineup_add = '+' + str(DIFF_INJURY_LINEUPS[player_info['team']][player_name]['diff'])

                    # print this after another round of processing ?
                    # print '[r:{risk_count}] +[{added_injury_str}] -[{removed_injury_str}] {last_starter}{additional_stars}{added_risk} ({avg_val}/{avg_val_n}) @ {salary} {player} ({proj_min} | {proj} ({proj_val}) | {proj_max} ({proj_val_max}) / {proj_start} ({proj_val_start}) | {proj_start_max} ({proj_val_start_max})) - U: {last_n_game_usg_str} - ({oppo}({oppo_def_rank}), L: {dkm}, V: {vegas_diff} ({ou_score}) / {vegas_reg_weighted_score})'.format(\
                    #     player=player_name, points_basis=player_info['points_basis'], vegas_reg_weighted_score=vegas_reg_weighted_score,\
                    #     median=player_info['median'], value_goal=player_info['value_goal'], \
                    #     added_injury_str=added_injury_str, removed_injury_str=removed_injury_str, \
                    #     poss_played=player_info['poss_played'], price_fluc=player_info['price_fluc'], \
                    #     min_need=min_need, min_need_max=min_need_max, ou_score=ou_score,\
                    #     avg_val=player_info['avg_val'], avg_val_n=avg_val_n, salary=player_info['salary'], \
                    #     risk_count=player_info['risk_count'], proj_rank=player_info['rank'], \
                    #     lineup_rank=player_info['lineup_rank'], lineup_add=lineup_add, \
                    #     oppo=player_info['oppo'], dkm=player_info['dkm'], vegas_diff=vegas_diff, \
                    #     oppo_def_rank=player_info['oppo_def_rank'], additional_stars=additional_stars, \
                    #     added_risk=player_info['added_risk'], last_starter=player_info['last_starter'], \
                    #     last_n_game_usg_str=last_n_game_usg_str, \
                    #     proj_val=player_info['proj_val'], proj_val_max=proj_val_max, \
                    #     proj_val_start=proj_val_start, proj_val_start_max=proj_val_start_max, \
                        # proj=player_info['proj_last_dkm'], proj_min=player_info['proj_last_dkm_min'], proj_max=player_info['proj_last_dkm_max'], \
                    #     proj_start=player_info['proj_last_dkm_start'], proj_start_min=player_info['proj_last_dkm_start_min'], proj_start_max=player_info['proj_last_dkm_start_max'])

                # print '\n'  


            # print '\n'

            # POSITION_RANK = {}
            # for position, position_players in csv_position.iteritems():
            #     print position

            #     position_players_sorted = sorted(position_players.iteritems(), key=lambda x: (x[1]['oppo_def_rank']), reverse=True)
            #     pos_idx = 0
            #     for obj in position_players_sorted:
            #         player_name = obj[0]
            #         values = obj[1]
            #         # if values['projection'] != None:
            #         # 
            #         # must_play = ''
            #         # if (values['lineup_rank'] == 1 or values['rank'] == 1):
            #         #     must_play = 'MUST PLAY '
                    
            #         # if np.isnan(values['usg']):
            #         #     POSITION_RANK[player_name] = 100
            #         #     csv_obj[player_name]['position_rank'] = 100

            #         # else:
            #         #     pos_idx += 1
            #         #     POSITION_RANK[player_name] = pos_idx
            #         #     csv_obj[player_name]['position_rank'] = pos_idx
            #         #     if pos_idx == 1:
            #         #         must_play = 'MUST PLAY '

            #         print '[r:{risk_count}], {player_name}'.format(player_name=player_name, \
            #             proj_rank=values['rank'], usg=values['usg'] ,risk_count=values['risk_count'])
            #     print '\n'

            # print '\n'

            # print '******* Always look at the exposure as it gives insight into who should be played based on the vegas and recent values *******'
            # print '******* USG can be better used for small slates due to limited set of players, but exposures should provide the guideline *******'
            # print '******* WARNING FOR GUYS WHO JUST CAME OFF AN INJURY *******'
            # print '******* PLAY THE GUYS WHO ARE CHALK *******'

            # print '******* POSSIBLE GAME STACKS DUE TO MULTIPLE INJURIES *******'
            # for team, team_name in POSSIBLE_GAME_STACKS.iteritems():
            #     ou_score = ''
            #     if team_name in vegas_lines:
            #         ou_score = vegas_lines[team_name]['ou_score']

            #     print team_name, ou_score 


            csv_obj_sorted = sorted(csv_obj.iteritems(), key=lambda x: (x[1]['starter'], x[1]['changed'], x[1]['oppo_def_rank'], x[1]['usg'], x[1]['avg_val']), reverse=True)
            for obj in csv_obj_sorted:
                player_name = obj[0]
                values = obj[1]
                # must_play = ''
                # if (values['lineup_rank'] == 1 or values['rank'] == 1 or values['position_rank'] == 1):
                    # must_play = 'MUST PLAY '
                    # must_play = ''

                print '({salary}) {avg_val} / {avg_val_n}, ({oppo_def_rank}), (PFD: {pfd}) [r:{risk_count}], {usg}, {player_name}'.format(player_name=player_name, \
                    proj_rank=values['rank'], salary=values['salary'], oppo_def_rank=values['oppo_def_rank'], pfd=values['pfd'], avg_val_n=values['avg_val_n'], usg=values['usg'], avg_val=values['avg_val'], risk_count=values['risk_count'])
        
        except csv.Error as e:
            sys.exit('file %s: %s' % (csv_file, e))


# news_scraper.get_updated_depth_chart()
# news_scraper.get_all_lineups()
# news_scraper.create_player_depth_table()
# news_scraper.create_oppo_stats_table()

# news_scraper.create_player_salary_log('2019-02-27', '')

init_out_players()
get_dk_money_obj('2019-06-05', 'Showdown')

# get total number of available players?

# out_from_team = OUT_LIST['PHX'] + TRADED_LIST['PHX'] + OUT_FOR_SEASON
# print process_pre_post_injury_depth_chart('PHX', out_from_team)


# out_from_team = OUT_PLAYERS + TRADED_LIST['GSW'] + OUT_FOR_SEASON

# pp.pprint(news_scraper.get_vegas_lines())
# potential stacks
# high vegas score, multiple out players / players that can benefit from the injuries
# do both team have multiple players out
# pp.pprint(diff_bw_out_lists())
