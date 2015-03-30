import pprint
import csv

YEAR = '2015'

TEAMS_DICT = {}

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

        pp.pprint(opponents_dict)

pp = pprint.PrettyPrinter(indent=4)
read_team_schedule_csv();


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
