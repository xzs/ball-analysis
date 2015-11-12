
import urllib2
import pprint
import csv
import logging
import json

from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = 'http://www.basketball-reference.com'
DEPTH_URL = 'http://www.rotoworld.com/teams/depth-charts/nba.aspx'
YEAR = '2016'


def get_depth_chart():
    current_starters = {}
    url = urllib2.urlopen(DEPTH_URL)
    soup = BeautifulSoup(url, 'html5lib')
    table = soup.find('table', attrs={'id':'cp1_tblDepthCharts'})
    table_body = table.find('tbody')

    rows = table_body.find_all('tr')

    for row in rows:
        logger.info('Getting starters for all teams');

        players = row.find_all('td')
        # loop through the players
        if len(players) > 0:
            for player in players:
                starter_table = player.find('table')
                if starter_table:
                    starter_body = starter_table.find('tbody')
                    starter = starter_body.find_all('tr', attrs={'class': 'highlight-row'})
                    for info in starter:
                        pos_player = info.find_all('td')
                        for td in pos_player[1::2]:
                            position = td.find('a').text
                            current_starters[position] = {'status': 'available'}
                            news = td.find('span')
                            if news:
                                current_starters[position]['status'] = news.text

    with open('misc/starters.json', 'w') as outfile:
        logger.info('Writing to json file')
        json.dump(current_starters, outfile)

    return current_starters

# Get all teams
def get_active_teams():

    teams_dict = {}

    url = urllib2.urlopen(BASE_URL+'/teams/')
    # we have to use the html5lib parser, as some elements were not showing up fully
    soup = BeautifulSoup(url, 'html5lib')

    table = soup.find('table', attrs={'id':'active'})
    table_body = table.find('tbody')
    rows = table_body.find_all('tr', attrs={'class':'full_table'})

    for row in rows:
        links = row.find_all('a')
        for link in links:
            logger.info('Getting team information')
            team_link = link.get('href')
            team = str(team_link.split('/')[2])
            schedule = str(link.get('href')) + YEAR + '_games.html'

            if team == 'NJN':
                team = 'BRK'
                team_url = '/teams/BRK/' + YEAR + '.html'
                schedule = '/teams/BRK/' + YEAR + '_games.html'
            elif team == 'CHA':
                team = 'CHO'
                team_url = '/teams/CHO/' + YEAR + '.html'
                schedule = '/teams/CHO/' + YEAR + '_games.html'
            elif team == 'NOH':
                team = 'NOP'
                team_url = '/teams/NOP/' + YEAR + '.html'
                schedule = '/teams/NOP/' + YEAR + '_games.html'
            else:
                team_url = str(link.get('href')) + YEAR + '.html'

            # create the object for each team
            team_obj = {
                'name': str(link.text),
                'url' : team_url,
                'schedule': schedule

            }
            teams_dict[team] = team_obj
            logger.info('Finished getting team information for: '+ team)

    return teams_dict

# Get all players
def get_current_roster(teams_dict):

    players_dict = {}

    for team in teams_dict:
        logger.info('Getting players information for: '+ team)
        logger.info(BASE_URL+teams_dict[team]['url'])
        url = urllib2.urlopen(BASE_URL+teams_dict[team]['url'])
        soup = BeautifulSoup(url, 'html5lib')

        players_dict[str(team)] = []

        table = soup.find('table', attrs={'id':'roster'})
        table_body = table.find('tbody')
        rows = table_body.find_all('tr')

        for row in rows:
            # get the array of anchors
            links = row.find_all('a')
            # get every other link to get the player
            player = links[::2][0]
            player_name = str(player.text)
            player_link = str(player.get('href'))
            player_log = player_link.split('.')[0]+'/gamelog/'+YEAR

            player_obj = {
                'url': player_link,
                'log': player_log
            }

            players_dict[team].append(
                {
                    player_name: player_obj
                }
            )
            logger.info('Finished getting player information for: '+ player_name)

        logger.info('Finished getting players information for: '+ team)

    return players_dict

# Get the game logs for each player
def get_player_log(players_dict):

    for team in players_dict:
        # loop through the array of players
        for player in players_dict[team]:
            for name in player:
                logger.info('open url for: '+name)
                url = urllib2.urlopen(BASE_URL+player[name]['log'])
                soup = BeautifulSoup(url, 'html5lib')
                log_rows = []

                table = soup.find('table', attrs={'id':'pgl_basic'})
                if table:
                    logger.info('Getting game logs for: ' + name)
                    table_body = table.find('tbody')
                    rows = table_body.find_all('tr')

                    for row in rows:
                        log_rows.append([val.text.encode('utf8') for val in row.find_all('td')])

                    with open('player_logs/'+YEAR+'/'+name+'.csv', 'wb') as f:
                        writer = csv.writer(f)
                        logger.info('Writing log csv for: ' + name)
                        writer.writerows(row for row in log_rows if row)

# Get the schedule for each team
def get_team_schedule(teams_dict):

    for team in teams_dict:
        print BASE_URL+teams_dict[team]['schedule']
        url = urllib2.urlopen(BASE_URL+teams_dict[team]['schedule'])
        soup = BeautifulSoup(url, 'html5lib')
        log_rows = []

        table = soup.find('table', attrs={'id':'teams_games'})
        if table:
            logger.info('Getting schedule for: ' + team)
            table_body = table.find('tbody')
            rows = table_body.find_all('tr')

            for row in rows:
                log_rows.append([val.text.encode('utf8') for val in row.find_all('td')])

            with open('team_schedules/'+YEAR+'/'+team+'.csv', 'wb') as f:
                writer = csv.writer(f)
                logger.info('Writing schedule csv for: ' + team)
                writer.writerows(row for row in log_rows if row)


pp = pprint.PrettyPrinter(indent=4)
TEAMS_DICT = get_active_teams()
get_team_schedule(TEAMS_DICT)
PLAYERS_DICT = get_current_roster(TEAMS_DICT)
get_player_log(PLAYERS_DICT);
get_depth_chart()
