import urllib2
import pprint
import csv
import logging
import json
import requests
# import numpy as np
import scipy.stats as ss
from bs4 import BeautifulSoup
from datetime import date, timedelta, datetime

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

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

# just the lineup call
def get_lineups_by_team(team, vs_teams, on_players, off_players, start_date, end_date):

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


def process_depth_charts():
    player_obj = {}
    for team in TEAMS_DICT:
        with open('../scrape/misc/depth_chart/'+team+'.json') as data_file:
            data = json.load(data_file)
            positions = ['PG', 'SG', 'SF', 'PF', 'C']
            for position in positions:
                depth = data[position]
                for player in depth:
                    player_obj[player['player']] = position

    return player_obj

def get_all_lineups():
    all_teams = get_all_teams_playing_today()
    depth_chart_obj = process_depth_charts()

    for team in all_teams:
        # lineup analysis
        print 'AGAINST ' + team
        team_wowy_obj = get_lineups_by_team(WOWY_TEAMS[team], 'all', [], [], FIRST_DATE_REG_SEASON, LAST_DATE_REG_SEASON)
        temp_lineup_obj = {}
        for lineup in team_wowy_obj['lineups'][0:10:1]:
            if lineup['poss'] >= 5:
                print ', '.join(lineup['lineup'])
                print 'Poss: {poss}, Min: {min}'.format(poss=lineup['poss'], min=lineup['min'])

        # lets get the teams that have already played them
        for abbrev, wowy_team in WOWY_TEAMS.iteritems():
            print wowy_team
            team_against_wowy_obj = get_lineups_by_team(wowy_team, [WOWY_TEAMS[team]], [], [], FIRST_DATE_REG_SEASON, LAST_DATE_REG_SEASON)

            temp_lineup_obj = {}
            lineup_sum_list = []
            for lineup in team_against_wowy_obj['lineups'][0:10:1]:
                lineup_sum = 0
                print ', '.join(lineup['lineup'])
                for idx, player in enumerate(lineup['lineup']):
                    try:
                        player_lineup_position = POSITION_TRANSLATE_DICT[idx+1]

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
                            # print depth_chart_obj[player]
                            if player in depth_chart_obj:
                                player_index = REVERSE_POSITION_TRANSLATE_DICT[depth_chart_obj[player]]
                            else:
                                player_index = idx+1
                            # print player_index
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

                # sum of the lineup
                print lineup_sum
                lineup_sum_list.append(lineup_sum)

            print 'PERCENT'
            # i need to look at the 3pt attempts esp from the 4 & 5 position
            if len(lineup_sum_list > 0):
                print ss.percentileofscore(lineup_sum_list, 15, kind='strict')

            sorted_temp_lineup_obj = sorted(temp_lineup_obj, key=lambda x: (temp_lineup_obj[x]['poss'], temp_lineup_obj[x]['num_lineups']), reverse=True)
            for player in sorted_temp_lineup_obj:
                player_name = player.encode('ascii', 'ignore')
                player_obj = temp_lineup_obj[player]
                print '{player} Poss: {poss}, Lineups: {num_lineups}'.format(
                    player=player_name, poss=player_obj['poss'], num_lineups=player_obj['num_lineups'])

                for positon, poss in player_obj['positions'].iteritems():
                    print '{positions}: {poss}'.format(positions=positon, poss=poss)

get_all_lineups()
# get_fantasy_news()
# get_team_against_position()