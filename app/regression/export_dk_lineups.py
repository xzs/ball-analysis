# !/usr/bin/env python
# _*_ coding:utf-8 _*_

import pprint
import logging
import glob
import operator
import json
import csv
from datetime import date, timedelta, datetime

import warnings
# explictly not show warnings
warnings.filterwarnings("ignore")

import urllib2
from bs4 import BeautifulSoup

pp = pprint.PrettyPrinter(indent=1)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_template_csv(player_id_obj):
    with open('../scrape/csv/DKSalariesTemplate.csv',) as csv_file:
        try:
            # need to improve this
            for i in range(8): # count from 0 to 7
                next(csv_file, None)

            players = csv.reader(csv_file)
            for player in players:
                player_id_obj[player[11]] = {
                    'name_id': player[10],
                    'id': player[12],
                }
            pp.pprint(player_id_obj)
            return player_id_obj
        except csv.Error as e:
            sys.exit('file %s: %s' % (csv_file, e))

def construct_dk_lineup(lineup, player_id_obj):
    lineup_list = []

    for player in lineup:
        lineup_list.append(player_id_obj[player]['name_id'])
    
    return lineup_list

def init():
    player_id_obj = read_template_csv({})
     # sample
    lineup = ['Langston Galloway', 'Garrett Temple', 'Ben McLemore', 'Skal Labissiere', 'Georgios Papagiannis']
    
    dk_positions = ['PG','SG','SF','PF','C','G','F','UTIL']
    with open('../scrape/csv/tester.csv', 'wb') as f:
        writer = csv.writer(f)
        logger.info('Writing log csv for: ')
        # write positions
        writer.writerow(dk_positions)
        # this needs to get looped for every position
        writer.writerow(construct_dk_lineup(lineup, player_id_obj))

init()