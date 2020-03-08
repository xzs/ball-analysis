# !/usr/bin/env python
# _*_ coding:utf-8 _*_
import MySQLdb
import pprint
import logging
import numpy as np
import sqlfetch
import news_scraper
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

CONTEST_NAME = 'contest-standings-81830453-showdown';
CONTEST_CUTOFF = 351

PLAYER_NAMING_EXCEPTION_LIST_NO_SUFFIX = [
    'Kelly Oubre',
    'Glenn Robinson',
    'Jaren Jackson',
    'Gary Trent',
    'Zach Norvell',
    'Dennis Smith',
    'Marvin Bagley',
    'Michael Porter',
    'Tim Hardaway',
    'Danuel House'
]

def two_decimals(num):
    return float('{0:.2f}'.format(num))

def populate_contest_position_obj(player, position, position_obj):
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
                'UTIL': {},
                'CPT': {}
            }

            player_position_obj = {
                'UTIL': {},
                'CPT': {}
            }

            player_obj = {}
            total_lineup_count = 0

            user_player_obj = {}
            player_lineup_count = 0

            num_single_lines = 0
            num_lineups_cashed = 0

            user_num_single_lines = 0
            user_num_lineups_cashed = 0

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

                if lineup_owner == 'x39sun':
                    if len(lineup) > 1:
                        player_lineup_count += 1
                        str_index = 0

                        if int(placing)  <= CONTEST_CUTOFF:
                            user_num_lineups_cashed += 1

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

                            except IndexError:
                                break

            for player in player_obj:
                num_lineups = player_obj[player]['num_lineups']
                player_obj[player]['ownership'] = two_decimals((float(num_lineups) / float(total_lineup_count)) * 100)

                # see how many "chances they are gambling on"
                if num_lineups == 1:
                    num_single_lines += 1


            print total_lineup_count
            print ''
            print 'Num cashed: %s (%s)' % (num_lineups_cashed, two_decimals((float(num_lineups_cashed) / float(total_lineup_count)) * 100))
            print ''
            print 'Num singles: %s (%s)' % (num_single_lines, two_decimals((float(num_single_lines) / float(total_lineup_count)) * 100))
            print ''
            sdo = sorted(player_obj.iteritems(), key=lambda x: (x[1]['num_lineups']), reverse=True)
            for player in sdo:
                player_name = player[0]
                values = player[1]
                ownership = two_decimals((float(values['num_lineups']) / float(total_lineup_count)) * 100)

                print '{player_name} ({ownership})'.format(player_name=player_name, ownership=ownership)


            for player in user_player_obj:
                num_lineups = user_player_obj[player]['num_lineups']
                user_player_obj[player]['ownership'] = two_decimals((float(num_lineups) / float(total_lineup_count)) * 100)

                # see how many "chances they are gambling on"
                if num_lineups == 1:
                    user_num_single_lines += 1

            # user
            print player_lineup_count
            print ''
            print 'Num cashed: %s (%s)' % (user_num_lineups_cashed, two_decimals((float(user_num_lineups_cashed) / float(player_lineup_count)) * 100))
            print ''
            print 'Num singles: %s (%s)' % (user_num_single_lines, two_decimals((float(user_num_single_lines) / float(player_lineup_count)) * 100))
            print ''
            sdo = sorted(user_player_obj.iteritems(), key=lambda x: (x[1]['num_lineups']), reverse=True)
            for player in sdo:
                player_name = player[0]
                values = player[1]
                ownership = two_decimals((float(values['num_lineups']) / float(player_lineup_count)) * 100)
                print '{player_name} ({ownership})'.format(player_name=player_name, ownership=ownership)


        except csv.Error as e:
            sys.exit('file %s: %s' % (csv_file, e))

print_dk_obj()