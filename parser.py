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

# G   Date                    opponent            Tm  Opp W   L   Streak  Note
# 0Game Number
# 1Date
# 2Time,
# 3Channel,
# 4Box Score,
# 5Home or Away,
# 6Opponent
# 7Result,
# 8OT
# 9Team Score
# 10Opponent Score
# 11Wins
# 12Loss
# 13Streak
# 14Note
# ['60', 'Sun, Mar 1, 2015', '1:00p EST', 'ABC', 'Box Score', '', 'Los Angeles Clippers', 'L', '', '86', '96', '37', '23', 'L 1', '']

def read_team_schedule_csv():

    opponents_dict = {}
    opponents_dict['opp'] = {}
    opponents_dict['channel'] = {}
    
    with open('team_schedules/CHI.csv', 'rb') as f:
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

def two_decimals(num):
    return float("{0:.2f}".format(num))
# 1,1,2014-10-29,23-078,MIL,@,CHO,L (-2),1,35:56,7,15,.467,0,2,.000,3,5,.600,1,5,6,2,0,1,4,2,17,8.0,-5
'''
0Rk
1Game played
2Date
3Age
4team
5Away
6opponent
7Result
8Game started
9Minutes played
10FGM
11FGA
12FG%
133PM
143PA
153P%
16FTM
17FTA
18FT%
19ORD
20DRB
21TRB
22AST
23STL
24BLK
25TOV
26PF
27PTS
28GmSc
29+/-
'''

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

        # pp.pprint(schedule)

        player_dict = {}
        player_dict['teams_against'] = {}
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


        player_dict['home_playtime'] = two_decimals(float(home_playtime_seconds / away_games)/60)
        player_dict['away_playtime'] = two_decimals(float(away_playtime_seconds / home_games)/60)

        player_dict['average_away_gmsc'] = two_decimals(float(away_gmsc / away_games))
        player_dict['average_home_gmsc'] = two_decimals(float(home_gmsc / home_games))
        player_dict['average_gmsc'] = two_decimals(float((away_gmsc+home_gmsc)/(away_games+home_games)))

        # calc_weighted_average(schedule, player_dict)
        player_dict['cov'] = calc_coefficient_of_variance(player_dict)

    pp.pprint(player_dict)
    return player_dict

def calc_weighted_average(schedule, player_dict):

    opponents = schedule['opp']
    for team in player_dict['teams_against']:
        if TEAMS_DICT[team] in opponents:
            print opponents[TEAMS_DICT[team]]


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

pp = pprint.PrettyPrinter(indent=4)
SCHEDULE_DICT = read_team_schedule_csv()
read_player_csv(SCHEDULE_DICT)


