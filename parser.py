import pprint
import csv

YEAR = '2015'

TEAMS_DICT = {}

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
def read_player_csv():
    with open('player_logs/Khris Middleton.csv', 'rb') as f:
        player_log = csv.reader(f)

        player_dict = {}
        away_games = 0
        home_games = 0
        away_gmsc = 0
        home_gmsc = 0
        # We want to be able to create a player dictionary that will contain the statistics for the GmSc.
        # The dictionary will also contain detailed information abou the teams the player has played agianst
        for record in player_log:
            # If he played
            if record[1]:

                if record[5]:
                    away_gmsc += float(record[28])
                    away_games += 1
                else:
                    home_gmsc += float(record[28])
                    home_games += 1

                if record[6] in player_dict:
                    player_dict[record[6]]['games'] += 1
                    player_dict[record[6]]['gmsc'] = two_decimals(float(player_dict[record[6]]['gmsc'] + float(record[28])) / player_dict[record[6]]['games'])
                else:
                    player_dict[record[6]] = {}
                    player_dict[record[6]]['games'] = 1
                    player_dict[record[6]]['gmsc'] = float(record[28])


        player_dict['average_away_gmsc'] = two_decimals(float(away_gmsc / away_games))
        player_dict['average_home_gmsc'] = two_decimals(float(home_gmsc / home_games))
        player_dict['average_gmsc'] = two_decimals(float((away_gmsc+home_gmsc)/(away_games+home_games)))

    pp.pprint(player_dict)
    return player_dict

pp = pprint.PrettyPrinter(indent=4)
SCHEDULE_DICT = read_team_schedule_csv();
read_player_csv()


