import urllib2
import pprint
import logging
import json
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

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

    today_news = soup.find('div', attrs={'class': 'daily-status-updates'})

    player_status = today_news.find_all('div', attrs={'class': 'daily-status-player'})
    daily_status_player = {}
    for player in player_status:
        player_status = player.find_all('a')
        try:
            status = player_status[0].text.split('-')[0].strip()
            player_name = player_status[1].text
            daily_status_player[player_name] = status
        except IndexError:
            LOGGER.debug('No news')
    return daily_status_player


def construct_api_url(team, on_players, off_players, start_date, end_date):
    base_url = 'http://nbawowy-52108.onmodulus.net/api/'

    vs_teams = '[76ers,Bobcats,Bucks,Bulls,Cavaliers,Celtics,Clippers,'\
                'Grizzlies,Hawks,Heat,Hornets,Jazz,Kings,Knicks,Lakers,'\
                'Magic,Mavericks,Nets,Nuggets,Pacers,Pelicans,Pistons,'\
                'Raptors,Rockets,Spurs,Suns,Thunder,Timberwolves,'\
                'Trail Blazers,Warriors,Wizards]'

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

def player_on_off(team, on_players, off_players, start_date, end_date):

    url_list = construct_api_url(team, on_players, off_players, start_date, end_date)

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
                    'time': player['time'] / 60
                }

        if stat['stat'] == 'lineups':
            for lineup in data:
                player_obj['lineups'].append({
                    'lineup': lineup['_id']['name'],
                    'poss': lineup['poss'],
                    'time': lineup['time'] / 60
                })

        if stat['stat'] == 'tov' or stat['stat'] == 'fga' or stat['stat'] == 'reb':
            process_stat_api(player_obj, data, stat['stat'])

    print player_obj

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

    for (player, fga) in temp_obj.iteritems():
        if player in player_obj['players']:
            player_obj['players'][player][stat] = fga
        else:
            player_obj['players'][player][stat] = 0

    return player_obj


player_on_off('Cavaliers', ['Iman Shumpert', 'LeBron James'], [], '2015-10-01', '2016-11-03')

# player_on_off('Nuggets', ['Jameer Nelson'], False, '2015-10-01', '2016-11-03')
# get_fantasy_news()
# get_team_against_position()