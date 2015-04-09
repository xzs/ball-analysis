import pprint
import csv
import math
from datetime import datetime

YEAR = '2015'

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

WESTERN_CONF = {
    'DAL':'Dallas Mavericks',
    'DEN':'Denver Nuggets',
    'GSW':'Golden State Warriors',
    'HOU':'Houston Rockets',
    'LAC':'Los Angeles Clippers',
    'LAL':'Los Angeles Lakers',
    'MEM':'Memphis Grizzlies',
    'MIN':'Minnesota Timberwolves',
    'NOP':'New Orleans Pelicans',
    'OKC':'Oklahoma City Thunder',
    'PHO':'Phoenix Suns',
    'POR':'Portland Trail Blazers',
    'SAC':'Sacramento Kings',
    'SAS':'San Antonio Spurs',
    'UTA':'Utah Jazz'
}

EASTERN_CONF = {
    'ATL':'Atlanta Hawks',
    'BOS':'Boston Celtics',
    'BRK':'Brooklyn Nets',
    'CHO':'Charlotte Hornets',
    'CHI':'Chicago Bulls',
    'CLE':'Cleveland Cavaliers',
    'DET':'Detroit Pistons',
    'IND':'Indiana Pacers',
    'MIA':'Miami Heat',
    'MIL':'Milwaukee Bucks',
    'NYK':'New York Knicks',
    'ORL':'Orlando Magic',
    'PHI':'Philadelphia 76ers',
    'TOR':'Toronto Raptors',
    'WAS':'Washington Wizards'
}

def two_decimals(num):
    return float("{0:.2f}".format(num))

def read_team_schedule_csv():

    opponents_dict = {}
    opponents_dict['opp'] = {}
    opponents_dict['channel'] = {}
    
    with open('team_schedules/MIL.csv', 'rb') as f:
        schedule = csv.reader(f)
        for games in schedule:
            # Count up the number of times the opponent is supposed to be played this season
            if games[6] in opponents_dict['opp']:
                opponents_dict['opp'][games[6]] += 1
            else:
                opponents_dict['opp'][games[6]] = 1                    

            # Count the number of times the team played on national TV, and against who
            # If it's not played on a local TV channel
            if games[3]:
                if games[3] in opponents_dict['channel']:
                    opponents_dict['channel'][games[3]]['times_played'] += 1
                    # If the channel already exists but the opponent does not
                    if games[6] in opponents_dict['channel'][games[3]]['opponent']:
                        opponents_dict['channel'][games[3]]['opponent'][games[6]] += 1
                    else:
                        opponents_dict['channel'][games[3]]['opponent'][games[6]] = 1       
                else:
                    opponents_dict['channel'][games[3]] = {}
                    opponents_dict['channel'][games[3]]['times_played'] = 1
                    opponents_dict['channel'][games[3]]['opponent'] = {}
                    opponents_dict['channel'][games[3]]['opponent'][games[6]] = 1

    return opponents_dict


'''
GmSc
Game Score; the formula is 
PTS + 0.4 * FG - 0.7 * FGA - 0.4*(FTA - FT) + 0.7 * ORB + 0.3 * DRB + STL + 0.7 * AST + 0.7 * BLK - 0.4 * PF - TOV. 
Game Score was created by John Hollinger to give a rough measure of a player's productivity for a single game. 
The scale is similar to that of points scored, (40 is an outstanding performance, 10 is an average performance, etc.).

'''
def read_player_csv(schedule):
    with open('player_logs/Khris Middleton.csv', 'rb') as f:
        player_log = csv.reader(f)

        player_dict = {}
        player_dict['teams_against'] = {}
        player_dict['eastern_conf'] = {}
        east_gmsc = 0
        player_dict['eastern_conf']['games'] = 0
        player_dict['western_conf'] = {}
        west_gmsc = 0
        player_dict['western_conf']['games'] = 0
        away_games = 0
        home_games = 0
        away_gmsc = 0
        home_gmsc = 0
        home_playtime_seconds = 0
        away_playtime_seconds = 0

        # We want to be able to create a player dictionary that will contain the statistics for the GmSc.
        # The dictionary will also contain detailed information abou the teams the player has played agianst
        for record in player_log:
            # If he played
            if record[1]:
                if record[5]:
                    away_gmsc += float(record[28])
                    away_games += 1
                    home_playtime = record[9].split(':')
                    home_playtime_seconds += int(home_playtime[0])*60 + int(home_playtime[1])
                else:
                    home_gmsc += float(record[28])
                    home_games += 1
                    away_playtime = record[9].split(':')
                    away_playtime_seconds += int(away_playtime[0])*60 + int(away_playtime[1])

                if record[6] in player_dict['teams_against']:
                    player_dict['teams_against'][record[6]]['games'] += 1
                    player_dict['teams_against'][record[6]]['gmsc'] = two_decimals(float(player_dict['teams_against'][record[6]]['gmsc'] + float(record[28])) / player_dict['teams_against'][record[6]]['games'])
                else:
                    player_dict['teams_against'][record[6]] = {}
                    player_dict['teams_against'][record[6]]['games'] = 1
                    player_dict['teams_against'][record[6]]['gmsc'] = float(record[28])

                player_dict['teams_against'][record[6]]['games_remain'] = schedule['opp'][TEAMS_DICT[record[6]]] - player_dict['teams_against'][record[6]]['games']

                if record[6] in EASTERN_CONF:
                    player_dict['eastern_conf']['games'] += 1
                    east_gmsc += float(record[28])
                else:
                    player_dict['western_conf']['games'] += 1
                    west_gmsc += float(record[28])


        player_dict['home_playtime'] = two_decimals(float(home_playtime_seconds / away_games)/60)
        player_dict['away_playtime'] = two_decimals(float(away_playtime_seconds / home_games)/60)

        player_dict['average_away_gmsc'] = two_decimals(float(away_gmsc / away_games))
        player_dict['average_home_gmsc'] = two_decimals(float(home_gmsc / home_games))
        player_dict['average_gmsc'] = two_decimals(float((away_gmsc+home_gmsc)/(away_games+home_games)))

        player_dict['eastern_conf']['gmsc'] = two_decimals(float(east_gmsc / player_dict['eastern_conf']['games']))
        player_dict['western_conf']['gmsc'] = two_decimals(float(west_gmsc / player_dict['western_conf']['games']))

        player_dict['cov'] = calc_coefficient_of_variance(player_dict)

    return player_dict

def calc_coefficient_of_variance(player_dict):

    total = 0
    num_teams = len(player_dict['teams_against'])
    for team in player_dict['teams_against']:
        total += player_dict['teams_against'][team]['gmsc']
    
    # Calculate mean
    mean = float(total / num_teams)

    variance_sum = 0
    for team in player_dict['teams_against']:
        variance_sum += math.pow((player_dict['teams_against'][team]['gmsc'] - mean), 2)
    # Calculate the variance
    variance = variance_sum / num_teams
    # Standard deviation
    std_deviation = math.sqrt(variance)

    # Coefficent of variation
    return two_decimals(std_deviation / mean)


# This method will calculate the trend for last n number of games
def last_n_games(num_games):
    # We read the file backwards from the csv file
    # However, if the file does not fit in memory this method of using reverse will not work
    count = 0
    PLAYER_DICT['last_'+str(num_games)+'_games'] = {}
    threes = 0
    gmsc = 0
    pts = 0 
    reb = 0 
    ast = 0 
    stl = 0 
    blk = 0 
    tov = 0 
    with open('player_logs/Khris Middleton.csv', 'rb') as f:
        for record in reversed(list(csv.reader(f))):
            # If he played
            if record[1] and count != num_games:
                gmsc += float(record[27]) 
                pts += float(record[27])
                reb += float(record[21])
                ast += float(record[22])
                stl += float(record[23])
                blk += float(record[24])
                tov += float(record[25])
                threes += float(record[13])
                count +=1

    PLAYER_DICT['last_'+str(num_games)+'_games']['gmsc'] = gmsc / num_games
    PLAYER_DICT['last_'+str(num_games)+'_games']['pts'] = pts / num_games
    PLAYER_DICT['last_'+str(num_games)+'_games']['reb'] = reb / num_games 
    PLAYER_DICT['last_'+str(num_games)+'_games']['ast'] = ast / num_games
    PLAYER_DICT['last_'+str(num_games)+'_games']['stl'] = stl / num_games
    PLAYER_DICT['last_'+str(num_games)+'_games']['blk'] = blk / num_games
    PLAYER_DICT['last_'+str(num_games)+'_games']['tov'] = tov / num_games
    PLAYER_DICT['last_'+str(num_games)+'_games']['3pm'] = threes / num_games

pp = pprint.PrettyPrinter(indent=4)
SCHEDULE_DICT = read_team_schedule_csv()
PLAYER_DICT = read_player_csv(SCHEDULE_DICT)
last_n_games(5)
last_n_games(10)
pp.pprint(PLAYER_DICT)

