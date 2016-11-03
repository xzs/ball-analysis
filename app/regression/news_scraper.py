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

NEWS_URL = 'http://www.rotoworld.com/teams/nba/'

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
        # print game
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

# get_fantasy_news()