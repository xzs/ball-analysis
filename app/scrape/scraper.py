
import urllib2
import pprint
import csv
import logging
import json

from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# we need to put this in
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
    'Portland Trailblazers': 'POR',
    'Sacramento Kings': 'SAC',
    'San Antonio Spurs': 'SAS',
    'Toronto Raptors': 'TOR',
    'Utah Jazz': 'UTA',
    'Washington Wizards': 'WAS'
}
# some links dont transfer from bbref
TRANSLATE_DICT = {
    'CHA':'CHO',
    'GS':'GSW',
    'LAK':'LAL',
    'MLW':'MIL',
    'NO':'NOP',
    'NY':'NYK',
    'BKN':'BRK',
    'SA':'SAS',
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
BASE_URL = 'http://www.basketball-reference.com'
DEPTH_URL = 'http://www.rotoworld.com/teams/clubhouse/nba/'
NEWS_URL = 'http://www.rotoworld.com/teams/nba/'
MATCHUP_URL = 'http://www.rotowire.com/daily/nba/defense-vspos.htm'

YEAR = '2016'


def get_fantasy_news():

    for team, name in NEWS_DICT.iteritems():
        # add the - to the team names
        split_string = name.split()
        new_string = ''
        for string in split_string:
            new_string += string +'-'
        team_link = new_string[:-1]

        logger.info('Scraping news for: '+ team)
        news_content = []
        url = urllib2.urlopen(NEWS_URL+'/'+team+'/'+team_link)
        soup = BeautifulSoup(url, 'html5lib')
        news_holder = soup.find_all('div', attrs={'class':'RW_pn'})[1]
        news = news_holder.find_all('div', attrs={'class':'pb'})

        for info in news:
            headline = info.find('div', attrs={'class':'headline'})
            name = headline.find('a').text
            news_report = info.find('div',attrs={'class':'report'}).find('p').text
            news_impact = info.find('div',attrs={'class':'impact'}).text

            news_content.append({
                'player': name,
                'report': news_report,
                'impact': news_impact,
            })

        if team in TRANSLATE_DICT:
            team = TRANSLATE_DICT[team]

        with open('misc/news/'+team+'.json', 'w') as outfile:
            logger.info('Writing news to json file: '+ team)
            json.dump(news_content, outfile)


def get_depth_chart():

    for team in NEWS_DICT:
        current_starters = {}
        url = urllib2.urlopen(DEPTH_URL+team)
        soup = BeautifulSoup(url, 'html5lib')

        # get id of the table
        table = soup.find('table', attrs={'id':'cp1_ctl04_tblDepthCharts'})
        table_body = table.find('tbody')
        rows = table_body.find_all('tr')
        for row in rows[2:]:
            players = row.find_all('td')
            for player in players:
                possible_position = player.text
                if possible_position in ['PG', 'SG', 'SF', 'PF', 'C']:
                    current_starters[possible_position] = []
                    current_position = possible_position
                else:
                    player_dict = {}
                    if player.find('a'):
                        player_dict['player'] = str(player.find('a').text)
                        player_dict['status'] = 'Available'
                        if player.find('div', attrs={'class': 'playercard'}):
                            player_card = player.find('div', attrs={'class': 'playercard'})
                            player_dict['status'] = player_card.find('span').text

                        current_starters[current_position].append(player_dict)

        if team in TRANSLATE_DICT:
            team = TRANSLATE_DICT[team]

        with open('misc/depth_chart/'+team+'.json', 'w') as outfile:
            logger.info('Writing to depth chart file:'+ team)
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

        team_dict = {}

        # find the team stats id=team_stats
        team_stats_table = soup.find('table', attrs={'id':'team_stats'})
        team_stats_table_header = team_stats_table.find('thead')
        team_stats_header_rows = team_stats_table_header.find('tr').find_all('th')

        team_stats_table_body = team_stats_table.find('tbody')
        team_stats_rows = team_stats_table_body.find_all('tr')[1].find_all('td')
        team_rank_rows = team_stats_table_body.find_all('tr')[2].find_all('td')

        # find the team stats id=team_stats
        team_misc_table = soup.find('table', attrs={'id':'team_misc'})
        team_misc_table_header = team_misc_table.find('thead')
        team_misc_header_rows = team_misc_table_header.find_all('tr')[1].find_all('th')

        team_misc_table_body = team_misc_table.find('tbody')
        team_misc_rows = team_misc_table_body.find_all('tr')[0].find_all('td')
        team_misc_rank_rows = team_misc_table_body.find_all('tr')[1].find_all('td')

        # misc
        for header_row, stat_row, rank_row in zip(team_misc_header_rows, team_misc_rows, team_misc_rank_rows):
            stat = str(header_row.text)
            if header_row.text != '':
                team_dict[stat] = {}
                team_dict[stat]['stat'] = str(stat_row.text)
                team_dict[stat]['rank'] = str(rank_row.text)

        # loop through the rows in parallel
        for header_row, stat_row, rank_row in zip(team_stats_header_rows, team_stats_rows, team_rank_rows):
            stat = str(header_row.text)
            if header_row.text != '':
                team_dict[stat] = {}
                team_dict[stat]['stat'] = str(stat_row.text)
                team_dict[stat]['rank'] = str(rank_row.text)

        with open('misc/team_stats/'+team+'.json', 'w') as outfile:
            logger.info('Writing news to json file: '+ team)
            json.dump(team_dict, outfile)

        # find the advanced stats id=advanced
        advanced_table = soup.find('table', attrs={'id':'advanced'})
        advanced_table_header = advanced_table.find('thead')
        advanced_header_rows = advanced_table_header.find('tr').find_all('th')

        advanced_table_body = advanced_table.find('tbody')
        advanced_stats_rows = advanced_table_body.find_all('tr')

        # loop through each player and append each key for them
        for player in advanced_stats_rows:
            player_stats_dict = {}
            player_stats = player.find_all('td')
            name = str(player_stats[1].text)
            player_stats_dict[name] = {}
            for stat, header in zip(player_stats, advanced_header_rows):
                category = str(header.text)
                if category != '':
                    player_stats_dict[name][category] = str(stat.text)

            with open('json_files/player_stats/'+YEAR+'/'+name+'.json', 'w') as outfile:
                logger.info('Writing news to json file: '+ name)
                json.dump(player_stats_dict, outfile)

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


def get_team_against_position():
    pos_list = ['PG', 'SG', 'SF', 'PF', 'C']
    site = 'DraftKings'
    matchup_data = {}

    for position in pos_list:
        logger.info('getting matchup information for: '+position)
        url = urllib2.urlopen(MATCHUP_URL+'?site=%s&pos=%s' % (site, position))
        soup = BeautifulSoup(url, 'html5lib')

        table = soup.find('table', attrs={'class': 'footballproj-table'})
        header = table.find('thead')
        team_header = header.find_all('tr')[1].find_all('th')

        table_body = table.find('tbody')
        teams = table_body.find_all('tr')

        for team in teams:
            team_stats = team.find_all('td')
            tempname = str(team_stats[0].text)
            team_name = REVERSE_TEAMS_DICT[tempname]

            if team_name not in matchup_data:
                matchup_data[team_name] = {}

            if position not in matchup_data[team_name]:
                matchup_data[team_name][position] = {}

            # zip with the header so it runs in "parallel"
            for header, stat in zip(team_header, team_stats):
                category = str(header.text)
                matchup_data[team_name][position][category] = str(stat.text)


    # loop each team
    for team in TEAMS_DICT:
        with open('misc/fantasy_stats/'+team+'.json', 'w') as outfile:
            logger.info('Writing to fantasy_stats file:' +team)
            json.dump(matchup_data[team], outfile)

    return matchup_data


pp = pprint.PrettyPrinter(indent=4)
teams_dict = get_active_teams()
get_team_schedule(teams_dict)
PLAYERS_DICT = get_current_roster(teams_dict)
get_player_log(PLAYERS_DICT)

get_depth_chart()
get_fantasy_news()
get_team_against_position()