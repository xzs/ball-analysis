import pprint
import csv
import math
import json
import glob
import sys
import logging
from datetime import datetime as dt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

YEAR = '2015'

ALL_STAR_DATE = '2015-02-22'

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
    return float('{0:.2f}'.format(num))

def read_team_schedule_csv(csv_f, team_name):

    logger.info('Parsing schedule for: '+team_name)

    SCHEDULE_DICT[team_name] = {}
    SCHEDULE_DICT[team_name]['opp'] = {}
    SCHEDULE_DICT[team_name]['channel'] = {}

    logger.info('Completed creation of schedule dictionary for: '+team_name)

    schedule = csv.reader(csv_f)
    for games in schedule:
        # Count up the number of times the opponent is supposed to be played this season
        if games[6] in SCHEDULE_DICT[team_name]['opp']:
            SCHEDULE_DICT[team_name]['opp'][games[6]] += 1
        else:
            SCHEDULE_DICT[team_name]['opp'][games[6]] = 1                    

        # Count the number of times the team played on national TV, and against who
        # If it's not played on a local TV channel
        if games[3]:
            if games[3] in SCHEDULE_DICT[team_name]['channel']:
                SCHEDULE_DICT[team_name]['channel'][games[3]]['times_played'] += 1
                # If the channel already exists but the opponent does not
                if games[6] in SCHEDULE_DICT[team_name]['channel'][games[3]]['opponent']:
                    SCHEDULE_DICT[team_name]['channel'][games[3]]['opponent'][games[6]] += 1
                else:
                    SCHEDULE_DICT[team_name]['channel'][games[3]]['opponent'][games[6]] = 1       
            else:
                SCHEDULE_DICT[team_name]['channel'][games[3]] = {}
                SCHEDULE_DICT[team_name]['channel'][games[3]]['times_played'] = 1
                SCHEDULE_DICT[team_name]['channel'][games[3]]['opponent'] = {}
                SCHEDULE_DICT[team_name]['channel'][games[3]]['opponent'][games[6]] = 1

        logger.info('Finished parsing schedule for: '+ team_name)
'''
GmSc
Game Score; the formula is 
points + 0.4 * FG - 0.7 * FGA - 0.4*(FTA - FT) + 0.7 * ORB + 0.3 * DRB + steals + 0.7 * assists + 0.7 * blocks - 0.4 * PF - turnovers. 
Game Score was created by John Hollinger to give a rough measure of a player's productivity for a single game. 
The scale is similar to that of points scored, (40 is an outstanding performance, 10 is an average performance, etc.).

'''
def read_player_csv(csv_f, schedule, player_name):
    logger.info('Reading player csv for: '+ player_name)

    player_log = csv.reader(csv_f)

    player_dict = {}
    player_dict['stats'] = {}
    player_dict['name'] = player_name
    
    player_dict['pre_all_star'] = {}
    player_dict['post_all_star'] = {}

    player_dict['teams_against'] = {}
    player_dict['eastern_conf'] = {}
    player_dict['eastern_conf']['games'] = 0
    player_dict['western_conf'] = {}
    player_dict['western_conf']['games'] = 0

    points_list = []
    assists_list = []
    rebounds_list = []

    points = 0
    rebounds = 0
    assists = 0
    steals = 0
    blocks = 0
    turnovers = 0
    threes = 0

    east_gmsc = 0
    west_gmsc = 0

    away_games = 0
    home_games = 0
    away_gmsc = 0
    home_gmsc = 0
    home_playtime_seconds = 0
    away_playtime_seconds = 0

    pre_all_star_games = 0
    post_all_star_games = 0

    # We want to be able to create a player dictionary that will contain the statistics for the GmSc.
    # The dictionary will also contain detailed information abou the teams the player has played agianst
    for record in player_log:
        player_dict['age'] = record[3].split('-')[0]
        team = record[4]
        player_dict['team'] = team
        # If he played
        if record[1]:
            if record[5]:
                logger.info('Compling away games')
                away_gmsc += float(record[28])
                away_games += 1
                home_playtime = record[9].split(':')
                if len(home_playtime) > 1:
                    home_playtime_seconds += int(home_playtime[0])*60 + int(home_playtime[1])
                else:
                    home_playtime_seconds = 0
            else:
                logger.info('Compling home games')
                home_gmsc += float(record[28])
                home_games += 1
                away_playtime = record[9].split(':')
                if len(away_playtime) > 1:
                    away_playtime_seconds += int(away_playtime[0])*60 + int(away_playtime[1])
                else:
                    away_playtime_seconds = 0

            logger.info('Beging game statistics')
            new_stats_dict(player_dict['teams_against'], record[6], record)
                
            # player_dict['teams_against'][record[6]]['games_remain'] = schedule[team]['opp'][TEAMS_DICT[record[6]]] - player_dict['teams_against'][record[6]]['games']

            points_list.append(float(record[27]))
            assists_list.append(float(record[22]))
            rebounds_list.append(float(record[21]))

            logger.info('Compling conference play')
            if record[6] in EASTERN_CONF:
                player_dict['eastern_conf']['games'] += 1
                east_gmsc += float(record[28])
            else:
                player_dict['western_conf']['games'] += 1
                west_gmsc += float(record[28])
            
            # points = two_decimals(float(points + float(record[27])))
            points += float(record[27])
            rebounds += float(record[21])
            assists += float(record[22])
            steals += float(record[23])
            blocks += float(record[24])
            turnovers += float(record[25])
            threes += float(record[13])

            # If any games the player played before the ALL_STAR_BREAK
            all_star = dt.strptime(ALL_STAR_DATE, "%Y-%m-%d")
            game_date = dt.strptime(record[2], "%Y-%m-%d")

            # If the game is played pre all star break
            if all_star < game_date:
                pre_all_star_games += 1
                new_stats_dict(player_dict, 'pre_all_star', record)
            else:
                post_all_star_games += 1
                new_stats_dict(player_dict, 'post_all_star', record)

    #  For now we only consider players who have played both a home and away game
    if home_games > 0 and away_games > 0:
        logger.info('First level dictionary values processing')
        player_dict['home_playtime'] = two_decimals(float(home_playtime_seconds / away_games)/60)
        player_dict['away_playtime'] = two_decimals(float(away_playtime_seconds / home_games)/60)

        player_dict['average_away_gmsc'] = two_decimals(float(away_gmsc / away_games))
        player_dict['average_home_gmsc'] = two_decimals(float(home_gmsc / home_games))
        player_dict['average_gmsc'] = two_decimals(float((away_gmsc + home_gmsc)/(away_games + home_games)))

        if player_dict['eastern_conf']['games'] != 0:
            player_dict['eastern_conf']['gmsc'] = two_decimals(float(east_gmsc / player_dict['eastern_conf']['games']))
        else:
            player_dict['eastern_conf']['gmsc'] = 0

        if player_dict['western_conf']['games'] != 0:
            player_dict['western_conf']['gmsc'] = two_decimals(float(west_gmsc / player_dict['western_conf']['games']))
        else:
            player_dict['western_conf']['gmsc'] = 0

        player_dict['stats']['points'] = two_decimals(float(points / (away_games + home_games)))
        player_dict['stats']['rebounds'] = two_decimals(float(rebounds / (away_games + home_games)))
        player_dict['stats']['assists'] = two_decimals(float(assists / (away_games + home_games)))
        player_dict['stats']['steals'] = two_decimals(float(steals / (away_games + home_games)))
        player_dict['stats']['blocks'] = two_decimals(float(blocks / (away_games + home_games)))
        player_dict['stats']['turnovers'] = two_decimals(float(turnovers / (away_games + home_games)))
        player_dict['stats']['3pm'] = two_decimals(float(threes / (away_games + home_games)))
        pp.pprint(player_dict)

        player_dict['cov'] = calc_coefficient_of_variance(player_dict)
        
        player_dict['best_stretch'] = {}
        player_dict['best_stretch']['points'] = consecutive_sum(points_list, 5)
        player_dict['best_stretch']['assists'] = consecutive_sum(assists_list, 5)
        player_dict['best_stretch']['rebounds'] = consecutive_sum(rebounds_list, 5)
    return player_dict


def new_stats_dict(player_dict, layer, record):

    if layer in player_dict:
        if 'stats' in player_dict[layer]:
            player_dict[layer]['stats']['games'] += 1

            player_dict[layer]['stats']['gmsc'] = float(player_dict[layer]['stats']['gmsc'] + float(record[28]))
            player_dict[layer]['stats']['points'] = float(player_dict[layer]['stats']['points'] + float(record[27]))
            player_dict[layer]['stats']['rebounds'] = float(player_dict[layer]['stats']['rebounds'] + float(record[21]))
            player_dict[layer]['stats']['assists'] = float(player_dict[layer]['stats']['assists'] + float(record[22]))
            player_dict[layer]['stats']['steals'] = float(player_dict[layer]['stats']['steals'] + float(record[23]))
            player_dict[layer]['stats']['blocks'] = float(player_dict[layer]['stats']['blocks'] + float(record[24]))
            player_dict[layer]['stats']['turnovers'] = float(player_dict[layer]['stats']['turnovers'] + float(record[25]))
            player_dict[layer]['stats']['3pm'] = float(player_dict[layer]['stats']['3pm'] + float(record[13]))
        else:
            player_dict[layer]['stats'] = {}
            player_dict[layer]['stats']['games'] = 1
            player_dict[layer]['stats']['gmsc'] = float(record[28])
            player_dict[layer]['stats']['points'] = float(record[27])
            player_dict[layer]['stats']['rebounds'] = float(record[21])
            player_dict[layer]['stats']['assists'] = float(record[22])
            player_dict[layer]['stats']['steals'] = float(record[23])
            player_dict[layer]['stats']['blocks'] = float(record[24])
            player_dict[layer]['stats']['turnovers'] = float(record[25])
            player_dict[layer]['stats']['3pm'] = float(record[13])
    else:
        player_dict[layer] = {}
        player_dict[layer]['stats'] = {}
        player_dict[layer]['stats']['games'] = 1
        player_dict[layer]['stats']['gmsc'] = float(record[28])
        player_dict[layer]['stats']['points'] = float(record[27])
        player_dict[layer]['stats']['rebounds'] = float(record[21])
        player_dict[layer]['stats']['assists'] = float(record[22])
        player_dict[layer]['stats']['steals'] = float(record[23])
        player_dict[layer]['stats']['blocks'] = float(record[24])
        player_dict[layer]['stats']['turnovers'] = float(record[25])
        player_dict[layer]['stats']['3pm'] = float(record[13])

    return player_dict

# One way to do this is to use Kande's algorithm which
# compares the max's of each array this will run in O(n) tim
'''
The other way consists of using a nested loop, although it is a o(n^2) solution
    for (var i=0; i<list.length; i++){
        sum = 0;
        for (var j=i; j<consec+i; j++){
            sum += list[j]
        }
        if (max < sum){
            max = sum
        }
    }
'''
'''
The other thing is that I want the largest consecutive sum given a period 
[1,4,2,4,5,7]
if n = 3, then the largest sum in this case would be (4+5+7) = 16
'''
def consecutive_sum(stats_list, n):
    logger.info('Process consecutive sum')
    max_sum = 0
    max_hash = 0
    #  we use enumerate to access the index
    for index, value in enumerate(stats_list):
        current_sum = 0
        temp_hash = {}
        for inx in range(index, n+index):
            try:
                # calculate the sums and append them to the list
                current_sum += stats_list[inx]
                temp_hash[inx+1] = stats_list[inx]
            except IndexError:
                current_sum = 0
        # If those sums are max then put the temp_list into a good_list
        if max_sum < current_sum:
            max_sum = current_sum
            max_hash = temp_hash

    return max_hash


def calc_coefficient_of_variance(player_dict):
    logger.info('COV processing')
    total = 0
    num_teams = len(player_dict['teams_against'])
    for team in player_dict['teams_against']:
        total += player_dict['teams_against'][team]['stats']['gmsc']
    
    # Calculate mean
    mean = float(total / num_teams)

    variance_sum = 0
    for team in player_dict['teams_against']:
        variance_sum += math.pow((player_dict['teams_against'][team]['stats']['gmsc'] - mean), 2)
    # Calculate the variance
    variance = variance_sum / num_teams
    # Standard deviation
    std_deviation = math.sqrt(variance)

    # Coefficent of variation
    return two_decimals(std_deviation / mean)


# This method will calculate the trend for last n number of games
def last_n_games(csv_f, num_games):
    # We read the file backwards from the csv file
    # However, if the file does not fit in memory this method of using reverse will not work
    logger.info('Best stretch processing')
    count = 0
    PLAYER_DICT['last_'+str(num_games)+'_games'] = {}
    threes = 0
    gmsc = 0
    points = 0 
    rebounds = 0 
    assists = 0 
    steals = 0 
    blocks = 0 
    turnovers = 0

    for record in reversed(list(csv.reader(csv_f))):
        # If he played
        if record[1] and count != num_games:
            gmsc += float(record[27]) 
            points += float(record[27])
            rebounds += float(record[21])
            assists += float(record[22])
            steals += float(record[23])
            blocks += float(record[24])
            turnovers += float(record[25])
            threes += float(record[13])
            count +=1

    PLAYER_DICT['last_'+str(num_games)+'_games']['gmsc'] = gmsc / num_games
    PLAYER_DICT['last_'+str(num_games)+'_games']['points'] = points / num_games
    PLAYER_DICT['last_'+str(num_games)+'_games']['rebounds'] = rebounds / num_games 
    PLAYER_DICT['last_'+str(num_games)+'_games']['assists'] = assists / num_games
    PLAYER_DICT['last_'+str(num_games)+'_games']['steals'] = steals / num_games
    PLAYER_DICT['last_'+str(num_games)+'_games']['blocks'] = blocks / num_games
    PLAYER_DICT['last_'+str(num_games)+'_games']['turnovers'] = turnovers / num_games
    PLAYER_DICT['last_'+str(num_games)+'_games']['3pm'] = threes / num_games

pp = pprint.PrettyPrinter(indent=4)

# I need to calculate pre and post all star

# Open all team schedules for processing
# SCHEDULE_DICT = {}
# for files in glob.glob("team_schedules/*.csv"):
#     team_name = files.split('/')[1].split('.c')[0]
#     logger.info('Parsing schedule for: '+team_name)

#     # this will need to be looped
#     with open(files, 'rb') as f:
#         try:
#             read_team_schedule_csv(f, team_name)

#         except csv.Error as e:
#             sys.exit('file %s: %s' % (files, e))

# # Open all player files for data parsing
# for files in glob.glob("player_logs/*.csv"):
#     player_name = files.split('/')[1].split('.c')[0]
#     # this will need to be looped
#     logger.info('Parsing stats for: '+player_name)

#     with open(files, 'rb') as f:
#         try:
#             PLAYER_DICT = read_player_csv(f, SCHEDULE_DICT, player_name)
#             # Since we need to go through the files again we seek to the beginning of the file
#             f.seek(0)
#             last_n_games(f, 5)
#             f.seek(0)
#             last_n_games(f, 10)
#             # Dump the json file
#             logger.info('Dumping json for: '+player_name)
#             with open('json_files/'+player_name+'.txt', 'w') as outfile:
#                 json.dump(PLAYER_DICT, outfile)

#         except csv.Error as e:
#             sys.exit('file %s: %s' % (files, e))

with open('team_schedules/MIL.csv', 'rb') as f:
    SCHEDULE_DICT = {}
    read_team_schedule_csv(f, 'MIL')

with open('player_logs/Khris Middleton.csv', 'rb') as f:
    PLAYER_DICT = read_player_csv(f, SCHEDULE_DICT, 'Khris Middleton')
