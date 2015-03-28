import urllib2
import pprint
import csv
import logging
from bs4 import BeautifulSoup

BASE_URL = 'http://www.basketball-reference.com'
YEAR = '2015'

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
            print 'Getting team information'
            team_link = link.get('href')
            team = team_link.split('/')[2]

            if team == 'NJN':
                team = 'BRK'
                team_url = '/teams/BRK/' + YEAR + '.html'
            elif team == 'CHA':
                team = 'CHO'
                team_url = '/teams/CHO/' + YEAR + '.html'
            elif team == 'NOH':
                team = 'NOP'
                team_url = '/teams/NOP/' + YEAR + '.html'
            else:
                team_url = link.get('href') + YEAR + '.html'


            # create the object for each team
            team_obj = {
                'name': str(link.text),
                'url' : team_url
            }
            teams_dict[team] = team_obj
            print 'Finished getting team information for: '+ team

    return teams_dict

# Get all players
def get_current_roster(teams_dict):

    players_dict = {}
    
    for team in teams_dict:
        print 'Getting players information for: '+ team
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
            print 'Finished getting player information for: '+ player_name
        
        print 'Finished getting players information for: '+ team

    return players_dict


def get_player_log(players_dict):

    for team in players_dict:
        # loop through the array of players
        for player in players_dict[team]:
            for name in player:
                url = urllib2.urlopen(BASE_URL+player[name]['log'])
                soup = BeautifulSoup(url, 'html5lib')
                log_rows = []

                table = soup.find('table', attrs={'id':'pgl_basic'})
                if table:
                    table_body = table.find('tbody')
                    rows = table_body.find_all('tr')

                    for row in rows:
                        log_rows.append([val.text.encode('utf8') for val in row.find_all('td')])

                    with open('player_logs/'+name+'.csv', 'wb') as f:
                        writer = csv.writer(f)
                        writer.writerows(row for row in log_rows if row)

pp = pprint.PrettyPrinter(indent=4)
TEAMS_DICT = get_active_teams()
PLAYERS_DICT = get_current_roster(TEAMS_DICT)
get_player_log(PLAYERS_DICT);

