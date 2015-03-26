import urllib2
import pprint
from bs4 import BeautifulSoup

BASE_URL = 'http://www.basketball-reference.com'
YEAR = '2015'
TEAMS_DICT = {}
TEAMS_URL = {}

def get_active_teams():
    url = urllib2.urlopen(BASE_URL+'/teams/')
    soup = BeautifulSoup(url)

    table = soup.find('table', attrs={'id':'active'})
    table_body = table.find('tbody')
    rows = table_body.find_all('tr', attrs={'class':'full_table'})

    for row in rows:
        cols = row.find_all('a')
        for link in cols:
            team_link = link.get('href') + YEAR + '.html'
            team = team_link.split('/')[2]
            TEAMS_DICT[team] = str(link.text) # Cast unicode to string
            TEAMS_URL[team] = team_link

def get_current_roster(teams_dict):

    # for team in teams_dict:
    #     url = urllib2.urlopen(BASE_URL+teams_dict[team])
    #     soup = BeautifulSoup(url)

    #     table = soup.find('table', attrs={'id':'roster'})
    #     print table
        # table_body = table.find('tbody')
        # rows = table_body.find_all('tr')

        # print rows
    # for some reason this is not getting the actual team page
    url = urllib2.urlopen('http://www.basketball-reference.com/teams/MIL/2015.html')
    # we have to use the html5lib parser, as some elements were not showing up fully
    soup = BeautifulSoup(url, 'html5lib')

    # table = soup.find('div', attrs={'id': 'all_roster'})
    print soup

pp = pprint.PrettyPrinter(indent=4)
get_active_teams()
get_current_roster(TEAMS_URL)
# pp.pprint(TEAMS_URL)
# pp.pprint(TEAMS_DICT)