# !/usr/bin/env python
# _*_ coding:utf-8 _*_
import MySQLdb
import pprint
import logging
import numpy as np
import requests
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

pp = pprint.PrettyPrinter(indent=1)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
SEASON = '2019-20'
SEASON_TYPE = 'Regular Season'

TEAM_ID_OBJ = {
    'ATL': 1610612737,
    'BKN': 1610612751,
    'BOS': 1610612738,
    'CHA': 1610612766,
    'CHI': 1610612741,
    'CLE': 1610612739,
    'DAL': 1610612742,
    'DEN': 1610612743,
    'DET': 1610612765,
    'GSW': 1610612744,
    'HOU': 1610612745,
    'IND': 1610612754,
    'LAC': 1610612746,
    'LAL': 1610612747,
    'MEM': 1610612763,
    'MIA': 1610612748,
    'MIL': 1610612749,
    'MIN': 1610612750,
    'NOP': 1610612740,
    'NYK': 1610612752,
    'OKC': 1610612760,
    'ORL': 1610612753,
    'PHI': 1610612755,
    'PHX': 1610612756,
    'POR': 1610612757,
    'SAC': 1610612758,
    'SAS': 1610612759,
    'TOR': 1610612761,
    'UTA': 1610612762,
    'WAS': 1610612764
}

# team : opponent
SLATE = {
    'MIA': 'SAC',
    'UTA': 'POR'
}


PBP_URL_PREFIX = 'https://api.pbpstats.com'
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/47.0.2526.73 Chrome/47.0.2526.73 Safari/537.36"


CONTEST_NAME = 'contest-standings-85712858';
CONTEST_CUTOFF = 2764

PLAYER_NAMING_EXCEPTION_LIST_NO_SUFFIX = [
    'Kelly Oubre',
    'Glenn Robinson',
    'Jaren Jackson',
    'Gary Trent',
    'Zach Norvell',
    'Dennis Smith',
    'Marvin Bagley',
    'Michael Porter',
    'Kevin Porter',
    'Larry Nance',
    'Lonnie Walker',
    'Tim Hardaway',
    'Danuel House',
    'Derrick Jones',
    'James Ennis',
    'Harry Giles',
    'Derrick Walton',
    'Jacob Evans',
    'Otto Porter',
    'Wendell Carter'
]

DK_TO_WOWY_TRANSLATE = {

    "Sergio Rodriguez": urllib.quote(u"Sergio Rodríguez".encode("utf-8")),
    "Alex Abrines": urllib.quote(u"Álex Abrines".encode("utf-8")),
    "Jacob Evans III": "Jacob Evans",
    "Nicolas Laprovittola": "Nicol\xc3\xa1s Laprovittola",
    "Dant\xc3\xa9 Exum": "Dante Exum",
    "Timothe Luwawu-Cabarrot": "Timoth\xc3\xa9 Luwawu-Cabarrot",
    "Nicolas Brussino": "Nicol\xc3\xa1s Brussino",
    "Jose Calderon": "Jos\xc3\xa9 Calder\xc3\xb3n",
    "Guillermo Hernangomez":"Guillermo Hernang\xc3\xb3mez",    
    "Juancho Hernang\xc3\xb3mez":"Juancho Hernangomez",
    "Alex Abrines":"\xc3\x81lex Abrines",
    "Otto Porter Jr.":"Otto Porter",
    "CJ McCollum":"C.J. McCollum",
    "JJ Redick":"J.J. Redick",
    "Nene Hilario": "Nene",
    "Johnny O'Bryant III": "Johnny O'Bryant III",
    "Royce O'Neale": "Royce O'Neale",
    "Derrick Walton Jr.": "Derrick Walton Jr.",
    "Wayne Selden Jr.": "Wayne Selden Jr."
}

def get_team_rosters(team, player_team):

    team_id = TEAM_ID_OBJ[team]
    team_url = PBP_URL_PREFIX  + '/get-team-players-for-season?TeamId=%s&Season=%s&SeasonType=%s' % (team_id, SEASON, SEASON_TYPE)

    response = requests.get(team_url, headers={'User-Agent': USER_AGENT})
    data = response.json()

    # print data

    for player_id in data['players']:
        player_name = data['players'][player_id]
        # construct a new dictionary with name first
        player_team[player_name] = team

    # return player_team

def get_player_team_slate():
    roster = {}
    for team in SLATE:
        opp = SLATE[team]
        get_team_rosters(team, roster)
        get_team_rosters(opp, roster)
    
    print roster
    return roster 


def get_team_stack_obj():
    roster = {}
    for team in SLATE:
        opp = SLATE[team]
        roster[team] = 0
        roster[opp] = 0
    
    return roster 

def two_decimals(num):
    return float('{0:.2f}'.format(num))

def populate_contest_position_obj(player, position, position_obj):
    # print player
    if player in position_obj[position]:
        position_obj[position][player] += 1
    else:
        position_obj[position][player] = 1

def print_dk_obj():
    with open('../scrape/results/'+CONTEST_NAME+'.csv',) as csv_file:
        try:
            next(csv_file, None)
            lineups = csv.reader(csv_file)
            csv_obj = {}

            position_obj = {
                'C': {},
                'PF': {},
                'SF': {},
                'SG': {},
                'PG': {},
                'G': {},
                'F': {},
                'UTIL': {},
            }

            player_position_obj = {
                'C': {},
                'PF': {},
                'SF': {},
                'SG': {},
                'PG': {},
                'G': {},
                'F': {},
                'UTIL': {},
            }

            player_obj = {}
            total_lineup_count = 0

            user_player_obj = {}
            player_lineup_count = 0

            num_single_lines = 0
            num_lineups_cashed = 0

            user_num_single_lines = 0
            user_num_lineups_cashed = 0

            summary_lineup_stack_obj = []

            for data in lineups:
                lineup_owner = data[2].split(' ')[0]
                score = data[4]
                placing = data[0]
                lineup = data[5].split(' ')

                # positions are [0], [3], [6], [9], [12], [15], [18], [21]
                # if lineup_owner == 'x39sun':
                if len(lineup) > 1:
                    total_lineup_count += 1
                    str_index = 0

                    if int(placing) <= CONTEST_CUTOFF:
                        num_lineups_cashed += 1

                    for player in lineup:
                        try:
                            position = lineup[str_index]
                            str_index += 1
                            player_first_name = lineup[str_index]
                            str_index += 1
                            player_last_name = lineup[str_index]

                            player_full_name = player_first_name + ' ' + player_last_name

                            # exceptions
                            if player_full_name in PLAYER_NAMING_EXCEPTION_LIST_NO_SUFFIX:
                                str_index += 1
                                player_suffix = lineup[str_index]
                                player_full_name = player_full_name + ' ' + player_suffix
                            str_index += 1

                            if player_full_name in player_obj:
                                player_obj[player_full_name]['num_lineups'] += 1
                            else:
                                player_obj[player_full_name] = {
                                    'num_lineups': 1
                                }

                            populate_contest_position_obj(player_full_name, position, position_obj)

                        except IndexError:
                            break

                # moklovin
                # ChipotleAddict
                # papagates
                # youdacao
                # jayk123x
                # l800Eddie
                # mrgoodseats
                # CZYX
                # ThatStunna
                # TheOctopus
                # SlowQueen
                # thepriest31
                # JBCJBCJBC
                # DFS_HofbrauKing
                # BRORANNOSAURUS_FLEX
                # fjbourne
                # Awesemo
                # mazwa
                if lineup_owner == 'ChipotleAddict':
                    if len(lineup) > 1:
                        lineup_stack_obj = get_team_stack_obj()
                        player_lineup_count += 1
                        str_index = 0

                        if int(placing)  <= CONTEST_CUTOFF:
                            user_num_lineups_cashed += 1

                        # print current lineup
                        # print data[5]

                        # i want to know what kind of game stacks did they play
                        # some_random_list = []
                        for player in lineup:
                            try:
                                position = lineup[str_index]
                                str_index += 1
                                player_first_name = lineup[str_index]
                                str_index += 1
                                player_last_name = lineup[str_index]

                                player_full_name = player_first_name + ' ' + player_last_name

                                # exceptions
                                if player_full_name in PLAYER_NAMING_EXCEPTION_LIST_NO_SUFFIX:
                                    str_index += 1
                                    player_suffix = lineup[str_index]
                                    player_full_name = player_full_name + ' ' + player_suffix
                                str_index += 1

                                if player_full_name in user_player_obj:
                                    user_player_obj[player_full_name]['num_lineups'] += 1
                                else:
                                    user_player_obj[player_full_name] = {
                                        'num_lineups': 1
                                    }

                                populate_contest_position_obj(player_full_name, position, player_position_obj)
                                # some_random_list.append(player_full_name)
                                if player_full_name in DK_TO_WOWY_TRANSLATE:
                                    player_full_name = DK_TO_WOWY_TRANSLATE[player_full_name]
                                if ALL_PLAYERS[player_full_name]:
                                    player_team = ALL_PLAYERS[player_full_name]

                                    lineup_stack_obj[player_team] += 1


                            except IndexError:
                                break

                        summary_lineup_stack_obj.append(lineup_stack_obj)

            for player in player_obj:
                num_lineups = player_obj[player]['num_lineups']
                player_obj[player]['ownership'] = two_decimals((float(num_lineups) / float(total_lineup_count)) * 100)

                # see how many "chances they are gambling on"
                if num_lineups == 1:
                    num_single_lines += 1
            

            total_ownership_obj = {}

            # print total_lineup_count
            # print ''
            # print 'Num cashed: %s (%s)' % (num_lineups_cashed, two_decimals((float(num_lineups_cashed) / float(total_lineup_count)) * 100))
            # print ''
            # print 'Num singles: %s (%s)' % (num_single_lines, two_decimals((float(num_single_lines) / float(total_lineup_count)) * 100))
            # print ''
            sdo = sorted(player_obj.iteritems(), key=lambda x: (x[1]['num_lineups']), reverse=True)
            for player in sdo:
                player_name = player[0]
                values = player[1]
                ownership = two_decimals((float(values['num_lineups']) / float(total_lineup_count)) * 100)
                total_ownership_obj[player_name] = ownership

                print '{player_name} ({ownership})'.format(player_name=player_name, ownership=ownership)


            print ''
            print ''

            # basically see the types of stakcs the player played
            some_obj = {}
            for lineup_stack in summary_lineup_stack_obj:
                for team in lineup_stack:
                    num_stacked_players = lineup_stack[team]

                    if team in some_obj:
                        some_obj[team] += num_stacked_players
                    else:
                        some_obj[team] = num_stacked_players

            for team in some_obj:
                print team
                print two_decimals((float(some_obj[team]) / float(player_lineup_count)))

            for player in user_player_obj:
                num_lineups = user_player_obj[player]['num_lineups']
                user_player_obj[player]['ownership'] = two_decimals((float(num_lineups) / float(total_lineup_count)) * 100)

                # see how many "chances they are gambling on"
                if num_lineups == 1:
                    user_num_single_lines += 1

            # user
            print
            print player_lineup_count
            print 'Num cashed: %s (%s)' % (user_num_lineups_cashed, two_decimals((float(user_num_lineups_cashed) / float(player_lineup_count)) * 100))
            print 'Num singles: %s (%s)' % (user_num_single_lines, two_decimals((float(user_num_single_lines) / float(player_lineup_count)) * 100))
            print 
            sdo = sorted(user_player_obj.iteritems(), key=lambda x: (x[1]['num_lineups']), reverse=True)
            for player in sdo:
                player_name = player[0]
                values = player[1]
                ownership = two_decimals((float(values['num_lineups']) / float(player_lineup_count)) * 100)
                diff_ownership = ownership - total_ownership_obj[player_name]
                print '{player_name} ({ownership}), ({diff_ownership})'.format(player_name=player_name, ownership=ownership, diff_ownership=diff_ownership)


        except csv.Error as e:
            sys.exit('file %s: %s' % (csv_file, e))

# ALL_PLAYERS = get_player_team_slate()
ALL_PLAYERS = {u'Jaylen Hoard': 'POR', u'DaQuan Jeffries': 'SAC', u'Gary Trent Jr.': 'POR', u'Jarrell Brantley': 'UTA', u'Jeff Green': 'UTA', u'Tony Bradley': 'UTA', u'Moses Brown': 'POR', u'Tyler Herro': 'MIA', u'Richaun Holmes': 'SAC', u'James Johnson': 'MIA', u"Royce O'Neale": 'UTA', u'Rayjon Tucker': 'UTA', u'Zach Collins': 'POR', u'Wenyen Gabriel': 'POR', u'Eric Mika': 'SAC', u'Kent Bazemore': 'POR', u'Ed Davis': 'UTA', u'Skal Labissiere': 'POR', u'Nemanja Bjelica': 'SAC', u'Harry Giles III': 'SAC', u'Donovan Mitchell': 'UTA', u'Stanton Kidd': 'UTA', u'Nassir Little': 'POR', u'Dewayne Dedmon': 'SAC', u'Caleb Swanigan': 'POR', u'Udonis Haslem': 'MIA', u'Bojan Bogdanovic': 'UTA', u'C.J. McCollum': 'POR', u'KZ Okpala': 'MIA', u'Kyle Guy': 'SAC', u'Harrison Barnes': 'SAC', u'Duncan Robinson': 'MIA', u'Chris Silva': 'MIA', u'Yogi Ferrell': 'SAC', u'Derrick Jones Jr.': 'MIA', u'Daryl Macon': 'MIA', u'Hassan Whiteside': 'POR', u'Justin James': 'SAC', u'Jordan Clarkson': 'UTA', u'Goran Dragic': 'MIA', u'Meyers Leonard': 'MIA', u'Marvin Bagley III': 'SAC', u'Mario Hezonja': 'POR', u'Anthony Tolliver': 'POR', u'Jimmy Butler': 'MIA', u'Juwan Morgan': 'UTA', u'Georges Niang': 'UTA', u'Carmelo Anthony': 'POR', u'Bogdan Bogdanovic': 'SAC', u'Dante Exum': 'UTA', u'Damian Lillard': 'POR', u'Emmanuel Mudiay': 'UTA', u'Bam Adebayo': 'MIA', u'Anfernee Simons': 'POR', u'Justise Winslow': 'MIA', u'Miye Oni': 'UTA', u'Buddy Hield': 'SAC', u'Trevor Ariza': 'POR', u'Mike Conley': 'UTA', u'Cory Joseph': 'SAC', u'Rudy Gobert': 'UTA', u"De'Aaron Fox": 'SAC', u'Gabe Vincent': 'MIA', u'Kelly Olynyk': 'MIA', u'Nigel Williams-Goss': 'UTA', u'Kendrick Nunn': 'MIA', u'Joe Ingles': 'UTA', u'Rodney Hood': 'POR', u'Dion Waiters': 'MIA'}


# print ALL_PLAYERS
print_dk_obj()