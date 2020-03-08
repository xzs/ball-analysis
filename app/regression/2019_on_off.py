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

today_date = date.today()
week_ago = today_date - timedelta(days=9)

SEASON = '2019-20'
SEASON_TYPE = 'Regular Season'

OLD_OUT_LIST = {
    'ATL': ['Evan Turner','Jabari Parker', 'Alex Len', 'Allen Crabbe', "DeAndre' Bembry", 'Trae Young'],
    'BOS': ['Robert Williams III', 'Jaylen Brown', 'Gordon Hayward', 'Kemba Walker'],
    'BKN': ['Iman Shumpert', 'David Nwaba', 'Kyrie Irving', 'Garrett Temple'],
    'CHA': ['Marvin Williams', 'Michael Kidd-Gilchrist', 'Malik Monk'],
    'CHI': ['Kris Dunn', 'Chandler Hutchison', 'Luke Kornet', 'Zach LaVine'],
    'CLE': ['Jordan Clarkson', 'Ante Zizic', 'Brandon Knight', 'John Henson', 'Alfonzo McKinnie', 'Tristan Thompson', 'Andre Drummond', 'Darius Garland'],
    'DAL': ['Dwight Powell', 'Ryan Broekhoff', 'Jalen Brunson', 'Dorian Finney-Smith'],
    'DEN': ['Malik Beasley', 'Juancho Hernangomez', 'Jarred Vanderbilt'],
    'DET': ['Blake Griffin', 'Andre Drummond', 'Reggie Jackson', 'Markieff Morris', 'Derrick Rose', 'Luke Kennard', 'Bruce Brown'],
    'GSW': ['Willie Cauley-Stein', 'Alec Burks', 'Glenn Robinson III', "D'Angelo Russell", 'Omari Spellman', 'Jacob Evans', 'Kevon Looney', 'Ky Bowman', 'Jeremy Pargo'],
    'HOU': ['Ryan Anderson', 'Gary Clark', 'Clint Capela'],
    'IND': ['Jeremy Lamb', 'Doug McDermott', 'Malcolm Brogdon', 'T.J. Warren'],
    'LAC': ['Maurice Harkless'],
    'LAL': [],
    'MEM': ['Grayson Allen', 'Solomon Hill', 'Jae Crowder', 'Bruno Caboclo', 'Jaren Jackson Jr.', 'Brandon Clarke'],
    'MIA': ['Justise Winslow', 'James Johnson', 'Dion Waiters', 'Tyler Herro', 'Meyers Leonard'],
    'MIL': [],
    'MIN': ['Jeff Teague', 'Treveon Graham', 'Jordan Bell', 'Shabazz Napier', 'Robert Covington', 'Keita Bates-Diop', 'Noah Vonleh', 'Allen Crabbe', 'Andrew Wiggins', 'Karl-Anthony Towns'],
    'NOP': ['Kenrich Williams', 'JJ Redick'],
    'NYK': ['Marcus Morris Sr.', 'Dennis Smith Jr.', 'Mitchell Robinson'],
    'OKC': ['Darius Bazley', 'Danilo Gallinari'],
    'ORL': ['Al-Farouq Aminu', 'Jonathan Isaac', 'Josh Magette', 'Evan Fournier'],
    'PHI': ['Trey Burke', 'James Ennis III', 'Ben Simmons', 'Joel Embiid', 'Josh Richardson'],
    'PHX': ['Tyler Johnson', 'Frank Kaminsky', 'Kelly Oubre Jr.', 'Deandre Ayton', 'Cameron Johnson'],
    'POR': ['Zach Collins', 'Rodney Hood', 'Skal Labissiere', 'Kent Bazemore', 'Anthony Tolliver'],
    'SAC': ['Trevor Ariza', 'Marvin Bagley III', 'Caleb Swanigan', 'Wenyen Gabriel', 'Richaun Holmes', 'Dewayne Dedmon'],
    'SAS': ['LaMarcus Aldridge', 'Marco Belinelli'],
    'TOR': ['Marc Gasol', 'Stanley Johnson', 'Fred VanVleet'],
    'UTA': ['Dante Exum', 'Jeff Green'],
    'WAS': ['CJ Miles', 'Jordan McRae', 'Isaiah Thomas', 'Ish Smith']
}

OUT_LIST = {
    'ATL': ['Evan Turner','Jabari Parker', 'Alex Len', 'Allen Crabbe', "DeAndre' Bembry"],
    'BOS': ['Robert Williams III', 'Jaylen Brown', 'Gordon Hayward', 'Kemba Walker'],
    'BKN': ['Iman Shumpert', 'David Nwaba', 'Kyrie Irving', 'Garrett Temple'],
    'CHA': ['Marvin Williams', 'Michael Kidd-Gilchrist', 'Malik Monk'],
    'CHI': ['Kris Dunn', 'Chandler Hutchison', 'Luke Kornet', 'Zach LaVine'],
    'CLE': ['Jordan Clarkson', 'Ante Zizic', 'Brandon Knight', 'John Henson', 'Alfonzo McKinnie', 'Andre Drummond', 'Darius Garland', 'Kevin Porter Jr.'],
    'DAL': ['Dwight Powell', 'Ryan Broekhoff', 'Jalen Brunson', 'Dorian Finney-Smith'],
    'DEN': ['Malik Beasley', 'Juancho Hernangomez', 'Jarred Vanderbilt'],
    'DET': ['Blake Griffin', 'Andre Drummond', 'Reggie Jackson', 'Markieff Morris', 'Luke Kennard', 'Derrick Rose'],
    'GSW': ['Willie Cauley-Stein', 'Alec Burks', 'Glenn Robinson III', "D'Angelo Russell", 'Omari Spellman', 'Jacob Evans', 'Kevon Looney', 'Ky Bowman', 'Jeremy Pargo', 'Draymond Green'],
    'HOU': ['Ryan Anderson', 'Gary Clark', 'Clint Capela', 'Eric Gordon'],
    'IND': ['Jeremy Lamb', 'Doug McDermott', 'Malcolm Brogdon', 'T.J. Warren'],
    'LAC': ['Maurice Harkless'],
    'LAL': [],
    'MEM': ['Grayson Allen', 'Solomon Hill', 'Jae Crowder', 'Bruno Caboclo', 'Jaren Jackson Jr.', 'Brandon Clarke'],
    'MIA': ['Justise Winslow', 'James Johnson', 'Dion Waiters', 'Tyler Herro', 'Meyers Leonard'],
    'MIL': [],
    'MIN': ['Jeff Teague', 'Treveon Graham', 'Jordan Bell', 'Shabazz Napier', 'Robert Covington', 'Keita Bates-Diop', 'Noah Vonleh', 'Allen Crabbe', 'Andrew Wiggins', 'Karl-Anthony Towns'],
    'NOP': ['Kenrich Williams', 'JJ Redick'],
    'NYK': ['Marcus Morris Sr.', 'Dennis Smith Jr.', 'Mitchell Robinson'],
    'OKC': ['Darius Bazley', 'Danilo Gallinari'],
    'ORL': ['Al-Farouq Aminu', 'Jonathan Isaac', 'Josh Magette', 'Evan Fournier'],
    'PHI': ['Trey Burke', 'James Ennis III', 'Ben Simmons', 'Joel Embiid', 'Josh Richardson'],
    'PHX': ['Tyler Johnson', 'Frank Kaminsky', 'Kelly Oubre Jr.', 'Deandre Ayton', 'Cameron Johnson'],
    'POR': ['Zach Collins', 'Rodney Hood', 'Skal Labissiere', 'Kent Bazemore', 'Anthony Tolliver'],
    'SAC': ['Trevor Ariza', 'Marvin Bagley III', 'Caleb Swanigan', 'Wenyen Gabriel', 'Richaun Holmes', 'Dewayne Dedmon'],
    'SAS': ['LaMarcus Aldridge', 'Marco Belinelli'],
    'TOR': ['Marc Gasol', 'Stanley Johnson', 'Fred VanVleet'],
    'UTA': ['Dante Exum', 'Jeff Green'],
    'WAS': ['CJ Miles', 'Jordan McRae', 'Isaiah Thomas', 'Ish Smith']
}

# one thing we can do here is be more specific about the positions
ON_FLOOR = {
    'ATL': {
        'Trae Young': 38,
        'John Collins': 36,
        'Kevin Huerter': 36,
        "Dewayne Dedmon": 22,
        "De'Andre Hunter": 34
    },
    'BOS': {
        'Jaylen Brown': 36,
        'Marcus Smart': 36,
        'Jayson Tatum': 38,
        'Gordon Hayward': 38,
        'Daniel Theis': 30
    },
    'BKN': {
        'Spencer Dinwiddie': 34,
        'Joe Harris': 32,
        'Caris LeVert': 34,
        'Jarrett Allen': 29,
        'Taurean Prince': 30
    },
    'CHA': {
        "Devonte' Graham": 33,
        'Terry Rozier': 33,
        'Miles Bridges': 35,
        'P.J. Washington': 32,
        'Cody Zeller': 26
    },
    'CHI': {
        'Tomas Satoransky': 34,
        'Zach LaVine': 34,
        'Ryan Arcidiacono': 28,
        'Thaddeus Young': 34,
        'Wendell Carter Jr.': 22
    },
    'CLE': {
        'Tristan Thompson': 32,
        'Kevin Love': 34,
        'Matthew Dellavedova': 32,
        'Collin Sexton': 38,
        'Cedi Osman': 34,
    },
    'DAL': {
        'Maxi Kleber': 30,
        'Jalen Brunson': 32,
        'Seth Curry': 32,
        'Tim Hardaway Jr.': 28,
        'Dorian Finney-Smith':  32
    },
    'DEN': {
        'Nikola Jokic': 36,
        'Jerami Grant': 34,
        'Will Barton': 32,
        'Jamal Murray': 36,
        'Gary Harris': 36
    },
    'DET': {
        'Brandon Knight': 34,
        'Svi Mykhailiuk': 31,
        'Christian Wood': 36,
        'Tony Snell': 33,
        'John Henson': 23
    },
    'GSW': {
        'Juan Toscano-Anderson': 27,
        'Eric Paschall': 32,
        'Marquese Chriss': 28,
        'Damion Lee': 34,
        'Andrew Wiggins': 36
    },
    'HOU': {
        'James Harden': 38,
        'Russell Westbrook': 38,
        'P.J. Tucker': 36,
        'Eric Gordon': 34,
        'Robert Covington': 38
    },
    'IND': {
        'Malcolm Brogdon': 34,
        'T.J. Warren': 34,
        'Victor Oladipo': 28,
        'Myles Turner': 26,
        'Domantas Sabonis': 34
    },
    'LAC': {
        'Kawhi Leonard': 37,
        'Patrick Beverley': 30,
        'Marcus Morris Sr.': 32,
        'Paul George': 32,
        'Ivica Zubac': 22
    },
    'LAL': {
        'LeBron James': 36,
        'Anthony Davis': 36,
        'Danny Green': 28,
        'JaVale McGee': 20,
        'Avery Bradley': 30
    },
    'MEM': {
        'Jonas Valanciunas': 28,
        'Ja Morant': 34,
        'Dillon Brooks': 34,
        'Jaren Jackson Jr.': 34,
        'Kyle Anderson': 28
    },
    'MIA': {
        'Goran Dragic': 30,
        'Kendrick Nunn': 34,
        'Bam Adebayo': 35,
        'Duncan Robinson': 31,
        'Jae Crowder': 32
    },
    'MIL': {
        'Giannis Antetokounmpo': 35,
        'Khris Middleton': 35,
        'Eric Bledsoe': 31,
        'Brook Lopez': 28,
        'Wesley Matthews': 30
    },
    'MIN': {
        'Jordan McLaughlin': 32,
        'Malik Beasley': 36,
        'Juancho Hernangomez': 30,
        'Naz Reid': 32,
        'Josh Okogie': 30
    },
    'NOP': {
        'Lonzo Ball': 38,
        'Jrue Holiday': 36,
        'Brandon Ingram': 34,
        'Zion Williamson': 31,
        'Derrick Favors': 28
    },
    'NYK': {
        'Elfrid Payton': 32,
        'Reggie Bullock': 28,
        'Julius Randle': 34,
        'RJ Barrett': 34,
        'Taj Gibson': 20
    },
    'OKC': {
        'Shai Gilgeous-Alexander': 36,
        'Danilo Gallinari': 32,
        'Steven Adams': 31,
        'Luguentz Dort': 22,
        'Chris Paul': 34
    },
    'ORL': {
        'Nikola Vucevic': 34,
        'Markelle Fultz': 34,
        'Aaron Gordon': 34,
        'Evan Fournier': 34,
        'Khem Birch': 20
    },
    'PHI': {
        'Shake Milton': 36,
        'Furkan Korkmaz': 25,
        'Glenn Robinson III': 20,
        'Tobias Harris': 36,
        'Al Horford': 33
    },
    'PHX': {
        'Devin Booker': 38,
        'Dario Saric': 30,
        'Ricky Rubio': 34,
        'Aron Baynes': 30,
        'Mikal Bridges': 38
    },
    'POR': {
        'Damian Lillard': 34, 
        'CJ McCollum': 38,
        'Hassan Whiteside': 36, 
        'Trevor Ariza': 38,
        'Carmelo Anthony': 34
    },
    'SAC': {
        "De'Aaron Fox": 30,
        'Nemanja Bjelica': 33,
        'Bogdan Bogdanovic': 30,
        'Harrison Barnes': 35,
        'Harry Giles III': 28
    },
    'SAS': {
        'DeMar DeRozan': 36,
        'Dejounte Murray': 29,
        'Trey Lyles': 30,
        'Jakob Poeltl': 25,
        'Bryn Forbes': 26,
    },
    'TOR': {
        'Kyle Lowry': 36,
        'Norman Powell': 36,
        'Pascal Siakam': 36,
        'Rondae Hollis-Jefferson': 32,
        'OG Anunoby': 32
    },
    'UTA': {
        'Donovan Mitchell': 36,
        'Rudy Gobert': 34,
        'Joe Ingles': 31,
        "Mike Conley": 33,
        'Bojan Bogdanovic': 36
    },
    'WAS': {
        'Bradley Beal': 37,
        'Isaac Bonga': 27,
        'Shabazz Napier': 28,
        'Rui Hachimura': 34,
        'Thomas Bryant': 20
    },


}

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

    'UTA': 'DET',
    'DEN': 'CLE',
    'ATL': 'MEM',
    'PHI': 'GSW',
    'SAC': 'POR',
   
}

SLATE_RATING_OBJ = {}

PBP_URL_PREFIX = 'https://api.pbpstats.com'
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/47.0.2526.73 Chrome/47.0.2526.73 Safari/537.36"


def list_to_string(my_list): 
    return ', '.join(my_list)

def two_decimals(num):
    return float('{0:.2f}'.format(num))


def diff_bw_out_lists():
    diff_obj = {}
    for s, p in zip(OUT_LIST, OLD_OUT_LIST):

        diff_obj[s] = {}
        diff_obj[s]['added'] = np.setdiff1d(OUT_LIST[s], OLD_OUT_LIST[p])
        diff_obj[s]['removed'] = np.setdiff1d(OLD_OUT_LIST[p], OUT_LIST[s])

    return diff_obj

def get_all_out_players():
    out_players = []
    for team in OUT_LIST:
        out_players += OUT_LIST[team]

    return out_players

def print_dk_obj():
    out_players = get_all_out_players()

    with open('../scrape/csv/2020-03-07.csv',) as csv_file:
        try:
            next(csv_file, None)
            players = csv.reader(csv_file)
            csv_obj = {}

            # position_obj = {
            #     'C': {},
            #     'PF': {},
            #     'SF': {},
            #     'SG': {},
            #     'PG': {}
            # }
            for player in players:
                positions = player[0].split('/'),
                name = player[2]
                salary =  player[5]
                # print salary, positions, name
                csv_obj[name] = {
                    'positions' : positions,
                    'salary': player[5],
                    'team': player[7],
                    'fp_needed' : float(salary)*0.001*6,
                    'avg_val' : two_decimals(float(player[8])/(0.001*float(salary)))
                }

                # for position in positions[0]:

                #     if salary > 3000 and name not in out_players:
                #         if salary in position_obj[position]:
                #             position_obj[position][salary].append(name)
                #         else:
                #             position_obj[position][salary] = [name]

            # what i want to know is that for each of these positions, what are other players around that price points ~200
            # anything but 3000
            # same, +200, -200, +400, -400
            # for position in position_obj:
            #     print position
            #     temp_salary_list = []

            #     for salary in position_obj[position]:
            #         # lets do something dumb for now and simply append these salaries in a list
            #         temp_salary_list.append(int(salary))

            #     sorted_list = sorted(temp_salary_list)
            #     for num in sorted_list:
            #         salary = str(num)
            #         print salary
            #         print list_to_string(position_obj[position][salary])
            #         if str(int(salary)-100) in position_obj[position]:
            #             print list_to_string(position_obj[position][str(int(salary)-100)])
            #         if str(int(salary)+100) in position_obj[position]:
            #             print list_to_string(position_obj[position][str(int(salary)+100)])
            #         if str(int(salary)-200) in position_obj[position]:
            #             print list_to_string(position_obj[position][str(int(salary)-200)])
            #         if str(int(salary)+200) in position_obj[position]:
            #             print list_to_string(position_obj[position][str(int(salary)+200)])
            #         print

            sdo = sorted(csv_obj.iteritems(), key=lambda x: (x[1]['avg_val']), reverse=True)
            for player_obj in sdo:
                player_name = player_obj[0]
                values = player_obj[1]

                if player_name not in out_players and values['avg_val'] >= 5.3:
                    print '{player_name} ({avg_val})'.format(player_name=player_name, avg_val=values['avg_val'])

        except csv.Error as e:
            sys.exit('file %s: %s' % (csv_file, e))

def get_team_rosters(url):

    team_roster = {}
    response = requests.get(url, headers={'User-Agent': USER_AGENT})
    data = response.json()

    for player_id in data['players']:
        player_name = data['players'][player_id]
        # construct a new dictionary with name first
        team_roster[player_name] = player_id

    return team_roster


def get_nba_team_stats(stats_type):
    url = PBP_URL_PREFIX + '/get-pace-efficiency-summary/nba?Season=%s&SeasonType=%s&Type=%s' % (SEASON, SEASON_TYPE, stats_type)
    pace_eff_obj = {}

    response = requests.get(url, headers={'User-Agent': USER_AGENT})
    data = response.json()


    for team in data['results']:
        pace_eff_obj[team['team_name']] = {
            'ppp': two_decimals(team['ppp']),
            'ppp_rank': team['ppp_rank'],
            'pace': two_decimals(team['spp']),
            'pace_rank': team['spp_rank']
        }

    return pace_eff_obj


def process_wowy(url):

    wowy_obj = {}
    response = requests.get(url, headers={'User-Agent': USER_AGENT})
    data = response.json()

    # OffPoss
    # Usage
    if 'multi_row_table_data' in data:
        for stats in data['multi_row_table_data']:
            wowy_obj[stats['Name']] = {
                'possessions_played': stats['OffPoss'] if 'OffPoss' in stats else 0,
                'usage': two_decimals(stats['Usage']) if 'Usage' in stats else 0,
                'minutes': stats['Minutes'] if 'Minutes' in stats else 0,
                'assists': stats['Assists'] if 'Assists' in stats else 0,
                'rebounds': stats['Rebounds'] if 'Rebounds' in stats else 0,
                'points': stats['Points'] if 'Points' in stats else 0,
                'turnovers': stats['Turnovers'] if 'Turnovers' in stats else 0,
                'steals': stats['Steals'] if 'Steals' in stats else 0,
                'blocks': stats['Blocks'] if 'Blocks' in stats else 0,
                'games_played': stats['GamesPlayed'] if 'GamesPlayed' in stats else 0
            }

    return wowy_obj


def process_wowy_combo(url):

    wowy_obj = {}
    response = requests.get(url, headers={'User-Agent': USER_AGENT})
    data = response.json()

    # OffPoss
    # Usage
    if 'results' in data:
        for stats in data['results']:
            if stats['On'] == '':
                wowy_obj = {
                    'def_rating': stats['DefRtg'] if 'DefRtg' in stats else 0,
                    'off_rating': two_decimals(stats['OffRtg']) if 'OffRtg' in stats else 0
                }

    return wowy_obj

def get_wowy(out_list, team_obj, stats_type, old_new_flag):

    if (len(out_list) > 1):
        temp_str = ''
        for idx, player in enumerate(out_list):
            temp_str = temp_str+str(idx)+'Exactly1OffFloor='+str(team_obj['roster'][player])+'&'
            
        link_str = PBP_URL_PREFIX + '/get-wowy-stats/nba?'+str(temp_str)+'TeamId='+str(team_obj['id'])+'&Season=%s&SeasonType=%s&Type=%s' % (SEASON, SEASON_TYPE, stats_type)
    elif (len(out_list) == 1):
        # link_str = 'https://api.pbpstats.com/get-wowy-stats/nba?0Exactly1OffFloor='+str(temp_list[0])+'&TeamId='+str(temp_team_id)+'&Season=2018-19&SeasonType=Regular%2BSeason&Type=Player'
        link_str = PBP_URL_PREFIX + '/get-wowy-stats/nba?0Exactly1OffFloor='+str(team_obj['roster'][out_list[0]])+'&TeamId='+str(team_obj['id'])+'&Season=%s&SeasonType=%s&Type=%s' % (SEASON, SEASON_TYPE, stats_type)
    else:
        # just get for players that are on
        temp_str = ''

        for idx, player in enumerate(out_list):
            temp_str = temp_str+str(idx)+'Exactly1OnFloor='+str(team_obj['roster'][player])+'&'
            
        link_str = PBP_URL_PREFIX + '/get-wowy-stats/nba?'+str(temp_str)+'TeamId='+str(team_obj['id'])+'&Season=%s&SeasonType=%s&Type=%s' % (SEASON, SEASON_TYPE, stats_type)

    if (len(out_list) >= 1):
        out_id = []
        for out_player in out_list:
            out_id.append(str(team_obj['roster'][out_player]))

        out_id_str = ",".join(str(x) for x in out_id)
        if old_new_flag == 'new' and stats_type == 'Team':
            combo_url = PBP_URL_PREFIX + '/get-wowy-combination-stats/nba?TeamId='+str(team_obj['id'])+'&Season=%s&SeasonType=%s&PlayerIds=%s' % (SEASON, SEASON_TYPE, out_id_str)
            combo_obj = process_wowy_combo(combo_url)

            SLATE_RATING_OBJ[team_obj['name']] = combo_obj

    # print link_str
    
    wowy_obj = {}
    if link_str != '':
        wowy_obj = process_wowy(link_str)
        # only print new set of lines
        if stats_type == 'Team' and old_new_flag == 'new':
            lbp = sorted(wowy_obj.iteritems(), key=lambda x: x[1]['possessions_played'], reverse=True)
            # get the number of games player
            for player_obj in lbp[0:12:1]:
                player_name = player_obj[0]
                values = player_obj[1]

                print player_name
                print '{usage} - {possessions_played}'.format(usage=values['usage'], possessions_played=values['possessions_played'])

            print '\n'

    return wowy_obj

def print_lineup_wowy_obj(wowy_obj, team): 

    # we can improve this by checking for the minutes as well since if they play less than 15min together it might be a new line
    lbp = sorted(wowy_obj.iteritems(), key=lambda x: x[1]['usage'], reverse=True)
    print 'Minutes Played This Season: %s' % lbp[0][1]['minutes']
    for player_obj in lbp:
        player_name = player_obj[0]
        values = player_obj[1]
        ppm = two_decimals((float(values['points']) / float(values['minutes']) * ON_FLOOR[team][player_name]))
        apm = two_decimals((float(values['assists']) / float(values['minutes']) * ON_FLOOR[team][player_name]))
        rpm = two_decimals((float(values['rebounds']) / float(values['minutes']) * ON_FLOOR[team][player_name]))
        tpm = two_decimals((float(values['turnovers']) / float(values['minutes']) * ON_FLOOR[team][player_name]))
        spm = two_decimals((float(values['steals']) / float(values['minutes']) * ON_FLOOR[team][player_name]))
        bpm = two_decimals((float(values['blocks']) / float(values['minutes']) * ON_FLOOR[team][player_name]))

        print player_name,ON_FLOOR[team][player_name]
        print '{usage}, {ppm} + {rpm} + {apm} + {spm} + {bpm} - {tpm} '.format(usage=values['usage'], ppm=ppm, rpm=rpm, apm=apm , spm=spm , bpm=bpm , tpm=tpm)

def roster_changes(team):
    diff_outs = diff_bw_out_lists()

    team_id = TEAM_ID_OBJ[team]
    team_url = PBP_URL_PREFIX  + '/get-team-players-for-season?TeamId=%s&Season=%s&SeasonType=%s' % (team_id, SEASON, SEASON_TYPE)

    team_roster = get_team_rosters(team_url)

    team_obj = {
        'id': team_id,
        'name': team,
        'url': team_url,
        'roster': team_roster
    }
    # for team in TEAM_ID_OBJ:
    if len(diff_outs[team]['added']) >= 1 or len(diff_outs[team]['removed']) >= 1:
        print team + " CHANGED"
        if len(diff_outs[team]['added']) >= 1:
            print 'Added:'
            print diff_outs[team]['added']

        if len(diff_outs[team]['removed']) >= 1:
            print 'Removed:'
            print diff_outs[team]['removed']


        # lets call the pbp on_off since there were changes for both on and off
        # API call for both OLD_OUT_LIST and OUT_LIST
        old_wowy = get_wowy(OLD_OUT_LIST[team], team_obj, 'Player', 'old')
        new_wowy = get_wowy(OUT_LIST[team], team_obj, 'Player', 'new')

        old_wowy_team = get_wowy(OLD_OUT_LIST[team], team_obj, 'Team', 'old')
        new_wowy_team = get_wowy(OUT_LIST[team], team_obj, 'Team', 'new')

        # do a simple subtraction between new and old
        diff_obj = {}
        for player in new_wowy:

            # players that could have been impacted due to changes
            # active players for both days
            if player in old_wowy and player in new_wowy:
                # store in obj
                diff_obj[player] = {
                    # 'diff_possessions_played': two_decimals(abs(new_wowy[player]['possessions_played'] - old_wowy[player]['possessions_played'])),
                    'diff_usage': new_wowy[player]['usage'] - old_wowy[player]['usage'],
                    'minutes': new_wowy[player]['minutes'],
                }

            else:
                # players that were not in the old_out_list
                # players who were either added or removed today
                print 'ADDED/REMOVED %s  -   %s,  %smin' % (player, new_wowy[player]['usage'], new_wowy[player]['minutes'])

        sdo = sorted(diff_obj.iteritems(), key=lambda x: (x[1]['minutes'], x[1]['diff_usage']), reverse=True)

        for player_obj in sdo:
            player_name = player_obj[0]
            values = player_obj[1]

            print '{player_name} ({diff_usage})  -  {usage},  {minutes_played}min'.format(player_name=player_name, \
                usage=new_wowy[player_name]['usage'], diff_usage=values['diff_usage'], minutes_played=values['minutes'])

        print '\n'

    on_floor_list = []

    for player_name, minutes in ON_FLOOR[team].iteritems():
        on_floor_list.append(str(team_roster[player_name]))

    on_floor_str = ','.join(on_floor_list)

    # for the last week or so how is the performance (?)
    # &FromDate=2020-01-23&ToDate=2020-02-01
    recent_link_str = PBP_URL_PREFIX + '/get-wowy-stats/nba?0Exactly5OnFloor='+on_floor_str+'&TeamId='+str(team_id)+'&Season=%s&SeasonType=%s&Type=%s&FromDate=%s&ToDate=%s' % (SEASON, SEASON_TYPE, 'Player', week_ago, today_date)
    recent_wowy_obj = process_wowy(recent_link_str)

    if (len(recent_wowy_obj) > 1):
        # we can improve this by checking for the minutes as well since if they play less than 15min together it might be a new line
        lbp = sorted(recent_wowy_obj.iteritems(), key=lambda x: x[1]['usage'], reverse=True)

        if lbp[0][1]['minutes'] >= 25:
            print 'Minutes Played This Week: %s' % lbp[0][1]['minutes']
            for player_obj in lbp:
                player_name = player_obj[0]
                values = player_obj[1]
                ppm = two_decimals((float(values['points']) / float(values['minutes']) * ON_FLOOR[team][player_name]))
                apm = two_decimals((float(values['assists']) / float(values['minutes']) * ON_FLOOR[team][player_name]))
                rpm = two_decimals((float(values['rebounds']) / float(values['minutes']) * ON_FLOOR[team][player_name]))
                tpm = two_decimals((float(values['turnovers']) / float(values['minutes']) * ON_FLOOR[team][player_name]))
                spm = two_decimals((float(values['steals']) / float(values['minutes']) * ON_FLOOR[team][player_name]))
                bpm = two_decimals((float(values['blocks']) / float(values['minutes']) * ON_FLOOR[team][player_name]))

                print player_name, ON_FLOOR[team][player_name]
                print '{usage}, {ppm} + {rpm} + {apm} + {spm} + {bpm} - {tpm} '.format(usage=values['usage'], ppm=ppm, rpm=rpm, apm=apm , spm=spm , bpm=bpm , tpm=tpm)
            
            print '\n'

        else:
            # get combinations with main guys
            print 'NEW LINE, Checking overall...'
            link_str = PBP_URL_PREFIX + '/get-wowy-stats/nba?0Exactly5OnFloor='+on_floor_str+'&TeamId='+str(team_id)+'&Season=%s&SeasonType=%s&Type=%s' % (SEASON, SEASON_TYPE, 'Player')
            wowy_obj = process_wowy(link_str)
            
            if (len(wowy_obj) > 1):
                print_lineup_wowy_obj(wowy_obj, team)

            else:
                print 'THIS IS A BRAND NEW LINE'
            print '\n'

    else:
        # get combinations with main guys
        print 'NEW LINE, Checking overall...'
        link_str = PBP_URL_PREFIX + '/get-wowy-stats/nba?0Exactly5OnFloor='+on_floor_str+'&TeamId='+str(team_id)+'&Season=%s&SeasonType=%s&Type=%s' % (SEASON, SEASON_TYPE, 'Player')
        wowy_obj = process_wowy(link_str)
        
        if (len(wowy_obj) > 1):
            print_lineup_wowy_obj(wowy_obj, team)
        else:
            print 'THIS IS A BRAND NEW LINE'
        print '\n'


team_pace_eff_obj = get_nba_team_stats('Team')
opp_pace_eff_obj = get_nba_team_stats('Opponent')

for team in SLATE:
    roster_changes(team)
    roster_changes(SLATE[team])
    print team
    print team_pace_eff_obj[team]
    print 'opponent'
    print opp_pace_eff_obj[team]
    print '\n'
    print SLATE[team]
    print team_pace_eff_obj[SLATE[team]]
    print 'opponent'
    print opp_pace_eff_obj[SLATE[team]]

    print '\n'
print pp.pprint(SLATE_RATING_OBJ)
print ''

print_dk_obj()
