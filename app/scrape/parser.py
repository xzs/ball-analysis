import pprint
import csv
import math
import json
import glob
import sys
import logging
import numpy
import re

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

    logger.debug('Completed creation of schedule dictionary for: '+team_name)
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
    player_dict['dfs_stats'] = {}

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

    stats_dict = {
        'all': {
            'points' : 0,
            'rebounds' : 0,
            'assists' : 0,
            'steals' : 0,
            'blocks' : 0,
            'turnovers' : 0,
            'threes' : 0,
            'fouls' : 0,
            'games': 0
        },
        'as_starter': {
            'points' : 0,
            'rebounds' : 0,
            'assists' : 0,
            'steals' : 0,
            'blocks' : 0,
            'turnovers' : 0,
            'threes' : 0,
            'fouls' : 0,
            'games': 0
        },
        'non_starter': {
            'points' : 0,
            'rebounds' : 0,
            'assists' : 0,
            'steals' : 0,
            'blocks' : 0,
            'turnovers' : 0,
            'threes' : 0,
            'fouls' : 0,
            'games': 0
        }

    }

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
    all_dfs_points = {}

    started_playtime_seconds = 0
    non_started_playtime_seconds = 0


    # We want to be able to create a player dictionary that will contain the statistics for the GmSc.
    # The dictionary will also contain detailed information abou the teams the player has played agianst
    for record in player_log:
        player_dict['basic_info']['age'] = record[3].split('-')[0]
        team = record[4]
        player_dict['basic_info']['team'] = team
        player_dict['basic_info']['position'] = record[len(record)-1]

        # If he played
        if record[1]:

            if record[5]:
                logger.debug('Compling away games')
                away_gmsc += float(record[28])
                away_games += 1
                away_playtime_seconds = process_playtime(away_playtime_seconds, record[9])
            else:
                logger.debug('Compling home games')
                home_gmsc += float(record[28])
                home_games += 1
                home_playtime_seconds = process_playtime(home_playtime_seconds, record[9])

            # for games the player started
            if record[8] == '1':
                logger.debug('Compling starter games')
                started_gmsc += float(record[28])
                started_games += 1
                started_playtime_seconds = process_playtime(started_playtime_seconds, record[9])
            else:
                logger.debug('Compling non_starter games')
                non_started_gmsc += float(record[28])
                non_started_games += 1
                non_started_playtime_seconds = process_playtime(non_started_playtime_seconds, record[9])

            # calculate the playtime for the player
            play_time_seconds = process_playtime(play_time_seconds, record[9])

            logger.debug('Begining game statistics')
            # Create new layers for statistics against every team
            new_stats_dict(player_dict['teams_against'], record[6], record)

            # Calculate the remaining games for each opponent
            player_dict['teams_against'][record[6]]['stats']['games_remain'] = schedule[team]['opp'][TEAMS_DICT[record[6]]] - player_dict['teams_against'][record[6]]['stats']['games']

            points_list.append(float(record[27]))
            assists_list.append(float(record[22]))
            rebounds_list.append(float(record[21]))

            logger.debug('Compling conference play')
            if record[6] in EASTERN_CONF:
                player_dict['eastern_conf']['games'] += 1
                east_gmsc += float(record[28])
            else:
                player_dict['western_conf']['games'] += 1
                west_gmsc += float(record[28])

            if record[8] == '1':
                stats_dict['as_starter'] = process_basic_stats(stats_dict['as_starter'], record)
            else:
                stats_dict['non_starter'] = process_basic_stats(stats_dict['non_starter'], record)

            stats_dict['all'] = process_basic_stats(stats_dict['all'], record)

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

            if record[30]:
                dfs_points = float(record[30])

                all_dfs_points[record[1]] = {
                    'opponent' : record[6],
                    'margin' : record[7],
                    'playtime' : record[9],
                    'date' : record[2],
                    'dk_points' : dfs_points
                }

                if 'max' not in player_dict['dfs_stats']:
                    player_dict['dfs_stats']['max'] = dfs_points
                else:
                    if player_dict['dfs_stats']['max'] < dfs_points:
                        player_dict['dfs_stats']['max'] = dfs_points
                if 'min' not in player_dict['dfs_stats']:
                    player_dict['dfs_stats']['min'] = dfs_points
                else:
                    if player_dict['dfs_stats']['min'] > dfs_points:
                        player_dict['dfs_stats']['min'] = dfs_points

    #  For now we only consider players who have played both a home or away game
    if home_games > 0 or away_games > 0:
        logger.debug('First level dictionary values processing')
        # calc home and away playtime + gmsc
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

        # calc starter and non starter playtime + gmsc
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

        # calc conferences gmsc
        if player_dict['eastern_conf']['games'] != 0:
            player_dict['eastern_conf']['gmsc'] = two_decimals(float(east_gmsc / player_dict['eastern_conf']['games']))
        else:
            player_dict['eastern_conf']['gmsc'] = 0

        if player_dict['western_conf']['games'] != 0:
            player_dict['western_conf']['gmsc'] = two_decimals(float(west_gmsc / player_dict['western_conf']['games']))
        else:
            player_dict['western_conf']['gmsc'] = 0

        # set playtimes
        player_dict['stats']['playtime'] = two_decimals(float(play_time_seconds / (away_games + home_games))/60)
        player_dict['as_starter']['playtime'] = player_dict['started_playtime']
        player_dict['non_starter']['playtime'] = player_dict['non_started_playtime']

        if started_games > 0:
            stats_dict['as_starter']['games'] = started_games
            player_dict['as_starter'] = process_summary_stats_def(player_dict['as_starter'], stats_dict['as_starter'], player_dict['average_started_gmsc'])

        if non_started_games > 0:
            stats_dict['non_starter']['games'] = non_started_games
            player_dict['non_starter'] = process_summary_stats_def(player_dict['non_starter'], stats_dict['non_starter'], player_dict['average_non_started_gmsc'])


        stats_dict['all']['games'] = away_games + home_games
        player_dict['stats'] = process_summary_stats_def(player_dict['stats'], stats_dict['all'], away_gmsc + home_gmsc)

        # variance of data
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

        # http://stackoverflow.com/a/4110705
        all_dfs_points = sorted(all_dfs_points.items(), key=lambda x: (x[1]["dk_points"]))
        process_best_dfs_points(10, all_dfs_points, player_dict['basic_info']['position'], player_dict)

        # pp.pprint(player_dict['fantasy_best'])
    return player_dict


def process_best_dfs_points(num_best, dfs_points, position, player_dict):

    player_dict['fantasy_best'] = {
        'log': []
    }
    pace = []
    pace_rank = []
    playtime = 0
    result_bucket = {
        'result': {
            'W': 0,
            'L': 0
        },
        'win_margin': [],
        'loss_margin': []
    }
    for record in list(reversed(dfs_points))[:num_best]:
        team = record[1]['opponent']
        if position in TEAM_DVP_STATS[team]:
            pace.append(float(LEAGUE_ADV_STATS[team]['Pace']['stat']))
            pace_rank.append(float(LEAGUE_ADV_STATS[team]['Pace']['rank']))
            playtime = process_playtime(playtime, record[1]['playtime'])
            points = re.findall("(\d+)", record[1]['margin'])[0]
            result_bucket = process_margin(record[1]['margin'][0], record[1]['margin'][3], points, result_bucket)

            player_dict['fantasy_best']['log'].append({
                'team': team,
                'game': record[1],
                'pace': LEAGUE_ADV_STATS[team]['Pace'],
                'dvp': TEAM_DVP_STATS[team][position]
            })

    player_dict['fantasy_best']['pace'] = {
        'pace': numpy_metrics({}, pace),
        'rank': numpy_metrics({}, pace_rank)
    }

    player_dict['fantasy_best']['margin'] = {
        'win': numpy_metrics({}, result_bucket['win_margin']),
        'loss': numpy_metrics({}, result_bucket['loss_margin'])
    }

    player_dict['fantasy_best']['results'] = {
        'win': result_bucket['result']['W'],
        'loss': result_bucket['result']['L']
    }

    player_dict['fantasy_best']['avg_playtime'] = two_decimals(float(playtime/num_best)/60)


def numpy_metrics(dict_obj, result_bucket):
    try:
        dict_obj['avg'] = two_decimals(numpy.average(result_bucket))
    except ValueError:  #raised if `y` is empty.
        pass

    try:
        dict_obj['med'] = two_decimals(numpy.median(result_bucket))
    except ValueError:  #raised if `y` is empty.
        pass

    try:
        dict_obj['min'] = two_decimals(numpy.min(result_bucket))
    except ValueError:  #raised if `y` is empty.
        pass

    try:
        dict_obj['max'] = two_decimals(numpy.max(result_bucket))
    except ValueError:  #raised if `y` is empty.
        pass

    return dict_obj

def process_margin(result, plus_minus, points, result_bucket):
    # results
    if result == 'W':
        result_bucket['result']['W'] += 1
    else:
        result_bucket['result']['L'] += 1

    # margin
    if plus_minus == '+':
        result_bucket['win_margin'].append(float(points))
    else:
        result_bucket['loss_margin'].append(float(points))

    return result_bucket


def process_basic_stats(dict_obj, record):
    dict_obj['points'] += float(record[27])
    dict_obj['rebounds'] += float(record[21])
    dict_obj['assists'] += float(record[22])
    dict_obj['steals'] += float(record[23])
    dict_obj['blocks'] += float(record[24])
    dict_obj['turnovers'] += float(record[25])
    dict_obj['threes'] += float(record[13])
    dict_obj['fouls'] += float(record[26])

    return dict_obj


def process_summary_stats_def(dict_obj, stats_dict, gmsc):

    dict_obj['points'] = two_decimals(float(stats_dict['points'] / stats_dict['games']))
    dict_obj['rebounds'] = two_decimals(float(stats_dict['rebounds'] / stats_dict['games']))
    dict_obj['assists'] = two_decimals(float(stats_dict['assists'] / stats_dict['games']))
    dict_obj['steals'] = two_decimals(float(stats_dict['steals'] / stats_dict['games']))
    dict_obj['blocks'] = two_decimals(float(stats_dict['blocks'] / stats_dict['games']))
    dict_obj['turnovers'] = two_decimals(float(stats_dict['turnovers'] / stats_dict['games']))
    dict_obj['threes'] = two_decimals(float(stats_dict['threes'] / stats_dict['games']))
    dict_obj['fouls'] = two_decimals(float(stats_dict['fouls'] / stats_dict['games']))
    # avg gmscr
    dict_obj['gmsc'] = two_decimals(float(gmsc /stats_dict['games']))
    dict_obj['dk_points'] = calc_dk_points(dict_obj)

    return dict_obj

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
            player_dict[layer]['stats']['fouls'] = float(player_dict[layer]['stats']['fouls'] + float(record[26]))
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
            player_dict[layer]['stats']['fouls'] = float(record[26])
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
        player_dict[layer]['stats']['fouls'] = float(record[26])

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
    logger.debug('Process consecutive sum')
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
    logger.debug('COV processing')
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
    logger.debug('Best stretch processing')
    count = 0
    PLAYER_DICT['last_'+str(num_games)+'_games'] = {}
    playtime = 0
    threes = 0
    fouls = 0
    gmsc = 0
    points = 0
    rebounds = 0
    assists = 0
    steals = 0
    blocks = 0
    turnovers = 0
    record_margin = ''

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
            fouls += float(record[26])
            if num_games == 1:
                record_margin = record[7] + ' ' + record[2]
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
    PLAYER_DICT['last_'+str(num_games)+'_games']['fouls'] = two_decimals(fouls / num_games)
    PLAYER_DICT['last_'+str(num_games)+'_games']['dk_points'] = calc_dk_points(PLAYER_DICT['last_'+str(num_games)+'_games'])
    if num_games == 1 and record_margin:
        PLAYER_DICT['last_'+str(num_games)+'_games']['record_margin'] = record_margin



def calc_dk_points(stats):
    dk_points = 0
    for (stat, value) in stats.iteritems():
        if stat in DK_SCORING:
            dk_points += (value * DK_SCORING[stat])

    dk_points = two_decimals(dk_points)
    return dk_points

# This method will calculate the trend for last n number of games
def last_n_games_adv(csv_f, num_games):
    # We read the file backwards from the csv file
    # However, if the file does not fit in memory this method of using reverse will not work
    logger.debug('Best stretch processing')
    count = 0
    # PLAYER_DICT['last_'+str(num_games)+'_games'] = {}
    ts = 0
    efg = 0
    usage = 0
    ortg = 0
    drtg = 0

    for record in reversed(list(csv.reader(csv_f))):
        # If he played
        if record[1] and count != num_games:
            if record[10]:
                ts += float(record[10])
            if record[19]:
                usage += float(record[19])
            if record[20]:
                ortg += float(record[20])
            if record[21]:
                drtg += float(record[21])
            if record[11]:
                efg += float(record[11])
            count +=1

    PLAYER_DICT['last_'+str(num_games)+'_games']['ts'] = two_decimals((ts / num_games)/60)
    PLAYER_DICT['last_'+str(num_games)+'_games']['usage'] = two_decimals(usage / num_games)
    PLAYER_DICT['last_'+str(num_games)+'_games']['ortg'] = two_decimals(ortg / num_games)
    PLAYER_DICT['last_'+str(num_games)+'_games']['drtg'] = two_decimals(drtg / num_games)
    PLAYER_DICT['last_'+str(num_games)+'_games']['efg'] = two_decimals(efg / num_games)

pp = pprint.PrettyPrinter(indent=4)

# Open all team schedules for processing
SCHEDULE_DICT = {}
TEAM_DVP_STATS = {}
SCHEDULE_DICT['league_schedule'] = {}
for files in glob.glob('team_schedules/'+YEAR+'/*.csv'):
    team_name = files.split('/')[2].split('.c')[0]

    with open(files, 'rb') as f:
        try:
            read_team_schedule_csv(f, team_name)
            logger.info('Dumping json for: '+team_name)

            # open team dvp stats
            with open('misc/fantasy_stats/'+team_name+'.json') as data_file:
                TEAM_DVP_STATS[team_name] = json.load(data_file)

            with open('json_files/team_schedules/'+YEAR+'/'+team_name+'.json', 'w') as outfile:
                json.dump(SCHEDULE_DICT[team_name], outfile)

        except csv.Error as e:
            sys.exit('file %s: %s' % (files, e))

with open('json_files/team_schedules/'+YEAR+'/league_schedule.json', 'w') as outfile:
    json.dump(SCHEDULE_DICT['league_schedule'], outfile)


with open('misc/team_stats/league.json') as data_file:
    LEAGUE_ADV_STATS = json.load(data_file)


ALL_PLAYERS = {}
# Open all player files for data parsing
for files in glob.glob('player_logs/'+YEAR+'/*.csv'):
    player_name = files.split('/')[2].split('.c')[0]

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
            try:
                with open('player_logs/advanced/'+YEAR+'/'+player_name+'.csv', 'rb') as adv_f:
                    adv_f.seek(0)
                    last_n_games_adv(adv_f, 1)
                    adv_f.seek(0)
                    last_n_games_adv(adv_f, 3)
                    adv_f.seek(0)
                    last_n_games_adv(adv_f, 5)
                    adv_f.seek(0)
                    last_n_games_adv(adv_f, 10)
            except IOError as e:
                print "Unable to open file" #Does not exist OR no read permissions
            # Dump the json file
            logger.debug('Dumping json for: '+player_name)
            with open('json_files/player_logs/'+YEAR+'/'+player_name+'.json', 'w') as outfile:
                json.dump(PLAYER_DICT, outfile)

        except csv.Error as e:
            sys.exit('file %s: %s' % (files, e))
# Dump a json for all players
with open('json_files/player_logs/'+YEAR+'/all_players.json', 'w') as outfile:
    json.dump(ALL_PLAYERS, outfile)

