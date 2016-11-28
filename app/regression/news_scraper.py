# !/usr/bin/env python
# _*_ coding:utf-8 _*_
import MySQLdb
import MySQLdb.converters
import time, urllib2
import pprint
import csv
import logging
import sqlfetch
import json
import requests
import numpy as np
import scipy.stats as ss
from bs4 import BeautifulSoup
from datetime import date, timedelta, datetime

import warnings
# explictly not show warnings
warnings.filterwarnings("ignore")
logging.getLogger("requests").setLevel(logging.WARNING)

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

conv = MySQLdb.converters.conversions.copy()
conv[246] = float    # convert decimals to floats
conv[10] = str       # convert dates to strings

# Open database connection
db = MySQLdb.connect("127.0.0.1","root","","nba_scrape", conv=conv)

# prepare a cursor object using cursor() method
cursor = db.cursor()

pp = pprint.PrettyPrinter(indent=4)


YEAR = '2017'

LAST_DATE_REG_SEASON = '2017-04-12'
FIRST_DATE_REG_SEASON = '2016-10-25'

FIRST_DATE_PRE_SEASON = '2016-10-01'
LAST_DATE_PRE_SEASON = '2016-10-15'

# some links dont transfer
SCRAPE_TRANSLATE_DICT = {
    'CHA':'CHO',
    'GS':'GSW',
    'LAK':'LAL',
    'MLW':'MIL',
    'NO':'NOP',
    'NY':'NYK',
    'BKN':'BRK',
    'SA':'SAS',
}

NEWS_DICT = {
    'ATL':'Atlanta Hawks',
    'BOS':'Boston Celtics',
    'BKN':'Brooklyn Nets',
    'CHA':'Charlotte Hornets',
    'CHI':'Chicago Bulls',
    'CLE':'Cleveland Cavaliers',
    'DAL':'Dallas Mavericks',
    'DEN':'Denver Nuggets',
    'DET':'Detroit Pistons',
    'GS':'Golden State Warriors',
    'HOU':'Houston Rockets',
    'IND':'Indiana Pacers',
    'LAC':'Los Angeles Clippers',
    'LAK':'Los Angeles Lakers',
    'MEM':'Memphis Grizzlies',
    'MIA':'Miami Heat',
    'MLW':'Milwaukee Bucks',
    'MIN':'Minnesota Timberwolves',
    'NO':'New Orleans Pelicans',
    'NY':'New York Knicks',
    'OKC':'Oklahoma City Thunder',
    'ORL':'Orlando Magic',
    'PHI':'Philadelphia 76ers',
    'PHO':'Phoenix Suns',
    'POR':'Portland Trail Blazers',
    'SAC':'Sacramento Kings',
    'SA':'San Antonio Spurs',
    'TOR':'Toronto Raptors',
    'UTA':'Utah Jazz',
    'WAS':'Washington Wizards'
}

TEAMS_DICT = {
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

REVERSE_TEAMS_DICT = {
    'Atlanta Hawks': 'ATL',
    'Boston Celtics': 'BOS',
    'Brooklyn Nets': 'BRK',
    'Charlotte Hornets': 'CHO',
    'Chicago Bulls': 'CHI',
    'Cleveland Cavaliers': 'CLE',
    'Dallas Mavericks': 'DAL',
    'Denver Nuggets': 'DEN',
    'Detroit Pistons': 'DET',
    'Golden State Warriors': 'GSW',
    'Houston Rockets': 'HOU',
    'Indiana Pacers': 'IND',
    'Los Angeles Clippers': 'LAC',
    'Los Angeles Lakers': 'LAL',
    'Memphis Grizzlies': 'MEM',
    'Miami Heat': 'MIA',
    'Milwaukee Bucks': 'MIL',
    'Minnesota Timberwolves': 'MIN',
    'New Orleans Pelicans': 'NOP',
    'New York Knicks': 'NYK',
    'Oklahoma City Thunder': 'OKC',
    'Orlando Magic': 'ORL',
    'Philadelphia 76ers': 'PHI',
    'Phoenix Suns': 'PHO',
    'Portland Trail Blazers': 'POR',
    'Sacramento Kings': 'SAC',
    'San Antonio Spurs': 'SAS',
    'Toronto Raptors': 'TOR',
    'Utah Jazz': 'UTA',
    'Washington Wizards': 'WAS'
}

NEWS_URL = 'http://www.rotoworld.com/teams/nba/'
MATCHUP_URL = 'http://www.rotowire.com/daily/nba/defense-vspos.htm'

def two_decimals(num):
    return float('{0:.2f}'.format(num))


def get_fantasy_news():

    for team, name in NEWS_DICT.iteritems():
        # add the - to the team names
        split_string = name.split()
        new_string = ''
        for string in split_string:
            new_string += string +'-'
        team_link = new_string[:-1]

        LOGGER.debug('Scraping news for: '+ team)
        news_content = []
        url = urllib2.urlopen(NEWS_URL+'/'+team+'/'+team_link)

        soup = BeautifulSoup(url, 'html5lib')
        news_holder = soup.find_all('div', attrs={'class':'RW_pn'})[1]
        news = news_holder.find_all('div', attrs={'class':'pb'})

        for info in news:
            headline = info.find('div', attrs={'class':'headline'})
            name = headline.find('a').text
            news_report = info.find('div', \
                attrs={'class':'report'}).find('p').text
            news_impact = info.find('div', \
                attrs={'class':'impact'}).text

            news_content.append({
                'player': name,
                'report': news_report,
                'impact': news_impact,
            })

        if team in SCRAPE_TRANSLATE_DICT:
            team = SCRAPE_TRANSLATE_DICT[team]

        with open('../scrape/misc/news/'+team+'.json', 'w') as outfile:
            LOGGER.info('Writing news to json file: '+ team)
            json.dump(news_content, outfile)


def get_vegas_lines(date):
    url = urllib2.urlopen('http://www.covers.com/Sports/NBA/Matchups?selectedDate='+date)
    soup = BeautifulSoup(url, 'html5lib')

    game_list = soup.find_all('div', attrs={'class': 'cmg_matchups_list'})[0]
    game_matchup = game_list.find_all('div', attrs={'class': 'cmg_matchup_game'})

    vegas_lines = {}
    for game in game_matchup:
        open_odds = game.find('div', attrs={'class': 'cmg_team_opening_odds'})
        odds_line = open_odds.find_all('span')
        over_under = odds_line[1].text
        advantage_team = odds_line[2].text
        matchup = game.find_all('div', attrs={'class': 'cmg_team_name'})

        for team in matchup:
            teams = team.find_all(text=True, recursive=False)
            for team in teams:
                team_name = team.strip()
                if team_name != '':
                    if team_name in SCRAPE_TRANSLATE_DICT:
                        team_name = SCRAPE_TRANSLATE_DICT[team_name]
                    vegas_lines[team_name] = {
                        'over_under': over_under,
                        'advantage_team': advantage_team
                    }
    return vegas_lines

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

def get_team_against_position():
    pos_list = ['PG', 'SG', 'G', 'SF', 'PF', 'F', 'C']
    site = 'DraftKings'
    matchup_data = {}
    matchup_data['league'] = {}
    matchup_data['league']['position'] = {}
    total_stats = {}
    for position in pos_list:
        LOGGER.info('getting matchup information for: '+position)
        url = urllib2.urlopen(MATCHUP_URL+'?site=%s&pos=%s' % (site, position))
        soup = BeautifulSoup(url, 'html5lib')

        table = soup.find('table', attrs={'class': 'footballproj-table'})
        header = table.find('thead')
        team_header = header.find_all('tr')[1].find_all('th')

        table_body = table.find('tbody')
        teams = table_body.find_all('tr')

        team_rank = 0
        matchup_data['league']['position'][position] = {}

        total_stats[position] = {}
        league_total = 0
        # only stats i care about
        valid_list = ['3PM', 'AST', 'BLK', 'FG%', 'PTS', 'REB', 'STL']
        for stat in valid_list:
            total_stats[position][stat] = 0

        for team in teams:
            team_stats = team.find_all('td')
            tempname = str(team_stats[0].text)

            team_name = REVERSE_TEAMS_DICT[tempname]

            if team_name not in matchup_data:
                matchup_data[team_name] = {}
                # the rank is in ascending order
            if position not in matchup_data[team_name]:
                matchup_data[team_name][position] = {}
                team_rank += 1
                matchup_data[team_name][position]['rank'] = team_rank

            # zip with the header so it runs in "parallel"
            for header, stat in zip(team_header, team_stats):
                category = str(header.text)
                matchup_data[team_name][position][category] = str(stat.text)

                # sum up totals for league average
                if category == 'Season':
                    league_total += float(stat.text)
                if category in valid_list:
                    total_stats[position][category] += float(stat.text)

            matchup_data['league']['position'][position]['average'] = float(league_total / 30)

        # parse each category
        for cat, total in total_stats[position].iteritems():
            total_stats[position][cat] = float(total / 30)

    matchup_data['league']['category'] = total_stats
    # loop each team
    for team in TEAMS_DICT:
        with open('../scrape/misc/fantasy_stats/'+team+'.json', 'w') as outfile:
            LOGGER.info('Writing to fantasy_stats file:' +team)
            json.dump(matchup_data[team], outfile)

    # dump league avg separately
    with open('../scrape/misc/fantasy_stats/league.json', 'w') as outfile:
        json.dump(matchup_data['league'], outfile)

    return matchup_data

def player_daily_status():
    url = urllib2.urlopen('https://basketballmonster.com/playernews.aspx')
    soup = BeautifulSoup(url, 'html5lib')

    today_news = soup.find_all('div', attrs={'class': 'daily-status-updates'})
    player_status = today_news[0].find_all('div', attrs={'class': 'daily-status-player'})
    projected_returns = today_news[1].find_all('div', attrs={'class': 'daily-status-player'})

    daily_status_player = {
        'today': {},
        'all': {},
    }
    for player in player_status:
        player_status = player.find_all('a')
        try:
            status = player_status[0].text.split('-')[0].strip()
            player_name = player_status[1].text
            daily_status_player['today'][player_name] = status
        except IndexError:
            LOGGER.debug('No news')

    for player in projected_returns:
        player_status = player.find_all('a')
        try:
            player_name = player_status[0].text
            daily_status_player['all'][player_name] = 'Out'
        except IndexError:
            LOGGER.debug('No news')

    return daily_status_player

def construct_api_url(team, vs_teams, on_players, off_players, start_date, end_date):
    base_url = 'http://nbawowy-52108.onmodulus.net/api/'

    if vs_teams == 'all':
        vs_teams = '[76ers,Bobcats,Bucks,Bulls,Cavaliers,Celtics,Clippers,'\
                    'Grizzlies,Hawks,Heat,Hornets,Jazz,Kings,Knicks,Lakers,'\
                    'Magic,Mavericks,Nets,Nuggets,Pacers,Pelicans,Pistons,'\
                    'Raptors,Rockets,Spurs,Suns,Thunder,Timberwolves,'\
                    'Trail Blazers,Warriors,Wizards]'
    else:
        vs_teams = '[%s]' % ','.join(map(str, vs_teams))

    link_list = [
        {
            'name': 'poss',
            'link': 'm/poss/q/'
        },
        {
            'name': 'tov',
            'link': 'tov/q/'
        },
        {
            'name': 'fga',
            'link': 'fga/q/'
        },
        {
            'name': 'lineups',
            'link': 'lineups/q/'
        },
        {
            'name': 'reb',
            'link': 'reb/q/'
        },
        {
            # free throw trips
            'name': 'fta',
            'link': 'fta/q/'
        },
        {
            'name': 'ast',
            'link': 'ast/q/'
        }
    ]


    home_away = '/both/'

    seasons = '[pre,regular,playoffs]'
    quarters = '[1,2,3,4,0,5,6,7]'
    # http://stackoverflow.com/questions/5445970/printing-list-in-python-properly
    on_players = '[%s]' % ','.join(map(str, on_players))
    off_players = '[%s]' % ','.join(map(str, off_players))

    url_list = []
    for stat in link_list:
        url = '{base_url}{seasons}{home_away}{stat_link}{quarters}'\
            '/team/{team}/vs/{vs_teams}/on/{on_players}/off/{off_players}'\
            '/from/{start_date}/to/{end_date}'.format(
                base_url=base_url,
                seasons=seasons,
                home_away=home_away,
                stat_link=stat['link'],
                quarters=quarters,
                team=team,
                vs_teams=vs_teams,
                on_players=on_players,
                off_players=off_players,
                start_date=start_date,
                end_date=end_date
            )
        url_list.append({
            'stat': stat['name'],
            'url': url
        })

    return url_list

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/47.0.2526.73 Chrome/47.0.2526.73 Safari/537.36"
def player_on_off(team, vs_teams, on_players, off_players, start_date, end_date):

    url_list = construct_api_url(team, vs_teams, on_players, off_players, start_date, end_date)

    player_obj = {
        'players': {},
        'lineups': [],
    }

    for stat in url_list:
        url = stat['url']
        response = requests.get(url, headers={'User-Agent': USER_AGENT})
        data = response.json()
        if stat['stat'] == 'poss':
            for player in data:
                player_name = player['_id']['name']

                player_obj['players'][player_name] = {
                    'poss': player['poss'],
                    'min': player['time'] / 60
                }

        if stat['stat'] == 'lineups':
            for lineup in data:
                player_obj['lineups'].append({
                    'lineup': lineup['_id']['name'],
                    'poss': lineup['poss'],
                    'min': lineup['time'] / 60
                })

        if stat['stat'] == 'tov' \
            or stat['stat'] == 'reb' \
            or stat['stat'] == 'ast':
            process_stat_api(player_obj, data, stat['stat'])

        if stat['stat'] == 'fga':
            temp_obj = {}
            for player in data:
                player_info = player['_id']
                player_name = player_info['name']
                if player_name not in temp_obj:
                    temp_obj[player_name] = {
                        'fg2m': 0,
                        'fg2x': 0,
                        'fg3m': 0,
                        'fg3x': 0
                    }

                if player_info['made'] == True and player_info['value'] == 2:
                    temp_obj[player_name]['fg2m'] += player['count']
                elif player_info['made'] == True and player_info['value'] == 3:
                    temp_obj[player_name]['fg3m'] += player['count']
                elif player_info['made'] == False and player_info['value'] == 2:
                    temp_obj[player_name]['fg2x'] += player['count']
                elif player_info['made'] == False and player_info['value'] == 3:
                    temp_obj[player_name]['fg3x'] += player['count']


            for (player, stat_name) in player_obj['players'].iteritems():
                if player in temp_obj:
                    player_obj['players'][player][stat['stat']] = temp_obj[player]
                else:
                    player_obj['players'][player][stat['stat']] = {
                        'fg2m': 0,
                        'fg2x': 0,
                        'fg3m': 0,
                        'fg3x': 0
                    }

        if stat['stat'] == 'fta':
            temp_obj = {}
            for player in data:
                player_info = player['_id']
                player_name = player_info['name']

                if player_name not in temp_obj:
                    temp_obj[player_name] = {
                        'fta2m': 0,
                        'fta2x': 0,
                        'fta3m': 0,
                        'fta3x': 0
                    }

                if player_info['made'] == True and player_info['out_of'] == 2:
                    temp_obj[player_name]['fta2m'] += player['count']
                elif player_info['made'] == True and player_info['out_of'] == 3:
                    temp_obj[player_name]['fta3m'] += player['count']
                elif player_info['made'] == False and player_info['out_of'] == 2:
                    temp_obj[player_name]['fta2x'] += player['count']
                elif player_info['made'] == False and player_info['out_of'] == 3:
                    temp_obj[player_name]['fta3x'] += player['count']


            for (player, stat_name) in player_obj['players'].iteritems():
                if player in temp_obj:
                    player_obj['players'][player][stat['stat']] = temp_obj[player]
                else:
                    player_obj['players'][player][stat['stat']] = {
                        'fta2m': 0,
                        'fta2x': 0,
                        'fta3m': 0,
                        'fta3x': 0
                    }


    for (player, stats) in player_obj['players'].iteritems():
        # definitions from nbawowy
        fta_made = stats['fta']['fta2m'] + stats['fta']['fta3m']
        fta_missed = stats['fta']['fta2x'] + stats['fta']['fta3x']
        fga_made = stats['fga']['fg2m'] + stats['fga']['fg3m']
        fga_missed = stats['fga']['fg2x'] + stats['fga']['fg3x']

        fga = fga_made + fga_missed
        fta = fta_made + fta_missed

        fta_2 = stats['fta']['fta2m'] + stats['fta']['fta2x']
        fta_3 = stats['fta']['fta3m'] + stats['fta']['fta3x']

        try:
            usg = ((fga + (0.44 * fta) + stats['tov']) / stats['poss'] * 100)
        except ZeroDivisionError:
            usg = 0
        try:
            pace = 48 * stats['poss'] / stats['min']
        except ZeroDivisionError:
            pace = 0

        plays = fga + (0.5 * fta) + stats['tov'] + stats['ast']
        tsa = fga + 0.5 * (fta_2) + (1/3) * (fta_3)

        try:
            ppp = (2* stats['fga']['fg2m'] + 3 * stats['fga']['fg3m'] + fta_made) \
                / (stats['fga']['fg2m'] + 0.7 * fga_missed \
                + stats['fga']['fg3m'] + stats['tov'] + 0.44 * fta)
        except ZeroDivisionError:
            ppp = 0

        try:
            scoring_index = (1 + ((-0.9 + 0.89 * ((fga_made + 0.73 * (fga_missed) \
                + 0.5 * fta_2 + (1/3) * fta_3 + stats['tov']) \
                / stats['poss']) + 0.5 * (2 * stats['fga']['fg2m'] \
                + 3 * stats['fga']['fg3m'] + fta_made)\
                / (fga + 0.5 * fta_2 + (1/3)* fta_3)) / 1.33) / 0.136)
        except ZeroDivisionError:
            scoring_index = 0

        # (2*stats.fg2m+3*stats.fg3m+stats.fta2m + stats.fta3m+stats.and1m + stats.techm+0.5*stats.fg3m+1.25*(stats.oreb+stats.dreb) + 1.5*(stats.ast2+stats.ast3) + 2 * stats.stl + 2 * stats.blk - 0.5 * stats.tov)/stats.min
        stats['complied_stats'] = {
            'usg': two_decimals(usg),
            'plays': two_decimals(plays),
            'pace': two_decimals(pace),
            'tsa': two_decimals(tsa),
            'ppp': two_decimals(ppp),
            'scoring_index': two_decimals(scoring_index)
        }

    return player_obj

def process_stat_api(player_obj, data, stat):
    temp_obj = {}
    count = 'count'
    if stat == 'tov':
        count = 'tov'

    for player in data:
        player_name = player['_id']['name']

        if player_name in temp_obj:
            temp_obj[player_name] += player[count]
        else:
            temp_obj[player_name] = player[count]

    for (player, stat_name) in player_obj['players'].iteritems():
        if player in temp_obj:
            player_obj['players'][player][stat] = temp_obj[player]
        else:
            player_obj['players'][player][stat] = 0

    return player_obj

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

REVERSE_POSITION_TRANSLATE_DICT = {
     'PG': 1,
     'SG': 2,
     'SF': 3,
     'PF': 4,
     'C': 5
}


def get_all_wowy_players():
    all_wowy_players = []
    base_url = 'http://nbawowy-52108.onmodulus.net/api/players/'

    vs_teams = ['76ers','Bobcats','Bucks','Bulls','Cavaliers','Celtics','Clippers',
                'Grizzlies','Hawks','Heat','Hornets','Jazz','Kings','Knicks','Lakers',
                'Magic','Mavericks','Nets','Nuggets','Pacers','Pelicans','Pistons',
                'Raptors','Rockets','Spurs','Suns','Thunder','Timberwolves',
                'Trail Blazers','Warriors','Wizards']

    for team in vs_teams:
        url = base_url + team
        response = requests.get(url, headers={'User-Agent': USER_AGENT})
        data = response.json()

        for player in data['players']:
            all_wowy_players.append(player)

    return all_wowy_players

# get_all_wowy_players()
# just the lineup call
def get_lineups_by_team(team, vs_teams, on_players, off_players, start_date, end_date):

    base_url = 'http://nbawowy-52108.onmodulus.net/api/'

    # http://nbawowy-52108.onmodulus.net/api/players/76ers/

    if vs_teams == 'all':
        vs_teams = '[76ers,Bobcats,Bucks,Bulls,Cavaliers,Celtics,Clippers,'\
                    'Grizzlies,Hawks,Heat,Hornets,Jazz,Kings,Knicks,Lakers,'\
                    'Magic,Mavericks,Nets,Nuggets,Pacers,Pelicans,Pistons,'\
                    'Raptors,Rockets,Spurs,Suns,Thunder,Timberwolves,'\
                    'Trail Blazers,Warriors,Wizards]'
    else:
        vs_teams = '[%s]' % ','.join(map(str, vs_teams))

    link_list = [
        {
            'name': 'lineups',
            'link': 'lineups/q/'
        }
    ]

    home_away = '/both/'

    seasons = '[pre,regular,playoffs]'
    quarters = '[1,2,3,4,0,5,6,7]'
    # http://stackoverflow.com/questions/5445970/printing-list-in-python-properly
    on_players = '[%s]' % ','.join(map(str, on_players))
    off_players = '[%s]' % ','.join(map(str, off_players))

    url_list = []
    for stat in link_list:
        url = '{base_url}{seasons}{home_away}{stat_link}{quarters}'\
            '/team/{team}/vs/{vs_teams}/on/{on_players}/off/{off_players}'\
            '/from/{start_date}/to/{end_date}'.format(
                base_url=base_url,
                seasons=seasons,
                home_away=home_away,
                stat_link=stat['link'],
                quarters=quarters,
                team=team,
                vs_teams=vs_teams,
                on_players=on_players,
                off_players=off_players,
                start_date=start_date,
                end_date=end_date
            )
        url_list.append({
            'stat': stat['name'],
            'url': url
        })

    player_obj = {
        'lineups': [],
    }

    for stat in url_list:
        url = stat['url']
        response = requests.get(url, headers={'User-Agent': USER_AGENT})
        data = response.json()

        if stat['stat'] == 'lineups':
            for lineup in data:
                player_obj['lineups'].append({
                    'lineup': lineup['_id']['name'],
                    'poss': lineup['poss'],
                    'min': lineup['time'] / 60
                })

    return player_obj


def get_all_teams_playing_today():
    # for all players playing in tomorrow's game we are going to get how they played in the preseason
    with open('../scrape/json_files/team_schedules/'+YEAR+'/league_schedule.json',) as data_file:
        data = json.load(data_file)
        today_date = date.today()
        formatted_date = today_date.strftime("%a, %b %-d, %Y")

        all_teams = []

        for game in data[formatted_date]:
            all_teams.append(game['team'])
            all_teams.append(game['opp'])

    return all_teams

def process_line_up_sums(lineup, temp_lineup_obj, player_depth_positions):
    lineup_sum = 0
    for idx, player in enumerate(lineup['lineup']):
        try:
            player_lineup_position = POSITION_TRANSLATE_DICT[idx+1]
            split_name = player.split('.')
            split_name_two = player.split("'")
            split_name_three = player.split("-")
            if len(split_name) > 1 or \
                len(split_name_two) > 1 or \
                len(split_name_three) > 1:
                if len(split_name) > 1:
                    player = "".join(split_name)
                if len(split_name_two) > 1:
                    player = "".join(split_name_two)
                if len(split_name_three) > 1:
                    player = " ".join(split_name_three)

                if player in player_depth_positions:
                    player_lineup_position = player_depth_positions[player]
            else:
                if player in player_depth_positions:
                    player_lineup_position = player_depth_positions[player]

            if player in temp_lineup_obj:
                temp_player = temp_lineup_obj[player]
                temp_player['num_lineups'] += 1
                temp_player['poss'] += lineup['poss']
                temp_player['min'] += lineup['min']

                # check for additional positions played
                if player_lineup_position in temp_player['positions']:
                    temp_player['positions'][player_lineup_position] += lineup['poss']
                else:
                    temp_player['positions'][player_lineup_position] = lineup['poss']
            else:

                if player in player_depth_positions:
                    player_index = REVERSE_POSITION_TRANSLATE_DICT[player_lineup_position]
                else:
                    player_index = idx+1

                temp_lineup_obj[player] = {
                    'poss': lineup['poss'],
                    'num_lineups': 1,
                    'min': lineup['min'],
                    'positions': {
                       player_lineup_position: lineup['poss']
                    },
                    'posIdx': player_index
                }

            lineup_sum += temp_lineup_obj[player]['posIdx']

        except KeyError:
            LOGGER.debug('Too many players')

    return lineup_sum

SQL_TRANSLATE_DICT = {
    'CHO':'CHA',
    'BRK':'BKN',
    'PHO':'PHX',
}

def get_sql_team_names():
    team_obj = {}
    query = """
        SELECT TEAM_ID, TEAM_ABBREVIATION FROM all_game_ids GROUP BY TEAM_ID
    """
    all_teams = sqlfetch.execute_query(query)

    for team in all_teams:
        team_obj[team['TEAM_ABBREVIATION']] = {
            'name': team['TEAM_ABBREVIATION'],
            'team_id': team['TEAM_ID']
        }

    return team_obj

def get_all_lineups():
    # all_teams = get_all_teams_playing_today()
    # depth_chart_obj = process_depth_charts()

    # also account for duplicates in the small_ball.json

    team_obj = get_sql_team_names()

    cursor.execute("DROP TABLE IF EXISTS team_lineups")

    sql = """CREATE TABLE team_lineups (
              TEAM_ID varchar(255),
              TEAM_NAME varchar(255),
              PLAYER_1 varchar(255),
              PLAYER_2 varchar(255),
              PLAYER_3 varchar(255),
              PLAYER_4 varchar(255),
              PLAYER_5 varchar(255),
              POSSESSIONS INT,
              MINUTES_PLAYED INT)"""

    cursor.execute(sql)

    all_teams = TEAMS_DICT.keys()
    # all_teams = ['DAL']

    all_small_ball_lineup_obj = {}
    for team in all_teams:
        with open('../scrape/misc/updated_depth_chart/'+team+'.json') as data_file:
            data = json.load(data_file)
            player_depth_positions = data['all']


        if team in SQL_TRANSLATE_DICT:
            sql_team_name = SQL_TRANSLATE_DICT[team]
        else:
            sql_team_name = team

        # lineup analysis
        print 'AGAINST ' + team
        temp_lineup_obj = {}
        # small_ball_sum = []
        lineup_poss = []
        small_ball_poss = []
        sql_lineups = []
        team_wowy_obj = get_lineups_by_team(WOWY_TEAMS[team], 'all', [], [], FIRST_DATE_REG_SEASON, LAST_DATE_REG_SEASON)
        for lineup in team_wowy_obj['lineups']:

            # if lineup['poss'] >= 5:
            lineup_poss.append(lineup['poss'])
            last_two_players = []
            for idx, lineup_player in enumerate(lineup['lineup']):
                try:
                    # print lineup['lineup'][idx]
                    if lineup['lineup'][idx] in WOWY_TO_DK_TRANSLATE:
                        lineup['lineup'][idx] = WOWY_TO_DK_TRANSLATE[lineup['lineup'][idx]]
                        if lineup['lineup'][idx] in DK_TO_SQL_TRANSLATE:
                            lineup['lineup'][idx] = DK_TO_SQL_TRANSLATE[lineup['lineup'][idx]]

                    if lineup['lineup'][idx] in DK_TO_SQL_TRANSLATE:
                        lineup['lineup'][idx] = DK_TO_SQL_TRANSLATE[lineup['lineup'][idx]]

                    lineup['lineup'][idx] = lineup['lineup'][idx].encode("utf-8")
                except IndexError:
                    print "Index doesn't exist!"

            team_id = team_obj[sql_team_name]['team_id']
            # translate team to sql_team
            try:
                val_string = '("{team_id}", "{team_name}", "{player_1}", "{player_2}", "{player_3}", "{player_4}", "{player_5}",'\
                    '"{possessions}", "{minutes_played}")'.format(
                        team_id=team_id, team_name=sql_team_name, \
                        player_1=lineup['lineup'][0], player_2=lineup['lineup'][1], player_3=lineup['lineup'][2], \
                        player_4=lineup['lineup'][3], player_5=lineup['lineup'][4], \
                        possessions=lineup['poss'], minutes_played=lineup['min']
                    )
                sql_lineups.append(val_string)
            except IndexError:
                print "Index doesn't exist!"

            # get last two players
            for player in lineup['lineup'][-2:]:
                split_name = player.split('.')
                if len(split_name) > 1:
                    player = "".join(split_name)
                last_two_players.append(player)

            lineup_sum = process_line_up_sums(lineup, temp_lineup_obj, player_depth_positions)

            last_two_players = '", "'.join(last_two_players)
            # look at the % for the 4 & 5 position
            player_fg3a = sqlfetch.execute_query(sqlfetch.get_avg_fg3a_by_player(FIRST_DATE_REG_SEASON, last_two_players))
            player_reb_pct = sqlfetch.execute_query(sqlfetch.get_avg_reb_pct_by_player(FIRST_DATE_REG_SEASON, last_two_players))

            # small_ball_sum.append(lineup_sum)

            if lineup_sum < 15 or player_reb_pct[0]['TOTAL_REB_PCT'] < 10:
                small_ball_poss.append(lineup['poss'])

        if len(small_ball_poss) > 0:
            # i need to know the percentages of posessions the small ball line ups take
            # percentile_small_lineups = ss.percentileofscore(small_ball_sum, 15, kind='strict')
            small_ball_poss = np.sum(small_ball_poss)
            lineup_poss = np.sum(lineup_poss)
            team_percentile_small_poss = float(small_ball_poss) / float(lineup_poss) * 100

            # print 'Small Ball Lineup (Positions) (%): {percentile_small_lineups}'.format(percentile_small_lineups=percentile_small_lineups)
            print 'Small Ball Poss (%): {team_percentile_small_poss}'.format(team_percentile_small_poss=team_percentile_small_poss)


        insert_players_string = ', '.join(sql_lineups)
        # return sql_players
        insert_sql = """INSERT INTO team_lineups VALUES {insert_players_string}""".format(insert_players_string=insert_players_string)

        cursor.execute(insert_sql)
        db.commit()

        # lets get the teams that have already played them
        for abbrev, wowy_team in WOWY_TEAMS.iteritems():
            with open('../scrape/misc/updated_depth_chart/'+abbrev+'.json') as data_file:
                data = json.load(data_file)
                player_depth_positions = data['all']

            # can reduce this call here if we do a check for if the wowy_team has played the oppo
            team_against_wowy_obj = get_lineups_by_team(wowy_team, [WOWY_TEAMS[team]], [], [], FIRST_DATE_REG_SEASON, LAST_DATE_REG_SEASON)

            if len(team_against_wowy_obj['lineups']) > 0:
                print wowy_team
                temp_lineup_obj = {}
                # small_ball_sum = []
                lineup_poss = []
                small_ball_poss = []
                for lineup in team_against_wowy_obj['lineups']:
                    # if lineup['poss'] >= 5:
                    lineup_poss.append(lineup['poss'])
                    lineup_sum = 0
                    last_two_players = []

                    # get last two players
                    for player in lineup['lineup'][-2:]:
                        split_name = player.split('.')
                        if len(split_name) > 1:
                            player = "".join(split_name)
                        last_two_players.append(player)

                    lineup_sum = process_line_up_sums(lineup, temp_lineup_obj, player_depth_positions)

                    last_two_players = '", "'.join(last_two_players)
                    # look at the % for the 4 & 5 position
                    player_fg3a = sqlfetch.execute_query(sqlfetch.get_avg_fg3a_by_player(FIRST_DATE_REG_SEASON, last_two_players))
                    player_reb_pct = sqlfetch.execute_query(sqlfetch.get_avg_reb_pct_by_player(FIRST_DATE_REG_SEASON, last_two_players))

                    # if lineup['poss'] >= 5:
                    # print ', '.join(lineup['lineup'])

                    # print 'POSS: {poss}, DEPTH_SUM: {lineup_sum}, PF_C_TOTAL_REB_PCT: {TOTAL_REB_PCT}, PF_C_TOTAL_FG3A: {TOTAL_FG3A}'.format(
                    #     poss=lineup['poss'], lineup_sum=lineup_sum, TOTAL_REB_PCT=player_reb_pct[0]['TOTAL_REB_PCT'], TOTAL_FG3A=player_fg3a[0]['TOTAL_FG3A'])

                    # small_ball_sum.append(lineup_sum)

                    if lineup_sum < 15 or player_reb_pct[0]['TOTAL_REB_PCT'] < 10:
                        small_ball_poss.append(lineup['poss'])

                if len(small_ball_poss) > 0:
                    # i need to know the percentages of posessions the small ball line ups take
                    # percentile_small_lineups = ss.percentileofscore(small_ball_sum, 15, kind='strict')
                    small_ball_poss = np.sum(small_ball_poss)
                    lineup_poss = np.sum(lineup_poss)
                    percentile_small_poss = float(small_ball_poss) / float(lineup_poss) * 100

                    # print 'Small Ball Lineup (%): {percentile_small_lineups}'.format(percentile_small_lineups=percentile_small_lineups)
                    print 'Small Ball Poss (%): {percentile_small_poss}'.format(percentile_small_poss=percentile_small_poss)

                if team in all_small_ball_lineup_obj:
                    all_small_ball_lineup_obj[team]['oppo'][abbrev] = two_decimals(percentile_small_poss)
                else:
                    all_small_ball_lineup_obj[team] = {
                        'own': two_decimals(team_percentile_small_poss),
                        'oppo': {
                            abbrev: two_decimals(percentile_small_poss)
                        }
                    }

    # print all_small_ball_lineup_obj
    # how much did they deviate from their avg lineup
    with open('../scrape/misc/updated_depth_chart/small_ball.json', 'w') as outfile:
        LOGGER.info('Writing to depth chart file: small_ball')
        json.dump(all_small_ball_lineup_obj, outfile)

def get_deiviation_lineups():

    with open('../scrape/misc/depth_chart/small_ball.json') as data_file:
        data = json.load(data_file)

        whatever_team_list = {}
        analysis_obj = {}
        for team, small_ball in data.iteritems():
            small_ball_deviated = []
            for oppo, oppo_small_ball in small_ball['against'].iteritems():
                # negative = bigger, positive = smaller
                deviated_pct = oppo_small_ball - data[oppo]['own']

                if oppo in whatever_team_list:
                    whatever_team_list[oppo].append(oppo_small_ball)
                else:
                    whatever_team_list[oppo] = [oppo_small_ball]
                # need to only account for the ones that are 2 standard deviations
                small_ball_deviated.append(deviated_pct)

            analysis_obj[team] = {
                'avg': np.average(small_ball_deviated),
                'median': np.median(small_ball_deviated)
            }

        with open('../scrape/misc/updated_depth_chart/lineup_analysis.json', 'w') as outfile:
            LOGGER.info('Writing to depth chart file: lineup_analysis')
            json.dump(analysis_obj, outfile)


def get_updated_depth_chart():

    url = urllib2.urlopen('http://basketball.realgm.com/nba/teams/Depth_Charts').read()
    soup = BeautifulSoup(url, 'html5lib')

    tables = soup.find_all('table', attrs={'class':'basketball'})
    if len(tables) == 30:
        teams = ['ATL', 'BOS', 'BRK', 'CHO', 'CHI', 'CLE', 'DAL', 'DEN', 'DET', 'GSW', 'HOU', 'IND', 'LAC', 'LAL', 'MEM', 'MIA', 'MIL', 'MIN', 'NOP', 'NYK', 'OKC', 'ORL', 'PHI', 'PHO', 'POR', 'SAC', 'SAS', 'TOR', 'UTA', 'WAS']

        for idx, table in enumerate(tables):
            current_starters = {
                'all': {}
            }
            table_body = table.find('tbody')
            rows = table_body.find_all('tr')
            for row in rows:
                players = row.find_all('td')

                for player in players[1:]:
                    player_position = player['data-th']
                    player_info = player.find('a')
                    if player_info:
                        player_link = player_info.get('href')
                        player_name = str(player_link.split('/')[2])
                        player_name = player_name.replace("-", " ")
                        rotation_role = players[0].text
                        current_starters['all'][player_name] = player_position
                        if player_position in current_starters:
                            current_starters[player_position].append({
                                "player": player_name,
                                "role": rotation_role
                            })
                        else:
                            current_starters[player_position] = [{
                                "player": player_name,
                                "role": rotation_role
                            }]

            with open('../scrape/misc/updated_depth_chart/'+teams[idx]+'.json', 'w') as outfile:
                LOGGER.info('Writing to depth chart file:'+ teams[idx])
                json.dump(current_starters, outfile)

    # return current_starters

DEPTH_TO_DK_TRANSLATE = {
    "Matt Dellavedova": "Matthew Dellavedova",
    "James McAdoo": "James Michael McAdoo",
    "John Lucas": "John Lucas III",
    "Karl Anthony Towns": "Karl-Anthony Towns",
    "Tim Hardaway Jr": "Tim Hardaway Jr.",
    "DeAndre Bembry": "DeAndre' Bembry",
    "Kentavious Caldwell Pope": "Kentavious Caldwell-Pope",
    "Kyle OQuinn": "Kyle O'Quinn",
    "Willy Hernangomez": "Guillermo Hernangomez",
    "JJ Barea": "J.J. Barea",
    "Dorian Finney Smith": "Dorian Finney-Smith",
    "AJ Hammons": "A.J. Hammons",
    "CJ McCollum": "C.J. McCollum",
    "Al Farouq Aminu": "Al-Farouq Aminu",
    "Domas Sabonis": "Domantas Sabonis",
    "JR Smith": "J.R. Smith",
    "Raulzinho Neto": "Raul Neto",
    "Michael Carter Williams": "Michael Carter-Williams",
    "RJ Hunter": "R.J. Hunter",
    "Michael Kidd Gilchrist": "Michael Kidd-Gilchrist",
    "KJ McDaniels": "K.J. McDaniels",
    "Maybyner Nene": "Nene Hilario",
    "Kelly Oubre Jr": "Kelly Oubre Jr.",
    "DAngelo Russell": "D'Angelo Russell",
    "Marcelinho Huertas": "Marcelo Huertas",
    "Larry Nance Jr": "Larry Nance Jr.",
    "TJ McConnell": "T.J. McConnell",
    "Timothe Luwawu Cabarrot": "Timothe Luwawu-Cabarrot",
    "TJ Warren": "T.J. Warren",
    "PJ Tucker": "P.J. Tucker",
    "Derrick Jones": "Derrick Jones Jr.",
    "JJ Redick": "J.J. Redick",
    "Luc Mbah a Moute": "Luc Richard Mbah a Moute",
    "Willie Cauley Stein": "Willie Cauley-Stein",
    "George Papagiannis": "Georgios Papagiannis",
    "DJ Augustin": "D.J. Augustin",
    "CJ Watson": "C.J. Watson",
    "CJ Wilcox": "C.J. Wilcox",
    "Stephen Zimmerman": "Stephen Zimmerman Jr.",
    "Rondae Hollis Jefferson": "Rondae Hollis-Jefferson",
    "CJ Miles": "C.J. Miles",
    "Glenn Robinson": "Glenn Robinson III",
    "ETwaun Moore": "E'Twaun Moore"
}

DK_TO_DEPTH_TRANSLATE = dict((v,k) for k,v in DEPTH_TO_DK_TRANSLATE.iteritems())

def get_dk_player_names():
    today_date = date.today()
    yesterday_date = today_date - timedelta(days=2)

    delta = today_date - yesterday_date

    # for the range of the past week
    dk_players = []
    for i in range(delta.days + 1):
        prev_date = yesterday_date + timedelta(days=i)
        with open('../scrape/csv/'+str(prev_date)+'.csv',) as csv_file:
            try:
                next(csv_file, None)
                players = csv.reader(csv_file)
                for player in players:
                    name = player[1]
                    if name not in dk_players:
                        dk_players.append(name)

            except csv.Error as e:
                sys.exit('file %s: %s' % (csv_file, e))

    return dk_players

def process_depth_charts():
    depth_players = []
    for team in TEAMS_DICT:
        with open('../scrape/misc/updated_depth_chart/'+team+'.json') as data_file:
            data = json.load(data_file)
            positions = ['PG', 'SG', 'SF', 'PF', 'C']
            for position in positions:
                depth = data[position]
                for player in depth:
                    depth_players.append(player['player'])

    return depth_players

def compare_players():
    depth_players = process_depth_charts()
    dk_players = get_dk_player_names()
    for player in depth_players:
        if player not in dk_players and player not in DEPTH_TO_DK_TRANSLATE:
            print "missed"

def get_sql_player_names():
    sql_players = []
    all_sql_players = sqlfetch.execute_query(sqlfetch.get_all_players_played(FIRST_DATE_REG_SEASON, LAST_DATE_REG_SEASON))
    for players in all_sql_players:
        sql_players.append(players['NAME'])

    return sql_players


def compare_sql_players():
    dk_players = get_dk_player_names()
    sql_players = get_sql_player_names()
    for player in dk_players:
        if player not in sql_players:
            print player

DK_TO_SQL_TRANSLATE = {
    "C.J. McCollum": "CJ McCollum",
    "DeAndre' Bembry": "DeAndre Bembry",
    "R.J. Hunter": "RJ Hunter",
    "T.J. Warren": "TJ Warren",
    "J.J. Barea": "Jose Juan Barea",
    "C.J. Miles": "CJ Miles",
    "J.J. Redick": "JJ Redick",
    "P.J. Tucker": "PJ Tucker",
    "Nene Hilario": "Nene",
    "Juancho Hernangomez": "Juan Hernangomez",
    "A.J. Hammons": "AJ Hammons",
    "Derrick Jones Jr.": "Derrick Jones, Jr.",
    "K.J. McDaniels": "KJ McDaniels",
    "C.J. Watson": "CJ Watson",
    "C.J. Wilcox": "CJ Wilcox",
    "Stephen Zimmerman Jr.": "Stephen Zimmerman",
    "T.J. McConnell": "TJ McConnell",
    "Kelly Oubre Jr.": "Kelly Oubre",
    "Timothe Luwawu-Cabarrot": "Timothe Luwawu",
    "Guillermo Hernangomez": "Willy Hernangomez",
    "Glenn Robinson III": "Glenn Robinson",
    "Wade Baldwin IV": "Wade Baldwin",
    "Luc Richard Mbah a Moute": "Luc Mbah a Moute"
}

SQL_TO_DK_TRANSLATE = dict((v,k) for k,v in DK_TO_SQL_TRANSLATE.iteritems())

DK_TO_WOWY_TRANSLATE = {
    "Sergio Rodriguez": unicode("Sergio Rodríguez", "utf-8"),
    "Alex Abrines": unicode("Álex Abrines", "utf-8"),
    "Nicolas Laprovittola": unicode("Nicolás Laprovittola", "utf-8"),
    "Dante Exum": unicode("Danté Exum", "utf-8")
}

WOWY_TO_DK_TRANSLATE = dict((v,k) for k,v in DK_TO_WOWY_TRANSLATE.iteritems())

def compare_wowy_players():
    dk_players = get_dk_player_names()
    wowy_players = get_all_wowy_players()
    for player in dk_players:
        if player not in wowy_players:
            print player

# compare_wowy_players()

def create_player_depth_table():
    cursor.execute("DROP TABLE IF EXISTS player_depth")

    sql = """CREATE TABLE player_depth (
              PLAYER_ID varchar(255) PRIMARY KEY,
              PLAYER_NAME varchar(255),
              TEAM_ID varchar(255),
              TEAM_NAME varchar(255),
              POSITION_1 varchar(255),
              POSITION_2 varchar(255),
              DK_POSITION_1 varchar(255),
              DK_POSITION_2 varchar(255),
              ROLE varchar(255))"""

    cursor.execute(sql)
    # insert
    try:
        sql_players = []
        all_sql_players = sqlfetch.execute_query(sqlfetch.get_all_players_played(FIRST_DATE_REG_SEASON, LAST_DATE_REG_SEASON))

        sql_players_dict = {}
        for players in all_sql_players:
            sql_players_dict[players['NAME']] = {
                'name': players['NAME'],
                'player_id': players['PLAYER_ID'],
                'team_id': players['TEAM_ID'],
                'team_name': players['TEAM_ABBREVIATION']
            }

        # get all the players from the depth chart
        teams = ['ATL', 'BOS', 'BRK', 'CHO', 'CHI', 'CLE', 'DAL', 'DEN', 'DET', 'GSW', 'HOU', 'IND', 'LAC', 'LAL', 'MEM', 'MIA', 'MIL', 'MIN', 'NOP', 'NYK', 'OKC', 'ORL', 'PHI', 'PHO', 'POR', 'SAC', 'SAS', 'TOR', 'UTA', 'WAS']

        for team in teams:
            with open('../scrape/misc/updated_depth_chart/'+team+'.json') as data_file:
                data = json.load(data_file)
                positions = ['PG', 'SG', 'SF', 'PF', 'C']
                for position in positions:
                    depth = data[position]
                    for player in depth:
                        player_name = player['player']
                        player_role = player['role']

                        # DEPTH TO SQL TRANSLATE
                        if player_name in DEPTH_TO_DK_TRANSLATE:
                            player_name = DEPTH_TO_DK_TRANSLATE[player_name]
                            if player_name in DK_TO_SQL_TRANSLATE:
                                player_name = DK_TO_SQL_TRANSLATE[player_name]

                        if player_name in sql_players_dict:
                            player_name = sql_players_dict[player_name]['name']
                            player_id = sql_players_dict[player_name]['player_id']
                            team_id = sql_players_dict[player_name]['team_id']
                            team_name = sql_players_dict[player_name]['team_name']
                            position_1 = position
                            role = player_role

                            val_string = '("{player_id}", "{player_name}", "{team_id}", "{team_name}", '\
                                            '"{position_1}", NULL, NULL, NULL, "{role}")'.format(
                                                player_id=player_id, player_name=player_name, \
                                                team_id=team_id, team_name=team_name, \
                                                position_1=position_1, role=role
                                            )

                            sql_players.append(val_string)

            # if players['NAME'] in SQL_TO_DK_TRANSLATE
        insert_players_string = ', '.join(sql_players)
        # return sql_players
        insert_sql = """INSERT INTO player_depth VALUES {insert_players_string}""".format(insert_players_string=insert_players_string)

        cursor.execute(insert_sql)
        db.commit()
    except:
        db.rollback()

def create_oppo_stats_table():

    # CREATE VIEW ALL_GAME_IDS AS
    #     SELECT tbt.game_id, tbt.TEAM_ABBREVIATION, tbt.TEAM_ID FROM traditional_boxscores_team as tbt

    # CREATE VIEW TEAM_FOULS AS
    # SELECT
    #     gl.`TEAM_ABBREVIATION` as TEAM,
    #     gl.TEAM_ID,
    #     ROUND(avg(tb.PF),
    #     2) as AVG_FOULS
    # FROM
    #     `sportvu_defense_team_game_logs`as gl
    # LEFT JOIN
    #     traditional_boxscores_team as tb
    #         ON tb.game_id = gl.game_id
    #         AND tb.team_id = gl.team_id
    # WHERE
    #     gl.date >= "2016-10-25"
    # GROUP BY
    #     TEAM
    cursor.execute("DROP TABLE IF EXISTS OPP_STATS_TABLE")

    sql = """
        CREATE TABLE OPP_STATS_TABLE AS SELECT
            tb.TEAM_NAME as NAME,
            tb.TEAM_ABBREVIATION as TEAM_NAME,
            ROUND(avg(dr.OPP_OREB_PCT),
            3) as AVG_OPP_OREB_PCT,
            ROUND(avg(rgl.REB),
            2) as NUM_REB_ALLOWED,
            ROUND(avg(rgl.OREB_CHANCES),
            2) as OPP_OREB_CHANCES,
            ROUND(avg(rgl.DREB_CHANCES),
            2) as OPP_DREB_CHANCES,
            ROUND(avg(rgl.REB_CHANCES),
            2) as OPP_REB_CHANCES,
            ROUND(avg(rgl.REB_CHANCE_PCT_ADJ),
            2) as OPP_REB_PCT_ADJ,
            ROUND(avg(csl.CATCH_SHOOT_FGA),
            3) as OPP_AVG_CATCH_SHOOT_FGA,
            ROUND(avg(csl.CATCH_SHOOT_PTS),
            3) as OPP_AVG_CATCH_SHOOT_PTS,
            ROUND(avg(csl.CATCH_SHOOT_FG_PCT),
            3) as OPP_CATCH_SHOOT_FG_PCT,
            ROUND(avg(ptl.PAINT_TOUCHES),
            3) as OPP_AVG_PAINT_TOUCHES,
            ROUND(avg(ptl.PAINT_TOUCH_FGA),
            3) as OPP_AVG_PAINT_TOUCH_FGA,
            ROUND(avg(ptl.PAINT_TOUCH_PTS),
            3) as OPP_PAINT_TOUCH_PTS,
            ROUND(avg(potl.POST_TOUCHES),
            3) as OPP_AVG_POST_TOUCHES,
            ROUND(avg(potl.POST_TOUCH_FGA),
            3) as OPP_AVG_POST_TOUCH_FGA,
            ROUND(avg(potl.POST_TOUCH_PTS),
            3) as OPP_POST_TOUCH_PTS,
            ROUND(avg(drl.DRIVES),
            2) as AVG_NUM_DRIVES_FACED,
            ROUND(avg(drl.DRIVE_FGA),
            2) as AVG_NUM_DRIVE_FGA_ALLOWED,
            ROUND(avg(drl.DRIVE_FTA),
            2) as AVG_NUM_DRIVE_FTA_ALLOWED,
            ROUND(avg(drl.DRIVE_PTS),
            2) as AVG_DRIVE_PTS_ALLOWED,
            ROUND(avg(drl.DRIVE_PF),
            2) as AVG_NUM_DRIVE_PF_COMMITED,
            ROUND(avg(tb3.AVG_FOULS),
            2) as AVG_FOULS
        FROM
            four_factors_boxscores_team as dr
        LEFT JOIN
            traditional_boxscores_team as tb
                ON tb.TEAM_ID = dr.TEAM_ID
                AND tb.GAME_ID = dr.GAME_ID
        left join
            game_summary as gs
                on dr.game_id = gs.game_id
        left join
            sportvu_rebounding_team_game_logs as rgl
                ON rgl.GAME_ID = dr.GAME_ID
        left join
            sportvu_catch_shoot_team_game_logs as csl
                ON csl.GAME_ID = dr.GAME_ID
        left join
            sportvu_paint_touches_team_game_logs as ptl
                ON ptl.GAME_ID = dr.GAME_ID
        left join
            sportvu_post_touches_team_game_logs as potl
                ON potl.GAME_ID = dr.GAME_ID
        left join
            sportvu_drives_team_game_logs as drl
                ON drl.GAME_ID = dr.GAME_ID
        LEFT JOIN
            team_fouls as tb3
                on tb3.TEAM_ID = tb.TEAM_ID
        LEFT JOIN
            ALL_GAME_IDS as tb2
                ON tb2.game_id = dr.GAME_ID
                and tb2.TEAM_ID != tb.TEAM_ID
        WHERE
            gs.GAME_DATE_EST >= '2016-10-26'
        GROUP BY
            TEAM_NAME
    """

    cursor.execute(sql)


# create_player_depth_table()
# compare_players()
# compare_sql_players()
# compare_wowy_players()

# get_updated_depth_chart()
# create_player_depth_table()
# create_oppo_stats_table
# get_fantasy_news()
# get_team_against_position()
# get_all_lineups()
# get_deiviation_lineups()


def test_markov_jimmy():
    query = """
                SELECT STR_TO_DATE(gs.game_date_est,"%Y-%m-%d") as DATE, ub.PLAYER_NAME as NAME, 
                ub.MIN, ub.TEAM_ABBREVIATION as TEAM_NAME, 
                tb.FG3M*0.5 + tb.REB*1.25+tb.AST*1.25+tb.STL*2+tb.BLK*2+tb.TO*-0.5+tb.PTS*1 as DK_POINTS 
                FROM usage_boxscores as ub LEFT JOIN game_summary as gs ON gs.game_id = ub.game_id 
                LEFT JOIN traditional_boxscores as tb ON tb.game_id = ub.game_id AND tb.player_id = ub.player_id 
                WHERE ub.PLAYER_NAME = "Kevin Love" AND STR_TO_DATE(gs.game_date_est,"%Y-%m-%d") >= "2015-10-27" AND ub.MIN >= 30 ORDER BY DATE
            """
    query_results = sqlfetch.execute_query(query)

    # get the first game and set that as a starting avg
    dk_avg = query_results[0]['DK_POINTS']

    num_games = len(query_results)

    prob_obj = {
        'better_than': {
            'in_std': {
                'greater_than' : [],
                'less_than' : []
            },
            'out_std': {
                'greater_than' : [],
                'less_than' : []
            },
            'equal_to' : []
        },
        'less_than': {
            'in_std': {
                'greater_than' : [],
                'less_than' : []
            },
            'out_std': {
                'greater_than' : [],
                'less_than' : []
            },
            'equal_to' : []
        }
    }
    dk_pts_list = []
    total_sum = dk_avg

    # within one deviation of the avg
    for idx, game in enumerate(query_results):
        current_game = game['DK_POINTS']

        dk_pts_list.append(current_game)

        current_std = np.std(dk_pts_list, dtype=np.float64, ddof=1)

        # get the std
        # comp_std = np.std(dk_pts_list)
        # print current_std
        try:
            next_game = query_results[idx+1]['DK_POINTS']
            within_deviation = (query_results[idx+1]['DK_POINTS'] - current_std) \
                                <= dk_avg <= \
                                (query_results[idx+1]['DK_POINTS'] + current_std)
        except IndexError:
            within_deviation = False

        # print within_deviation
        b_in_std = prob_obj['better_than']['in_std']
        b_out_std = prob_obj['better_than']['out_std']
        l_in_std = prob_obj['less_than']['in_std']
        l_out_std = prob_obj['less_than']['out_std']

        if current_game > dk_avg:
            # within one deviation
            # coming off a better than avg game was the next game better than this one ?
            # coming off a better than avg game was the next game worse than this one?
            # coming off a better than avg game was the next game same than this one?
            try:
                # print current_game
                # print query_results[idx+1]['DK_POINTS']
                if next_game > current_game:
                    if within_deviation:
                        b_in_std['greater_than'].append(next_game)
                    else:
                        b_out_std['greater_than'].append(next_game)

                if next_game < current_game:
                    if within_deviation:
                        b_in_std['less_than'].append(next_game)
                    else:
                        b_out_std['less_than'].append(next_game)

                # exclude logic for the last entry
                if next_game == current_game and idx != len(query_results) - 1:
                    prob_obj['better_than']['equal_to'].append(next_game)

            except IndexError:
                print 'no future games'

        elif current_game <= dk_avg:
            # coming off a less than avg game was the next game better than this one?
            # coming off a less than avg game was the next game worse than this one?
            # coming off a less than avg game was the next game same than this one?
            try:
                if next_game > current_game:
                    if within_deviation:
                        l_in_std['greater_than'].append(next_game)
                    else:
                        l_out_std['greater_than'].append(next_game)

                if next_game < current_game:
                    if within_deviation:
                        l_in_std['less_than'].append(next_game)
                    else:
                        l_out_std['less_than'].append(next_game)

                if next_game == current_game and idx != len(query_results) - 1:
                    prob_obj['less_than']['equal_to'].append(next_game)
            except IndexError:
                print 'no future games'

        total_sum += current_game
        dk_avg = (total_sum) / (idx+1)


    pp.pprint(prob_obj)

    #
    better_than_total = float(len(b_in_std['greater_than']) + len(b_in_std['less_than']) + len(b_out_std['greater_than']) + len(b_out_std['less_than']))
    less_than_total = float(len(l_in_std['greater_than']) + len(l_in_std['less_than']) + len(l_out_std['greater_than']) + len(l_out_std['less_than']))

    print float(len(b_in_std['greater_than'])) / better_than_total
    print float(len(b_in_std['less_than'])) / better_than_total

    print float(len(b_out_std['greater_than'])) / better_than_total
    print float(len(b_out_std['less_than'])) / better_than_total

    print float(len(l_in_std['greater_than'])) / less_than_total
    print float(len(l_in_std['less_than'])) / less_than_total

    print float(len(l_out_std['greater_than'])) / less_than_total
    print float(len(l_out_std['less_than'])) / less_than_total



test_markov_jimmy()

