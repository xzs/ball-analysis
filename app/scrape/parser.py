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

YEAR = '2016'

ALL_STAR_DATE = '2016-02-13'

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
'''
    Point = +1 PT
    Made 3pt. shot = +0.5 PTs
    Rebound = +1.25 PTs
    Assist = +1.5 PTs
    Steal = +2 PTs
    Block = +2 PTs
    Turnover = -0.5 PTs
    Double-Double = +1.5PTs (MAX 1 PER PLAYER: Points, Rebounds, Assists, Blocks, Steals)
    Triple-Double = +3PTs (MAX 1 PER PLAYER: Points, Rebounds, Assists, Blocks, Steals)
'''
DK_SCORING = {
    'points': 1,
    'threes': 0.5,
    'rebounds': 1.25,
    'assists': 1.25,
    'steals': 2,
    'blocks': 2,
    'turnovers': -0.5
}

def two_decimals(num):
    return float('{0:.2f}'.format(num))

def read_team_schedule_csv(csv_f, team_name):

    logger.info('Parsing schedule for: '+team_name)

    SCHEDULE_DICT[team_name] = {}
    SCHEDULE_DICT[team_name]['opp'] = {}
    SCHEDULE_DICT[team_name]['by_date'] = {}
    SCHEDULE_DICT[team_name]['channel'] = {}

    logger.info('Completed creation of schedule dictionary for: '+team_name)
    schedule = csv.reader(csv_f)
    for game in schedule:
        date = game[1]
        opp = game[6]
        time = game[2]
        if game[5] == '@':
            location = 'Away'
        else:
            location = 'Home'
        # Count up the number of times the opponent is supposed to be played this season
        if game[1] not in SCHEDULE_DICT[team_name]['by_date']:
            SCHEDULE_DICT[team_name]['by_date'][date] = {
                'opp': REVERSE_TEAMS_DICT[opp],
                'time': time,
                'location': location
            }
        # create the dict for the league schedule
        # I need to remove duplicates
        if date not in SCHEDULE_DICT['league_schedule']:
            SCHEDULE_DICT['league_schedule'][date] = []
            SCHEDULE_DICT['league_schedule'][date].append({
                'team': team_name,
                'opp': REVERSE_TEAMS_DICT[opp],
                'location': location,
                'time': time
            })
        else:
            # loop through to check if the game was already registered
            if not any(game['opp'] == team_name for game in SCHEDULE_DICT['league_schedule'][date]):
                SCHEDULE_DICT['league_schedule'][date].append({
                    'team': team_name,
                    'opp': REVERSE_TEAMS_DICT[opp],
                    'location': location,
                    'time': time
                })


        # count the times the opp have been played
        if opp in SCHEDULE_DICT[team_name]['opp']:
            SCHEDULE_DICT[team_name]['opp'][opp] += 1
        else:
            SCHEDULE_DICT[team_name]['opp'][opp] = 1

        # Count the number of times the team played on national TV, and against who
        # If it's not played on a local TV channel
        if game[3]:
            if game[3] in SCHEDULE_DICT[team_name]['channel']:
                SCHEDULE_DICT[team_name]['channel'][game[3]]['times_played'] += 1
                # If the channel already exists but the opponent does not
                if opp in SCHEDULE_DICT[team_name]['channel'][game[3]]['opponent']:
                    SCHEDULE_DICT[team_name]['channel'][game[3]]['opponent'][opp] += 1
                else:
                    SCHEDULE_DICT[team_name]['channel'][game[3]]['opponent'][opp] = 1
            else:
                SCHEDULE_DICT[team_name]['channel'][game[3]] = {}
                SCHEDULE_DICT[team_name]['channel'][game[3]]['times_played'] = 1
                SCHEDULE_DICT[team_name]['channel'][game[3]]['opponent'] = {}
                SCHEDULE_DICT[team_name]['channel'][game[3]]['opponent'][opp] = 1

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
    player_dict['as_starter'] = {}
    player_dict['non_starter'] = {}
    player_dict['basic_info'] = {}
    player_dict['basic_info']['name'] = player_name

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

    started_points = 0
    started_rebounds = 0
    started_assists = 0
    started_steals = 0
    started_blocks = 0
    started_turnovers = 0
    started_threes = 0

    non_started_points = 0
    non_started_rebounds = 0
    non_started_assists = 0
    non_started_steals = 0
    non_started_blocks = 0
    non_started_turnovers = 0
    non_started_threes = 0

    east_gmsc = 0
    west_gmsc = 0

    away_games = 0
    home_games = 0

    away_gmsc = 0
    home_gmsc = 0

    play_time_seconds = 0
    home_playtime_seconds = 0
    away_playtime_seconds = 0

    pre_all_star_games = 0
    post_all_star_games = 0

    #
    started_games = 0
    non_started_games = 0

    started_gmsc = 0
    non_started_gmsc = 0

    started_playtime_seconds = 0
    non_started_playtime_seconds = 0


    # We want to be able to create a player dictionary that will contain the statistics for the GmSc.
    # The dictionary will also contain detailed information abou the teams the player has played agianst
    for record in player_log:
        player_dict['basic_info']['age'] = record[3].split('-')[0]
        team = record[4]
        player_dict['basic_info']['team'] = team
        # If he played
        if record[1]:

            if record[5]:
                logger.info('Compling away games')
                away_gmsc += float(record[28])
                away_games += 1
                away_playtime_seconds = process_playtime(away_playtime_seconds, record[9])
            else:
                logger.info('Compling home games')
                home_gmsc += float(record[28])
                home_games += 1
                home_playtime_seconds = process_playtime(home_playtime_seconds, record[9])

            # for games the player started
            if record[8] == '1':
                logger.info('Compling home games')
                started_gmsc += float(record[28])
                started_games += 1
                started_playtime_seconds = process_playtime(started_playtime_seconds, record[9])
            else:
                logger.info('Compling home games')
                non_started_gmsc += float(record[28])
                non_started_games += 1
                non_started_playtime_seconds = process_playtime(non_started_playtime_seconds, record[9])

            # calculate the playtime for the player
            play_time_seconds = process_playtime(play_time_seconds, record[9])

            logger.info('Begining game statistics')
            # Create new layers for statistics against every team
            new_stats_dict(player_dict['teams_against'], record[6], record)

            # Calculate the remaining games for each opponent
            player_dict['teams_against'][record[6]]['stats']['games_remain'] = schedule[team]['opp'][TEAMS_DICT[record[6]]] - player_dict['teams_against'][record[6]]['stats']['games']

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


            if record[8] == '1':
                started_points += float(record[27])
                started_rebounds += float(record[21])
                started_assists += float(record[22])
                started_steals += float(record[23])
                started_blocks += float(record[24])
                started_turnovers += float(record[25])
                started_threes += float(record[13])
            else:
                non_started_points += float(record[27])
                non_started_rebounds += float(record[21])
                non_started_assists += float(record[22])
                non_started_steals += float(record[23])
                non_started_blocks += float(record[24])
                non_started_turnovers += float(record[25])
                non_started_threes += float(record[13])

            points += float(record[27])
            rebounds += float(record[21])
            assists += float(record[22])
            steals += float(record[23])
            blocks += float(record[24])
            turnovers += float(record[25])
            threes += float(record[13])

            # If any games the player played before the ALL_STAR_BREAK
            all_star = dt.strptime(ALL_STAR_DATE, '%Y-%m-%d')
            game_date = dt.strptime(record[2], '%Y-%m-%d')

            # If the game is played pre all star break
            if all_star > game_date:
                pre_all_star_games += 1
                # Create statistic layers for pre all star games
                new_stats_dict(player_dict, 'pre_all_star', record)
            else:
                post_all_star_games += 1
                # Create statistic layers for post all star games
                new_stats_dict(player_dict, 'post_all_star', record)

    #  For now we only consider players who have played both a home and away game
    if home_games > 0 or away_games > 0:
        logger.info('First level dictionary values processing')
        # value_when_true if condition else value_when_false
        if home_games > 0:
            player_dict['home_playtime'] = two_decimals(float(home_playtime_seconds / home_games)/60)
            player_dict['average_home_gmsc'] = two_decimals(float(home_gmsc / home_games))
        else:
            player_dict['home_playtime'] = 0
            player_dict['average_home_gmsc'] = 0

        if away_games > 0:
            player_dict['away_playtime'] = two_decimals(float(away_playtime_seconds / away_games)/60)
            player_dict['average_away_gmsc'] = two_decimals(float(away_gmsc / away_games))
        else:
            player_dict['away_playtime'] = 0
            player_dict['average_away_gmsc'] = 0

        if started_games > 0:
            player_dict['started_playtime'] = two_decimals(float(started_playtime_seconds / started_games)/60)
            player_dict['average_started_gmsc'] = two_decimals(float(started_gmsc / started_games))
        else:
            player_dict['started_playtime'] = 0
            player_dict['average_started_gmsc'] = 0

        if non_started_games > 0:
            player_dict['non_started_playtime'] = two_decimals(float(non_started_playtime_seconds / non_started_games)/60)
            player_dict['average_non_started_gmsc'] = two_decimals(float(non_started_gmsc / non_started_games))
        else:
            player_dict['non_started_playtime'] = 0
            player_dict['average_non_started_gmsc'] = 0

        player_dict['stats']['playtime'] = two_decimals(float(play_time_seconds / (away_games + home_games))/60)

        player_dict['as_starter']['playtime'] = player_dict['started_playtime']
        player_dict['non_starter']['playtime'] = player_dict['non_started_playtime']

        if player_dict['eastern_conf']['games'] != 0:
            player_dict['eastern_conf']['gmsc'] = two_decimals(float(east_gmsc / player_dict['eastern_conf']['games']))
        else:
            player_dict['eastern_conf']['gmsc'] = 0

        if player_dict['western_conf']['games'] != 0:
            player_dict['western_conf']['gmsc'] = two_decimals(float(west_gmsc / player_dict['western_conf']['games']))
        else:
            player_dict['western_conf']['gmsc'] = 0


        if started_games > 0:
            player_dict['as_starter']['points'] = two_decimals(float(started_points / started_games))
            player_dict['as_starter']['rebounds'] = two_decimals(float(started_rebounds / started_games))
            player_dict['as_starter']['assists'] = two_decimals(float(started_assists / started_games))
            player_dict['as_starter']['steals'] = two_decimals(float(started_steals / started_games))
            player_dict['as_starter']['blocks'] = two_decimals(float(started_blocks / started_games))
            player_dict['as_starter']['turnovers'] = two_decimals(float(started_turnovers / started_games))
            player_dict['as_starter']['threes'] = two_decimals(float(started_threes / started_games))
            # avg gmscr
            player_dict['as_starter']['gmsc'] = two_decimals(float(player_dict['average_started_gmsc']/started_games))
            player_dict['as_starter']['dk_points'] = calc_dk_points(player_dict['as_starter'])

        if non_started_games > 0:
            player_dict['non_starter']['points'] = two_decimals(float(non_started_points / non_started_games))
            player_dict['non_starter']['rebounds'] = two_decimals(float(non_started_rebounds / non_started_games))
            player_dict['non_starter']['assists'] = two_decimals(float(non_started_assists / non_started_games))
            player_dict['non_starter']['steals'] = two_decimals(float(non_started_steals / non_started_games))
            player_dict['non_starter']['blocks'] = two_decimals(float(non_started_blocks / non_started_games))
            player_dict['non_starter']['turnovers'] = two_decimals(float(non_started_turnovers / non_started_games))
            player_dict['non_starter']['threes'] = two_decimals(float(non_started_threes / non_started_games))
            # avg gmscr
            player_dict['non_starter']['gmsc'] = two_decimals(float(player_dict['average_non_started_gmsc']/non_started_games))
            player_dict['non_starter']['dk_points'] = calc_dk_points(player_dict['non_starter'])


        player_dict['stats']['points'] = two_decimals(float(points / (away_games + home_games)))
        player_dict['stats']['rebounds'] = two_decimals(float(rebounds / (away_games + home_games)))
        player_dict['stats']['assists'] = two_decimals(float(assists / (away_games + home_games)))
        player_dict['stats']['steals'] = two_decimals(float(steals / (away_games + home_games)))
        player_dict['stats']['blocks'] = two_decimals(float(blocks / (away_games + home_games)))
        player_dict['stats']['turnovers'] = two_decimals(float(turnovers / (away_games + home_games)))
        player_dict['stats']['threes'] = two_decimals(float(threes / (away_games + home_games)))
        # avg gmscr
        player_dict['stats']['gmsc'] = two_decimals(float((away_gmsc + home_gmsc)/(away_games + home_games)))
        player_dict['stats']['dk_points'] = calc_dk_points(player_dict['stats'])

        player_dict['cov'] = calc_coefficient_of_variance(player_dict)

        player_dict['best_stretch'] = {}
        player_dict['best_stretch']['points'] = consecutive_sum(points_list, 5)
        player_dict['best_stretch']['assists'] = consecutive_sum(assists_list, 5)
        player_dict['best_stretch']['rebounds'] = consecutive_sum(rebounds_list, 5)

        # Process the stats for pre and post all star
        average_stats(player_dict['pre_all_star'])
        average_stats(player_dict['post_all_star'])
        # Process the stats for each team
        average_stats(player_dict['teams_against'])

    return player_dict


def process_playtime(playtime_seconds, record):
    playtime = record.split(':')
    if len(playtime) > 1:
        playtime_seconds += int(playtime[0])*60 + int(playtime[1])
    else:
        playtime_seconds = 0

    return playtime_seconds

# Create a temp obj with the player's basic information
def categorize_players_by_teams(player, players_obj):
    # I need to store the names in a json file as a list of objects
    team = player['basic_info']['team']
    temp_player_obj = {}
    temp_player_obj['name'] = player['basic_info']['name']
    temp_player_obj['team'] = team
    temp_player_obj['age'] = player['basic_info']['age']
    if team in players_obj:
        # add player to
        players_obj[team].append(temp_player_obj)
    else:
        players_obj[team] = []
        players_obj[team].append(temp_player_obj)


# Process the stats dictionary
def new_stats_dict(player_dict, layer, record):

    if layer in player_dict:
        if 'stats' in player_dict[layer]:
            player_dict[layer]['stats']['games'] += 1
            player_dict[layer]['stats']['playtime'] = process_playtime(player_dict[layer]['stats']['playtime'], record[9])
            player_dict[layer]['stats']['gmsc'] = float(player_dict[layer]['stats']['gmsc'] + float(record[28]))
            player_dict[layer]['stats']['points'] = float(player_dict[layer]['stats']['points'] + float(record[27]))
            player_dict[layer]['stats']['rebounds'] = float(player_dict[layer]['stats']['rebounds'] + float(record[21]))
            player_dict[layer]['stats']['assists'] = float(player_dict[layer]['stats']['assists'] + float(record[22]))
            player_dict[layer]['stats']['steals'] = float(player_dict[layer]['stats']['steals'] + float(record[23]))
            player_dict[layer]['stats']['blocks'] = float(player_dict[layer]['stats']['blocks'] + float(record[24]))
            player_dict[layer]['stats']['turnovers'] = float(player_dict[layer]['stats']['turnovers'] + float(record[25]))
            player_dict[layer]['stats']['threes'] = float(player_dict[layer]['stats']['threes'] + float(record[13]))
        else:
            player_dict[layer]['stats'] = {}
            if layer != 'pre_all_star' and layer != 'post_all_star':
                player_dict[layer]['team_against'] = layer
            player_dict[layer]['stats']['games'] = 1
            player_dict[layer]['stats']['playtime'] = process_playtime(0, record[9])
            player_dict[layer]['stats']['gmsc'] = float(record[28])
            player_dict[layer]['stats']['points'] = float(record[27])
            player_dict[layer]['stats']['rebounds'] = float(record[21])
            player_dict[layer]['stats']['assists'] = float(record[22])
            player_dict[layer]['stats']['steals'] = float(record[23])
            player_dict[layer]['stats']['blocks'] = float(record[24])
            player_dict[layer]['stats']['turnovers'] = float(record[25])
            player_dict[layer]['stats']['threes'] = float(record[13])
    else:
        player_dict[layer] = {}
        player_dict[layer]['stats'] = {}
        if layer != 'pre_all_star' and layer != 'post_all_star':
            player_dict[layer]['team_against'] = layer
        player_dict[layer]['stats']['games'] = 1
        player_dict[layer]['stats']['playtime'] = process_playtime(0, record[9])
        player_dict[layer]['stats']['gmsc'] = float(record[28])
        player_dict[layer]['stats']['points'] = float(record[27])
        player_dict[layer]['stats']['rebounds'] = float(record[21])
        player_dict[layer]['stats']['assists'] = float(record[22])
        player_dict[layer]['stats']['steals'] = float(record[23])
        player_dict[layer]['stats']['blocks'] = float(record[24])
        player_dict[layer]['stats']['turnovers'] = float(record[25])
        player_dict[layer]['stats']['threes'] = float(record[13])

    player_dict[layer]['stats']['dk_points'] = calc_dk_points(player_dict[layer]['stats'])
    return player_dict


# Calculate the average stats for the stats dictionary
def average_stats(player_dict):

    # If 'stats' key is already in the first level hash - pre_all_star & post_all_star
    if 'stats' in player_dict:
        for stat in player_dict['stats']:
            if stat not in ('games'):
                if stat == 'playtime':
                    player_dict['stats'][stat] = two_decimals(float(player_dict['stats'][stat]) / float(player_dict['stats']['games']) / 60)
                else:
                    player_dict['stats'][stat] = two_decimals(float(player_dict['stats'][stat]) / float(player_dict['stats']['games']))
    else:
        for team in player_dict:
            for stat in player_dict[team]['stats']:
                # Python's 'or' expressions works like a single line if, so it's better to do an in
                if stat not in ('games', 'games_remain'):
                    if stat == 'playtime':
                        player_dict[team]['stats'][stat] = two_decimals(float(player_dict[team]['stats'][stat]) / float(player_dict[team]['stats']['games']) / 60)
                    else:
                        player_dict[team]['stats'][stat] = two_decimals(float(player_dict[team]['stats'][stat]) / float(player_dict[team]['stats']['games']))
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
    if mean == 0:
        return 0
    else:
        return two_decimals(std_deviation / mean)


# This method will calculate the trend for last n number of games
def last_n_games(csv_f, num_games):
    # We read the file backwards from the csv file
    # However, if the file does not fit in memory this method of using reverse will not work
    logger.info('Best stretch processing')
    count = 0
    PLAYER_DICT['last_'+str(num_games)+'_games'] = {}
    playtime = 0
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
            playtime = process_playtime(playtime, record[9])
            gmsc += float(record[28])
            points += float(record[27])
            rebounds += float(record[21])
            assists += float(record[22])
            steals += float(record[23])
            blocks += float(record[24])
            turnovers += float(record[25])
            threes += float(record[13])
            count +=1

    PLAYER_DICT['last_'+str(num_games)+'_games']['playtime'] = two_decimals((playtime / num_games)/60)
    PLAYER_DICT['last_'+str(num_games)+'_games']['gmsc'] = two_decimals(gmsc / num_games)
    PLAYER_DICT['last_'+str(num_games)+'_games']['points'] = two_decimals(points / num_games)
    PLAYER_DICT['last_'+str(num_games)+'_games']['rebounds'] = two_decimals(rebounds / num_games)
    PLAYER_DICT['last_'+str(num_games)+'_games']['assists'] = two_decimals(assists / num_games)
    PLAYER_DICT['last_'+str(num_games)+'_games']['steals'] = two_decimals(steals / num_games)
    PLAYER_DICT['last_'+str(num_games)+'_games']['blocks'] = two_decimals(blocks / num_games)
    PLAYER_DICT['last_'+str(num_games)+'_games']['turnovers'] = two_decimals(turnovers / num_games)
    PLAYER_DICT['last_'+str(num_games)+'_games']['threes'] = two_decimals(threes / num_games)
    PLAYER_DICT['last_'+str(num_games)+'_games']['dk_points'] = calc_dk_points(PLAYER_DICT['last_'+str(num_games)+'_games'])


def calc_dk_points(stats):
    dk_points = 0
    for (stat, value) in stats.iteritems():
        if stat in DK_SCORING:
            dk_points += (value * DK_SCORING[stat])

    dk_points = two_decimals(dk_points)
    return dk_points


pp = pprint.PrettyPrinter(indent=4)

# Open all team schedules for processing
SCHEDULE_DICT = {}
SCHEDULE_DICT['league_schedule'] = {}
for files in glob.glob('team_schedules/'+YEAR+'/*.csv'):
    team_name = files.split('/')[2].split('.c')[0]
    logger.info('Parsing schedule for: '+team_name)

    # this will need to be looped
    with open(files, 'rb') as f:
        try:
            read_team_schedule_csv(f, team_name)
            logger.info('Dumping json for: '+team_name)

            with open('json_files/team_schedules/'+YEAR+'/'+team_name+'.json', 'w') as outfile:
                json.dump(SCHEDULE_DICT[team_name], outfile)
        except csv.Error as e:
            sys.exit('file %s: %s' % (files, e))

with open('json_files/team_schedules/'+YEAR+'/league_schedule.json', 'w') as outfile:
    json.dump(SCHEDULE_DICT['league_schedule'], outfile)

ALL_PLAYERS = {}
# Open all player files for data parsing
for files in glob.glob('player_logs/'+YEAR+'/*.csv'):
    player_name = files.split('/')[2].split('.c')[0]

    # this will need to be looped
    logger.info('Parsing stats for: '+player_name)

    with open(files, 'rb') as f:
        try:
            PLAYER_DICT = read_player_csv(f, SCHEDULE_DICT, player_name)
            categorize_players_by_teams(PLAYER_DICT, ALL_PLAYERS)

            # Since we need to go through the files again we seek to the beginning of the file
            f.seek(0)
            last_n_games(f, 1)
            f.seek(0)
            last_n_games(f, 3)
            f.seek(0)
            last_n_games(f, 5)
            f.seek(0)
            last_n_games(f, 10)
            # Dump the json file
            logger.info('Dumping json for: '+player_name)
            with open('json_files/player_logs/'+YEAR+'/'+player_name+'.json', 'w') as outfile:
                json.dump(PLAYER_DICT, outfile)

        except csv.Error as e:
            sys.exit('file %s: %s' % (files, e))
# Dump a json for all players
with open('json_files/player_logs/'+YEAR+'/all_players.json', 'w') as outfile:
    json.dump(ALL_PLAYERS, outfile)

