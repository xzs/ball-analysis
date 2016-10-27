import MySQLdb
import pprint
import csv
import logging
import json
import MySQLdb.converters
from datetime import date, timedelta

pp = pprint.PrettyPrinter(indent=4)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

conv = MySQLdb.converters.conversions.copy()
conv[246] = float    # convert decimals to floats
conv[10] = str       # convert dates to strings

# Open database connection
db = MySQLdb.connect("127.0.0.1","root","","nba_scrape", conv=conv)

# prepare a cursor object using cursor() method
cursor = db.cursor()
DATE = date.today() - timedelta(1)
LAST_DATE_REG_SEASON = '2016-04-15'
FIRST_DATE_REG_SEASON = '2015-10-27'
DATE_FORMAT_YEAR = str("%Y-%m-%d")

POSITIONS = ['G', 'F', 'G-F', 'C']

TEAMS_DICT = {
    'ATL':'Atlanta Hawks',
    'BOS':'Boston Celtics',
    'BKN':'Brooklyn Nets',
    'CHA':'Charlotte Hornets',
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

PLAYER_SYNERGY_TABLES_OFFENSE = [
    'synergy_cut_offense', 'synergy_handoff_offense',
    'synergy_isolation_offense', 'synergy_misc_offense', 'synergy_off_screen_offense',
    'synergy_post_up_offense', 'synergy_pr_ball_handler_offense', 'synergy_pr_roll_man_offense',
    'synergy_put_back_offense', 'synergy_spot_up_offense', 'synergy_transition_offense'
]

PLAYER_SYNERGY_TABLES_DEFENSE = [
    'synergy_handoff_defense', 'synergy_isolation_defense',
    'synergy_off_screen_defense', 'synergy_post_up_defense', 'synergy_pr_ball_handler_defense',
    'synergy_pr_roll_man_defense', 'synergy_spot_up_defense'
]

TEAM_SYNERGY_TABLES_OFFENSE = [
    'synergy_cut_team_offense', 'synergy_handoff_team_offense',
    'synergy_isolation_team_offense', 'synergy_misc_team_offense', 'synergy_off_screen_team_offense',
    'synergy_post_up_team_offense', 'synergy_pr_ball_handler_team_offense', 'synergy_pr_roll_man_team_offense',
    'synergy_put_back_team_offense', 'synergy_spot_up_team_offense', 'synergy_transition_team_offense'
]

TEAM_SYNERGY_TABLES_DEFENSE = [
    'synergy_cut_team_defense', 'synergy_handoff_team_defense',
    'synergy_isolation_team_defense', 'synergy_misc_team_defense', 'synergy_off_screen_team_defense',
    'synergy_post_up_team_defense', 'synergy_pr_ball_handler_team_defense', 'synergy_pr_roll_man_team_defense',
    'synergy_put_back_team_defense', 'synergy_spot_up_team_defense', 'synergy_transition_team_defense'
]


def default_player_box_query():
    player_query = 'SELECT STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") as DATE, '\
        'ub.PLAYER_NAME as NAME, '\
        'ub.TEAM_ABBREVIATION as TEAM_NAME, '\
        'tb2.TEAM_ABBREVIATION as TEAM_AGAINST, '\
        'ub.START_POSITION, '\
        'ub.MIN, ub.USG_PCT, ub.PCT_FGA, ub.PCT_FG3A, ub.PCT_FTA, '\
        'ub.PCT_REB, ub.PCT_AST, ub.PCT_TOV, ub.PCT_STL, '\
        'ub.PCT_BLK, ub.PCT_PF, ub.PCT_PTS, '\
        'tb.FGA, tb.FG_PCT, tb.FG3M, tb.FG3A, tb.FG3_PCT, '\
        'tb.FTA, tb.FT_PCT, tb.REB, tb.AST, tb.STL, '\
        'tb.BLK, tb.TO, tb.PF, tb.PTS, tb.PLUS_MINUS, '\
        'tb.FG3M*0.5 + tb.REB*1.25+tb.AST*1.25+tb.STL*2+tb.BLK*2+tb.TO*-0.5+tb.PTS*1 as DK_POINTS, '\
        'ptb.RBC as REB_CHANCES, ptb.TCHS as TOUCHES, ptb.PASS, '\
        'ptb.AST/ptb.PASS as AST_PER_PASS, ptb.CFGA as CONTESTED_FGA, ptb.CFG_PCT as CONTESTED_FG_PCT, '\
        'ab.OFF_RATING, ab.DEF_RATING, ab.NET_RATING, '\
        'ab.AST_PCT, ab.REB_PCT, ab.EFG_PCT, ab.PACE, '\
        'sb.PCT_FGA_2PT, sb.PCT_FGA_3PT, sb.PCT_PTS_2PT, sb.PCT_PTS_3PT, '\
        'sb.PCT_PTS_OFF_TOV, sb.PCT_PTS_PAINT, '\
        'sb.PCT_AST_FGM, sb.PCT_UAST_FGM, '\
        'ff.OPP_EFG_PCT, ff.OPP_FTA_RATE, ff.OPP_TOV_PCT, ff.OPP_OREB_PCT, '\
        'mb.PTS_OFF_TOV, mb.PTS_FB, mb.PTS_2ND_CHANCE, mb.PTS_PAINT, mb.OPP_PTS_OFF_TOV, '\
        'mb.OPP_PTS_2ND_CHANCE, mb.OPP_PTS_FB, mb.OPP_PTS_PAINT, mb.OPP_PTS_2ND_CHANCE, mb.PFD, '\
        'gs.NATL_TV_BROADCASTER_ABBREVIATION as NATIONAL_TV '\
    'FROM usage_boxscores as ub '\
        'LEFT JOIN game_summary as gs '\
            'ON gs.game_id = ub.game_id '\
        'LEFT JOIN traditional_boxscores as tb '\
            'ON tb.game_id = ub.game_id AND tb.player_id = ub.player_id '\
        'LEFT JOIN player_tracking_boxscores as ptb '\
            'ON ptb.game_id = ub.game_id AND ptb.player_id = ub.player_id '\
        'LEFT JOIN advanced_boxscores as ab '\
            'ON ab.game_id = ub.game_id AND ab.player_id = ub.player_id '\
        'LEFT JOIN scoring_boxscores as sb '\
            'ON sb.game_id = ub.game_id AND sb.player_id = ub.player_id '\
        'LEFT JOIN four_factors_boxscores as ff '\
            'ON ff.game_id = ub.game_id AND ff.player_id = ub.player_id '\
        'LEFT JOIN misc_boxscores as mb '\
            'ON mb.game_id = ub.game_id AND mb.player_id = ub.player_id '\
        'INNER JOIN (SELECT tbt.game_id, tbt.TEAM_ABBREVIATION FROM traditional_boxscores_team as tbt) as tb2 '\
            'ON tb2.game_id = ub.game_id and tb2.TEAM_ABBREVIATION != ub.TEAM_ABBREVIATION ' % {'date_format_year': DATE_FORMAT_YEAR}

    return player_query


def default_team_query():
    team_query = 'SELECT gs.GAME_ID, '\
        'STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") as DATE, '\
        'ab.TEAM_ABBREVIATION as TEAM, '\
        'tb2.TEAM_ABBREVIATION as TEAM_AGAINST, '\
        'tb.FGA, tb.FG_PCT, tb.FG3M, tb.FG3A, tb.FG3_PCT, '\
        'tb.FTA, tb.FT_PCT, tb.REB, tb.AST, tb.STL, '\
        'tb.BLK, tb.TO, tb.PF, tb.PTS, tb.PLUS_MINUS,'\
        'tb.FG3M*0.5 + tb.REB*1.25+tb.AST*1.25+tb.STL*2+tb.BLK*2+tb.TO*-0.5+tb.PTS*1 as DK_POINTS, '\
        'ptb.RBC as REB_CHANCES, ptb.TCHS as TOUCHES, ptb.PASS, ptb.AST/ptb.PASS as AST_PER_PASS, '\
        'ptb.CFGA as CONTESTED_FGA, ptb.CFG_PCT as CONTESTED_FG_PCT, '\
        'ab.OFF_RATING, ab.DEF_RATING, ab.NET_RATING, '\
        'ab.AST_PCT, ab.REB_PCT, ab.EFG_PCT, ab.PACE, '\
        'sb.PCT_FGA_2PT, sb.PCT_FGA_3PT, sb.PCT_PTS_2PT, sb.PCT_PTS_3PT, '\
        'sb.PCT_PTS_OFF_TOV, sb.PCT_PTS_PAINT, '\
        'ff.OPP_EFG_PCT, ff.OPP_FTA_RATE, ff.OPP_TOV_PCT, ff.OPP_OREB_PCT, '\
        'mb.PTS_OFF_TOV, mb.PTS_FB, mb.PTS_2ND_CHANCE, mb.PTS_PAINT, '\
        'mb.OPP_PTS_OFF_TOV, mb.OPP_PTS_2ND_CHANCE, mb.OPP_PTS_FB, mb.OPP_PTS_PAINT, '\
        'mb.OPP_PTS_2ND_CHANCE, mb.PFD, '\
        'os.LARGEST_LEAD, os.TIMES_TIED, '\
        'gs.NATL_TV_BROADCASTER_ABBREVIATION as NATIONAL_TV '\
    'FROM advanced_boxscores_team as ab '\
        'LEFT JOIN game_summary as gs '\
            'ON gs.game_id = ab.game_id '\
        'LEFT JOIN traditional_boxscores_team as tb '\
            'ON tb.game_id = ab.game_id AND tb.team_abbreviation = ab.team_abbreviation '\
        'LEFT JOIN player_tracking_boxscores_team as ptb '\
            'ON ptb.game_id = ab.game_id AND ptb.team_abbreviation = ab.team_abbreviation '\
        'LEFT JOIN scoring_boxscores_team as sb '\
            'ON sb.game_id = ab.game_id AND sb.team_abbreviation = ab.team_abbreviation '\
        'LEFT JOIN four_factors_boxscores_team as ff '\
            'ON ff.game_id = ab.game_id AND ff.team_abbreviation = ab.team_abbreviation '\
        'LEFT JOIN misc_boxscores_team as mb '\
            'ON mb.game_id = ab.game_id AND mb.team_abbreviation = ab.team_abbreviation '\
        'LEFT JOIN other_stats as os '\
            'ON os.game_id = ab.game_id AND os.team_abbreviation = ab.team_abbreviation '\
        'INNER JOIN (SELECT tbt.game_id, tbt.TEAM_ABBREVIATION FROM traditional_boxscores_team as tbt) as tb2 '\
            'ON tb2.game_id = ab.game_id AND tb2.TEAM_ABBREVIATION != ab.TEAM_ABBREVIATION ' % {'date_format_year': DATE_FORMAT_YEAR}

    return team_query


def synergy_queries():

    # player
    player_offense_dict = {}
    for table in PLAYER_SYNERGY_TABLES_OFFENSE:
        player_offense_query = 'SELECT CONCAT(PlayerFirstName, " ", PlayerLastName) as NAME, TeamNameAbbreviation as TEAM_NAME, GP, P, '\
                            'ROUND(PossG,2) as POSSG, ROUND(PPP,4) as PPP, ROUND(PPG,4) as PPG, BetterPPP+1 as PPP_RANK, '\
                            'CASE '\
                            'WHEN @prev_value = PossG THEN @rank_count '\
                            'WHEN @prev_value := PossG THEN @rank_count := @rank_count + 1 '\
                            'END AS POSSG_RANK '\
                            'FROM %(table)s, (SELECT @prev_value:=NULL, @rank_count:=0) as V '\
                                'WHERE DATE = "%(date)s" ORDER BY PossG DESC' % {'date': DATE, 'table': table}
        player_offense_dict[table] = format_to_json(execute_query(player_offense_query), 'NAME')

    # json dump for all players
    with open('../scrape/json_files/synergy/player_offense_data.json', 'w') as outfile:
        logger.info('Writing synergy to json file: player_offense_data')
        json.dump(player_offense_dict, outfile)


    # player defense
    player_defense_dict = {}
    for table in PLAYER_SYNERGY_TABLES_DEFENSE:
        player_defense_query = 'SELECT CONCAT(PlayerFirstName, " ", PlayerLastName) as NAME, TeamNameAbbreviation as TEAM_NAME, GP, P, '\
                            'ROUND(PossG,2) as POSSG, ROUND(PPP,4) as PPP, ROUND(PPG,4) as PPG, BetterPPP+1 as PPP_RANK, '\
                            'CASE '\
                            'WHEN @prev_value = PossG THEN @rank_count '\
                            'WHEN @prev_value := PossG THEN @rank_count := @rank_count + 1 '\
                            'END AS POSSG_RANK '\
                            'FROM %(table)s, (SELECT @prev_value:=NULL, @rank_count:=0) as V '\
                                'WHERE DATE = "%(date)s" ORDER BY PossG DESC' % {'date': DATE, 'table': table}
        player_defense_dict[table] = format_to_json(execute_query(player_defense_query), 'NAME')

    # json dump for all players
    with open('../scrape/json_files/synergy/player_defense_data.json', 'w') as outfile:
        logger.info('Writing synergy to json file: player_defense_data')
        json.dump(player_defense_dict, outfile)


    # team offense
    team_offense_dict = {}
    for table in TEAM_SYNERGY_TABLES_OFFENSE:
        # reset the session variables http://dba.stackexchange.com/a/56609
        team_offense_query = 'SELECT TeamName as NAME, TeamNameAbbreviation as TEAM_NAME, GP, '\
                            'ROUND(PossG,2) as POSSG, ROUND(PPP,4) as PPP, ROUND(FG,2) as FG, BetterPPP+1 as PPP_RANK, '\
                            'CASE '\
                            'WHEN @prev_value = PossG THEN @rank_count '\
                            'WHEN @prev_value := PossG THEN @rank_count := @rank_count + 1 '\
                            'END AS POSSG_RANK '\
                            'FROM %(table)s, (SELECT @prev_value:=NULL, @rank_count:=0) as V '\
                                'WHERE DATE = "%(date)s" ORDER BY PossG DESC' % {'date': DATE, 'table': table}
        team_offense_dict[table] = format_to_json(execute_query(team_offense_query), 'TEAM_NAME')

    # store json dump for all teams
    with open('../scrape/json_files/synergy/team_offense_data.json', 'w') as outfile:
        logger.info('Writing synergy to json file: team_offense_data')
        json.dump(team_offense_dict, outfile)

    # team defense
    team_defense_dict = {}
    for table in TEAM_SYNERGY_TABLES_DEFENSE:
        team_defense_query = 'SELECT TeamName as NAME, TeamNameAbbreviation as TEAM_NAME, GP, '\
                        'ROUND(PossG,2) as POSSG, ROUND(PPP,4) as PPP, ROUND(FG,2) as FG, BetterPPP+1 as PPP_RANK, '\
                        'CASE '\
                        'WHEN @prev_value = PPP THEN @rank_count '\
                        'WHEN @prev_value := PPP THEN @rank_count := @rank_count + 1 '\
                        'END AS POSSG_RANK '\
                        'FROM %(table)s, (SELECT @prev_value:=NULL, @rank_count:=0) as V '\
                            'WHERE DATE = "%(date)s" ORDER BY PossG DESC' % {'date': DATE, 'table': table}
        team_defense_dict[table] = format_to_json(execute_query(team_defense_query), 'TEAM_NAME')

    # store json dump for all teams
    with open('../scrape/json_files/synergy/team_defense_data.json', 'w') as outfile:
        logger.info('Writing synergy to json file: team_defense_data')
        json.dump(team_defense_dict, outfile)


def format_to_json(query_result, key_name):

    final_result = {}
    for result in query_result:
        name = result[key_name]
        final_result[name] = result

    return final_result


def sportvu_queries(query_type, is_regular_season, is_player, teams, date):

    query_dict = {
        'query_for': '',
        'query_id': ''
    }

    if query_type == 'player':
        query_dict['query_for'] = 'PLAYER_NAME'
        query_dict['query_id'] = 'PLAYER_ID'
        query_type = ''
    else:
        query_dict['query_for'] = 'TEAM_NAME'
        query_dict['query_id'] = 'TEAM_ID'
        query_type = '_team'

    sportvu_query = 'SELECT cs.%(query_for)s as NAME, cs.TEAM_ABBREVIATION as TEAM_NAME, cs.GP, '\
            'cs.CATCH_SHOOT_FGA/cs.GP as "CATCH_SHOOT_FGA_PER_GAME", cs.CATCH_SHOOT_FG_PCT, cs.CATCH_SHOOT_FG3A/cs.GP as "CATCH_SHOOT_3FGA_PER_GAME", '\
            'cs.CATCH_SHOOT_FG3_PCT, cs.CATCH_SHOOT_EFG_PCT, '\
            'def.DEF_RIM_FGM/cs.GP as "FG_AT_RIM_ALLOWED_PER_GAME", def.DEF_RIM_FGA/cs.GP as "FG_AT_RIM_FACED_PER_GAME", def.DEF_RIM_FG_PCT, '\
            'dr.DRIVES/cs.GP as "DRIVES_PER_GAME", dr.DRIVE_FGA/cs.GP as "DRIVE_FGA_PER_GAME", '\
            'dr.DRIVE_FG_PCT, dr.DRIVE_PTS/cs.GP as "DRIVE_PTS_PER_GAME", dr.DRIVE_PF/cs.GP as "DRIVE_PF_PER_GAME", dr.DRIVE_PF_PCT, '\
            'et.ELBOW_TOUCHES/cs.GP as "ELBOW_TOUCHES_PER_GAME", et.ELBOW_TOUCH_FGA/cs.GP as "ELBOW_TOUCH_FGA_PER_GAME", '\
            'et.ELBOW_TOUCH_FG_PCT, et.ELBOW_TOUCH_PASSES/cs.GP as "ELBOW_TOUCH_PASSES_PER_GAME", '\
            'pt.PAINT_TOUCHES/cs.GP as "PAINT_TOUCHES_PER_GAME", pt.PAINT_TOUCH_FGA/cs.GP as "PAINT_TOUCH_FGA_PER_GAME", '\
            'pt.PAINT_TOUCH_FG_PCT, pt.PAINT_TOUCH_PASSES/cs.GP as "PAINT_TOUCH_PASSES_PER_GAME", '\
            'pass.PASSES_MADE/cs.GP as "PASSES_MADE_PER_GAME", pass.PASSES_RECEIVED/cs.GP as "PASSES_RECEIVED_PER_GAME", '\
            'pass.AST_PTS_CREATED/cs.GP as "AST_PTS_CREATED_PER_GAME", '\
            'poss.TOUCHES/cs.GP as "TOUCHES_PER_GAME", poss.TIME_OF_POSS/cs.GP AS "TIME_OF_POSS_PER_GAME", '\
            'poss.AVG_SEC_PER_TOUCH, poss.PTS_PER_TOUCH, '\
            'pot.POST_TOUCHES/cs.GP as "POST_TOUCHES_PER_GAME", pot.POST_TOUCH_FGA/cs.GP as "POST_TOUCH_FGA_PER_GAME", '\
            'pot.POST_TOUCH_FG_PCT, pot.POST_TOUCH_PASSES/cs.GP as "POST_TOUCH_PASSES_PER_GAME", '\
            'pus.PULL_UP_FGA/cs.GP as "PULL_UP_FGA_PER_GAME", pus.PULL_UP_FG_PCT, pus.PULL_UP_PTS/cs.GP as "PULL_UP_PTS_PER_GAME", '\
            'pus.PULL_UP_FG3A/cs.GP as "PULL_UP_3FGA_PER_GAME", pus.PULL_UP_FG3_PCT, pus.PULL_UP_EFG_PCT, '\
            'reb.OREB/cs.GP as "OREB_PER_GAME", reb.OREB_CHANCE_PCT, reb.AVG_OREB_DIST, reb.DREB/cs.GP as "DREB_PER_GAME", '\
            'reb.DREB_CHANCE_PCT, reb.AVG_DREB_DIST, reb.REB/cs.GP as "REB_PER_GAME", reb.REB_CHANCE_PCT, reb.AVG_REB_DIST, '\
            'sp.DIST_MILES/cs.GP as "DIST_MILES_PER_GAME", sp.AVG_SPEED '\
    'FROM sportvu_catch_shoot%(query_type)s as cs '\
        'LEFT JOIN sportvu_defense%(query_type)s as def '\
            'ON def.%(query_id)s = cs.%(query_id)s '\
            'AND def.DATE = cs.DATE '\
            'AND def.IS_REGULAR_SEASON = cs.IS_REGULAR_SEASON '\
        'LEFT JOIN sportvu_drives%(query_type)s as dr '\
            'ON dr.%(query_id)s = cs.%(query_id)s '\
            'AND dr.DATE = cs.DATE '\
            'AND dr.IS_REGULAR_SEASON = cs.IS_REGULAR_SEASON '\
        'LEFT JOIN sportvu_elbow_touches%(query_type)s as et '\
            'ON et.%(query_id)s = cs.%(query_id)s '\
            'AND et.DATE = cs.DATE '\
            'AND et.IS_REGULAR_SEASON = cs.IS_REGULAR_SEASON '\
        'LEFT JOIN sportvu_paint_touches%(query_type)s as pt '\
            'ON pt.%(query_id)s = cs.%(query_id)s '\
            'AND pt.DATE = cs.DATE '\
            'AND pt.IS_REGULAR_SEASON = cs.IS_REGULAR_SEASON '\
        'LEFT JOIN sportvu_passing%(query_type)s as pass '\
            'ON pass.%(query_id)s = cs.%(query_id)s '\
            'AND pass.DATE = cs.DATE '\
            'AND pass.IS_REGULAR_SEASON = cs.IS_REGULAR_SEASON '\
        'LEFT JOIN sportvu_possessions%(query_type)s as poss '\
            'ON poss.%(query_id)s = cs.%(query_id)s '\
            'AND poss.DATE = cs.DATE '\
            'AND poss.IS_REGULAR_SEASON = cs.IS_REGULAR_SEASON '\
        'LEFT JOIN sportvu_post_touches%(query_type)s as pot '\
            'ON pot.%(query_id)s = cs.%(query_id)s '\
            'AND pot.DATE = cs.DATE '\
            'AND pot.IS_REGULAR_SEASON = cs.IS_REGULAR_SEASON '\
        'LEFT JOIN sportvu_pull_up_shoot%(query_type)s as pus '\
            'ON pus.%(query_id)s = cs.%(query_id)s '\
            'AND pus.DATE = cs.DATE '\
            'AND pus.IS_REGULAR_SEASON = cs.IS_REGULAR_SEASON '\
        'LEFT JOIN sportvu_rebounding%(query_type)s as reb '\
            'ON reb.%(query_id)s = cs.%(query_id)s '\
            'AND reb.DATE = cs.DATE '\
            'AND reb.IS_REGULAR_SEASON = cs.IS_REGULAR_SEASON '\
        'LEFT JOIN sportvu_speed%(query_type)s as sp '\
            'ON sp.%(query_id)s = cs.%(query_id)s '\
            'AND sp.DATE = cs.DATE '\
            'AND sp.IS_REGULAR_SEASON = cs.IS_REGULAR_SEASON '\
    'WHERE cs.DATE = "%(date)s" AND cs.IS_REGULAR_SEASON = %(is_regular_season)s ' % {
        'date': date,
        'query_for': query_dict['query_for'],
        'query_id': query_dict['query_id'],
        'query_type': query_type,
        'is_regular_season': is_regular_season
    }

    # compare teams if passed
    if is_player == 1:
        sportvu_query += 'AND cs.PLAYER_NAME = "%(player)s" ' % {
            'player': teams,
        }
    else:
        sportvu_query += 'AND (cs.TEAM_ABBREVIATION = "%(team_one)s" OR cs.TEAM_ABBREVIATION = "%(team_two)s")' % {
            'team_one': teams[0],
            'team_two': teams[1]
        }

    return sportvu_query


def get_sportvu_game_logs(name, query_type, is_regular_season, last_n):
    query_dict = {
        'query_for': '',
        'query_id': ''
    }

    if query_type == 'player':
        query_dict['query_for'] = 'PLAYER_NAME'
        query_dict['query_id'] = 'PLAYER_ID'
        query_type = ''
    else:
        query_dict['query_for'] = 'TEAM_ABBREVIATION'
        query_dict['query_id'] = 'TEAM_ID'
        query_type = '_team'

    sportvu_query = 'SELECT cs.DATE, tb.%(query_for)s as NAME, '\
                    'tb.TEAM_ABBREVIATION as TEAM_NAME, tb2.TEAM_ABBREVIATION as TEAM_AGAINST, tb.MIN, '\
                    'cs.CATCH_SHOOT_FGM, cs.CATCH_SHOOT_FGM - cs.CATCH_SHOOT_FG3M as CATCH_SHOOT_FG2M, cs.CATCH_SHOOT_FGA, '\
                    'cs.CATCH_SHOOT_FGA - cs.CATCH_SHOOT_FG3A as CATCH_SHOOT_FG2A, cs.CATCH_SHOOT_FG_PCT, '\
                    'cs.CATCH_SHOOT_PTS, cs.CATCH_SHOOT_FG3M, cs.CATCH_SHOOT_FG3A, cs.CATCH_SHOOT_FG3_PCT, cs.CATCH_SHOOT_EFG_PCT, '\
                    'def.DEF_RIM_FGM as "FG_AT_RIM_ALLOWED", def.DEF_RIM_FGA as "FG_AT_RIM_FACED", def.DEF_RIM_FG_PCT, '\
                    'dr.DRIVES, dr.DRIVE_FGM, dr.DRIVE_FGA, dr.DRIVE_FG_PCT, dr.DRIVE_FTM, dr.DRIVE_FTA, dr.DRIVE_FT_PCT, dr.DRIVE_PTS, dr.DRIVE_PTS_PCT, '\
                    'dr.DRIVE_PASSES, dr.DRIVE_PASSES_PCT, dr.DRIVE_AST, dr.DRIVE_AST_PCT, dr.DRIVE_TOV, dr.DRIVE_TOV_PCT, dr.DRIVE_PF, dr.DRIVE_PF_PCT, '\
                    'et.ELBOW_TOUCHES, et.ELBOW_TOUCH_FGM, et.ELBOW_TOUCH_FGA, et.ELBOW_TOUCH_FG_PCT, et.ELBOW_TOUCH_FTM, et.ELBOW_TOUCH_FTA, '\
                    'et.ELBOW_TOUCH_FT_PCT, et.ELBOW_TOUCH_PTS, et.ELBOW_TOUCH_PTS_PCT, et.ELBOW_TOUCH_PASSES, et.ELBOW_TOUCH_PASSES_PCT, '\
                    'et.ELBOW_TOUCH_AST, et.ELBOW_TOUCH_AST_PCT, et.ELBOW_TOUCH_TOV, et.ELBOW_TOUCH_TOV_PCT, et.ELBOW_TOUCH_FOULS, et.ELBOW_TOUCH_FOULS_PCT, '\
                    'pt.PAINT_TOUCHES, pt.PAINT_TOUCH_FGM, pt.PAINT_TOUCH_FGA, pt.PAINT_TOUCH_FG_PCT, pt.PAINT_TOUCH_FTM, pt.PAINT_TOUCH_FTA, '\
                    'pt.PAINT_TOUCH_FT_PCT, pt.PAINT_TOUCH_PTS, pt.PAINT_TOUCH_PTS_PCT, pt.PAINT_TOUCH_PASSES, pt.PAINT_TOUCH_PASSES_PCT, '\
                    'pt.PAINT_TOUCH_AST, pt.PAINT_TOUCH_AST_PCT, pt.PAINT_TOUCH_TOV, pt.PAINT_TOUCH_TOV_PCT, pt.PAINT_TOUCH_FOULS, pt.PAINT_TOUCH_FOULS_PCT, '\
                    'pass.PASSES_MADE, pass.PASSES_RECEIVED, pass.AST, pass.FT_AST, pass.SECONDARY_AST, pass.POTENTIAL_AST, pass.AST_PTS_CREATED, '\
                    'pass.AST_ADJ, pass.AST_TO_PASS_PCT, pass.AST_TO_PASS_PCT_ADJ, '\
                    'poss.POINTS, poss.TOUCHES, poss.FRONT_CT_TOUCHES, poss.TIME_OF_POSS, poss.AVG_SEC_PER_TOUCH, poss.AVG_DRIB_PER_TOUCH, '\
                    'poss.PTS_PER_TOUCH, poss.ELBOW_TOUCHES, poss.POST_TOUCHES, poss.PAINT_TOUCHES, poss.PTS_PER_ELBOW_TOUCH, poss.PTS_PER_POST_TOUCH, poss.PTS_PER_PAINT_TOUCH, '\
                    'pot.TOUCHES, pot.POST_TOUCHES, pot.POST_TOUCH_FGM, pot.POST_TOUCH_FGA, pot.POST_TOUCH_FG_PCT, pot.POST_TOUCH_FTM, pot.POST_TOUCH_FTA, '\
                    'pot.POST_TOUCH_FT_PCT, pot.POST_TOUCH_PTS, pot.POST_TOUCH_PTS_PCT, pot.POST_TOUCH_PASSES, pot.POST_TOUCH_PASSES_PCT, pot.POST_TOUCH_AST, pot.POST_TOUCH_AST_PCT, '\
                    'pot.POST_TOUCH_TOV, pot.POST_TOUCH_TOV_PCT, pot.POST_TOUCH_FOULS, pot.POST_TOUCH_FOULS_PCT, '\
                    'pus.PULL_UP_FGM, pus.PULL_UP_FGM - pus.PULL_UP_FG3M as PULL_UP_FG2M, pus.PULL_UP_FGA, pus.PULL_UP_FGA - pus.PULL_UP_FG3A as PULL_UP_FG2A, '\
                    'pus.PULL_UP_FG_PCT, pus.PULL_UP_FG3M, pus.PULL_UP_FG3A, pus.PULL_UP_FG3_PCT, pus.PULL_UP_PTS, pus.PULL_UP_EFG_PCT, '\
                    'reb.OREB, reb.OREB_CONTEST, reb.OREB_UNCONTEST, reb.OREB_CONTEST_PCT, reb.OREB_CHANCES, reb.OREB_CHANCE_PCT, reb.OREB_CHANCE_DEFER, '\
                    'reb.OREB_CHANCE_PCT_ADJ, reb.AVG_OREB_DIST, reb.DREB, reb.DREB_CONTEST, reb.DREB_UNCONTEST, reb.DREB_CONTEST_PCT, reb.DREB_CHANCES, '\
                    'reb.DREB_CHANCE_PCT, reb.DREB_CHANCE_DEFER, reb.DREB_CHANCE_PCT_ADJ, reb.AVG_DREB_DIST, reb.REB, reb.REB_CONTEST, reb.REB_UNCONTEST, '\
                    'reb.REB_CONTEST_PCT, reb.REB_CHANCES, reb.REB_CHANCE_PCT, reb.REB_CHANCE_DEFER, reb.REB_CHANCE_PCT_ADJ, reb.AVG_REB_DIST, '\
                    'sp.DIST_FEET, sp.DIST_MILES, sp.DIST_MILES_OFF, sp.DIST_MILES_DEF, sp.AVG_SPEED, sp.AVG_SPEED_OFF, sp.AVG_SPEED_DEF, '\
                    'tb.FG3M*0.5 + tb.REB*1.25 + tb.AST*1.25 + tb.STL*2 + tb.BLK*2 + tb.TO*-0.5 + tb.PTS*1 as DK_POINTS '\
                    'FROM sportvu_catch_shoot%(query_type)s_game_logs as cs  '\
                    'LEFT JOIN sportvu_defense%(query_type)s_game_logs as def ON def.%(query_id)s = cs.%(query_id)s AND def.GAME_ID = cs.GAME_ID '\
                    'LEFT JOIN sportvu_drives%(query_type)s_game_logs as dr ON dr.%(query_id)s = cs.%(query_id)s AND dr.GAME_ID = cs.GAME_ID '\
                    'LEFT JOIN sportvu_elbow_touches%(query_type)s_game_logs as et ON et.%(query_id)s = cs.%(query_id)s AND et.GAME_ID = cs.GAME_ID '\
                    'LEFT JOIN sportvu_paint_touches%(query_type)s_game_logs as pt ON pt.%(query_id)s = cs.%(query_id)s AND pt.GAME_ID = cs.GAME_ID '\
                    'LEFT JOIN sportvu_passing%(query_type)s_game_logs as pass ON pass.%(query_id)s = cs.%(query_id)s AND pass.GAME_ID = cs.GAME_ID '\
                    'LEFT JOIN sportvu_possessions%(query_type)s_game_logs as poss ON poss.%(query_id)s = cs.%(query_id)s AND poss.GAME_ID = cs.GAME_ID '\
                    'LEFT JOIN sportvu_post_touches%(query_type)s_game_logs as pot ON pot.%(query_id)s = cs.%(query_id)s AND pot.GAME_ID = cs.GAME_ID '\
                    'LEFT JOIN sportvu_pull_up_shoot%(query_type)s_game_logs as pus ON pus.%(query_id)s = cs.%(query_id)s AND pus.GAME_ID = cs.GAME_ID '\
                    'LEFT JOIN sportvu_rebounding%(query_type)s_game_logs as reb ON reb.%(query_id)s = cs.%(query_id)s AND reb.GAME_ID = cs.GAME_ID '\
                    'LEFT JOIN sportvu_speed%(query_type)s_game_logs as sp ON sp.%(query_id)s = cs.%(query_id)s AND sp.GAME_ID = cs.GAME_ID '\
                    'LEFT JOIN traditional_boxscores%(query_type)s as tb ON tb.%(query_id)s = cs.%(query_id)s AND tb.GAME_ID = cs.GAME_ID '\
                    'INNER JOIN (SELECT tbt.game_id, tbt.TEAM_ABBREVIATION FROM traditional_boxscores_team as tbt) as tb2 ON tb2.game_id = cs.GAME_ID and tb2.TEAM_ABBREVIATION != tb.TEAM_ABBREVIATION '\
                    'WHERE cs.IS_REGULAR_SEASON = %(is_regular_season)s AND tb.%(query_for)s = "%(name)s" ORDER BY DATE ' % {
                        'name': name,
                        'is_regular_season': is_regular_season,
                        'query_for': query_dict['query_for'],
                        'query_id': query_dict['query_id'],
                        'query_type': query_type
                    }

    if last_n != 0:
        sportvu_query += 'DESC LIMIT %(last_n)s' % {'last_n': last_n}

    return sportvu_query


def get_sportvu_team_logs(name, stat, is_regular_season):

    sportvu_query = 'SELECT * FROM sportvu_%(stat)s_team_game_logs as sl '\
                    'INNER JOIN (SELECT tb.GAME_ID, tb.TEAM_ABBREVIATION, tb.FG3M*0.5 + tb.REB*1.25 + tb.AST*1.25 + tb.STL*2 + tb.BLK*2 + tb.TO*-0.5 + tb.PTS*1 as DK_POINTS '\
                        'FROM traditional_boxscores_team AS tb) AS tb ON tb.GAME_ID = sl.GAME_ID and tb.TEAM_ABBREVIATION = sl.TEAM_ABBREVIATION '\
                    'WHERE sl.TEAM_ABBREVIATION = "%(name)s" AND sl.IS_REGULAR_SEASON = %(is_regular_season)s' % {
                        'stat': stat, 'name': name, 'is_regular_season': is_regular_season
                    }

    return sportvu_query

def get_synergy_player(name, date_1, date_2, last_n):

    synergy_query = 'SELECT gs.GAME_ID, STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") as DATE, ub.PLAYER_NAME as NAME, ub.TEAM_ABBREVIATION as TEAM, tb2.TEAM_ABBREVIATION as TEAM_AGAINST, syn.CUT_PossG, '\
            'syn.HANDOFF_PossG, syn.HANDOFF_PPP, syn.HANDOFF_FG, '\
            'syn.ISO_PossG, syn.ISO_PPP, syn.ISO_FG, '\
            'syn.MISC_PossG, syn.MISC_PPP, syn.MISC_FG, '\
            'syn.OFF_SCREEN_PossG, syn.OFF_SCREEN_PPP, syn.OFF_SCREEN_FG, '\
            'syn.POST_UP_PossG, syn.POST_UP_PPP, syn.POST_UP_FG, '\
            'syn.PR_HANDLER_PossG, syn.PR_HANDLER_PPP, syn.PR_HANDLER_FG, '\
            'syn.PR_ROLL_PossG, syn.PR_ROLL_PPP, syn.PR_ROLL_FG, '\
            'syn.PUT_BACK_PossG, syn.PUT_BACK_PPP, syn.PUT_BACK_FG, '\
            'syn.SPOT_UP_PossG, syn.SPOT_UP_PPP, syn.SPOT_UP_FG, '\
            'syn.TRANS_PossG, syn.TRANS_PPP, syn.TRANS_FG, '\
            'tb.FG3M*0.5 + tb.REB*1.25 + tb.AST*1.25 + tb.STL*2 + tb.BLK*2 + tb.TO*-0.5 + tb.PTS*1 as DK_POINTS '\
            'FROM usage_boxscores AS ub LEFT JOIN game_summary as gs ON gs.game_id = ub.game_id '\
            'LEFT JOIN traditional_boxscores as tb ON tb.game_id = ub.game_id AND tb.player_id = ub.player_id '\
            'INNER JOIN (SELECT tbt.game_id, tbt.TEAM_ABBREVIATION FROM traditional_boxscores_team as tbt) as tb2 ON tb2.game_id = ub.game_id and tb2.TEAM_ABBREVIATION != ub.TEAM_ABBREVIATION '\
            'INNER JOIN (SELECT game_id FROM traditional_boxscores WHERE player_name = "Jeremy Lin" ) as tb3 ON '\
                'tb3.game_id = ub.game_id AND STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") >= "%(date_begin)s" AND STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") <= "%(date_end)s" '\
            'INNER JOIN (SELECT scto.DATE, scto.TeamNameAbbreviation as TEAM_NAME, scto.GP, scto.PossG as CUT_PossG, scto.PPP as CUT_PPP, scto.FG as CUT_FG, '\
                'shto.PossG as HANDOFF_PossG, shto.PPP as HANDOFF_PPP, shto.FG as HANDOFF_FG, '\
                'sito.PossG as ISO_PossG, sito.PPP as ISO_PPP, sito.FG as ISO_FG, '\
                'smto.PossG as MISC_PossG, smto.PPP as MISC_PPP, smto.FG as MISC_FG, '\
                'sosto.PossG as OFF_SCREEN_PossG, sosto.PPP as OFF_SCREEN_PPP, sosto.FG as OFF_SCREEN_FG, '\
                'sputo.PossG as POST_UP_PossG, sputo.PPP as POST_UP_PPP, sputo.FG as POST_UP_FG, '\
                'spbhto.PossG as PR_HANDLER_PossG, spbhto.PPP as PR_HANDLER_PPP, spbhto.FG as PR_HANDLER_FG, '\
                'sprmto.PossG as PR_ROLL_PossG, sprmto.PPP as PR_ROLL_PPP, sprmto.FG as PR_ROLL_FG, '\
                'spbto.PossG as PUT_BACK_PossG, spbto.PPP as PUT_BACK_PPP, spbto.FG as PUT_BACK_FG , '\
                'ssuto.PossG as SPOT_UP_PossG, ssuto.PPP as SPOT_UP_PPP, ssuto.FG as SPOT_UP_FG, '\
                'stto.PossG as TRANS_PossG, stto.PPP as TRANS_PPP, stto.FG as TRANS_FG '\
                'FROM synergy_cut_team_offense AS scto LEFT JOIN synergy_handoff_team_offense AS shto ON '\
                    'scto.TEAM_ID = shto.TEAM_ID AND scto.DATE = shto.DATE AND scto.IS_REGULAR_SEASON = shto.IS_REGULAR_SEASON '\
                'LEFT JOIN synergy_isolation_team_offense AS sito ON '\
                    'scto.TEAM_ID = sito.TEAM_ID AND scto.DATE = sito.DATE AND scto.IS_REGULAR_SEASON = sito.IS_REGULAR_SEASON '\
                'LEFT JOIN synergy_misc_team_offense AS smto ON '\
                    'scto.TEAM_ID = smto.TEAM_ID AND scto.DATE = smto.DATE AND scto.IS_REGULAR_SEASON = smto.IS_REGULAR_SEASON '\
                'LEFT JOIN synergy_off_screen_team_offense AS sosto ON '\
                    'scto.TEAM_ID = sosto.TEAM_ID AND scto.DATE = sosto.DATE AND scto.IS_REGULAR_SEASON = sosto.IS_REGULAR_SEASON '\
                'LEFT JOIN synergy_post_up_team_offense AS sputo ON '\
                    'scto.TEAM_ID = sputo.TEAM_ID AND scto.DATE = sputo.DATE AND scto.IS_REGULAR_SEASON = sputo.IS_REGULAR_SEASON '\
                'LEFT JOIN synergy_pr_ball_handler_team_offense AS spbhto ON '\
                    'scto.TEAM_ID = spbhto.TEAM_ID AND scto.DATE = spbhto.DATE AND scto.IS_REGULAR_SEASON = spbhto.IS_REGULAR_SEASON '\
                'LEFT JOIN synergy_pr_roll_man_team_offense AS sprmto ON '\
                    'scto.TEAM_ID = sprmto.TEAM_ID AND scto.DATE = sprmto.DATE AND scto.IS_REGULAR_SEASON = sprmto.IS_REGULAR_SEASON '\
                'LEFT JOIN synergy_put_back_team_offense AS spbto ON '\
                    'scto.TEAM_ID = spbto.TEAM_ID AND scto.DATE = spbto.DATE AND scto.IS_REGULAR_SEASON = spbto.IS_REGULAR_SEASON '\
                'LEFT JOIN synergy_spot_up_team_offense AS ssuto ON '\
                    'scto.TEAM_ID = ssuto.TEAM_ID AND scto.DATE = ssuto.DATE AND scto.IS_REGULAR_SEASON = ssuto.IS_REGULAR_SEASON '\
                'LEFT JOIN synergy_transition_team_offense AS stto ON '\
                    'scto.TEAM_ID = stto.TEAM_ID AND scto.DATE = stto.DATE AND scto.IS_REGULAR_SEASON = stto.IS_REGULAR_SEASON '\
                    'WHERE scto.IS_REGULAR_SEASON = 1) as syn ON syn.DATE = STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") and syn.TEAM_NAME = tb2.TEAM_ABBREVIATION '\
                'WHERE ub.PLAYER_NAME = "%(name)s" ORDER BY DATE ' % {'date_format_year': DATE_FORMAT_YEAR, 'date_begin': date_1, 'date_end': date_2, 'name':name}

    if last_n != 0:
        synergy_query += 'DESC LIMIT %(last_n)s' % {'last_n': last_n}

    return synergy_query

def get_game_line(team, is_last_game, date_1, date_2):

    team_query = 'SELECT * FROM line_score '\
        'WHERE team_abbreviation = "%(team)s" ' % {
                'team': team
        }

    # last game
    if is_last_game == 1:
        team_query += 'AND game_id = (SELECT game_id FROM traditional_boxscores_team '\
        'WHERE TEAM_ABBREVIATION = "%(team)s" ORDER BY game_id DESC LIMIT 1)' % {
            'team': team
        }

    else:
        team_query += 'AND STR_TO_DATE(game_date_est,"%(date_format_year)s") >= "%(date_begin)s" '\
        'AND STR_TO_DATE(game_date_est,"%(date_format_year)s") <= "%(date_end)s" ' % {
            'date_format_year': DATE_FORMAT_YEAR, 'date_begin': date_1, 'date_end': date_2
        }

    return team_query

# last n games for team
def team_last_game(team, n):
    team_query = default_team_query()
    team_query += 'INNER JOIN (SELECT game_id FROM traditional_boxscores_team WHERE TEAM_ABBREVIATION = "%(team)s" ORDER BY game_id DESC LIMIT %(games)s ) as tb3 '\
                        'ON tb3.game_id = ab.game_id '\
                    'WHERE ab.TEAM_ABBREVIATION = "%(team)s"' % {'team': team, 'games': n}

    return team_query

# matchup results for team b/w dates
def team_direct_matchup(team, team_matchup, date_1, date_2):

    team_query = default_team_query()
    team_query += 'INNER JOIN (SELECT game_id FROM traditional_boxscores_team WHERE TEAM_ABBREVIATION = "%(team)s" ORDER BY game_id) as tb3 '\
                        'ON tb3.game_id = ab.game_id '\
                    'WHERE ab.TEAM_ABBREVIATION = "%(team)s" AND tb2.TEAM_ABBREVIATION = "%(team_matchup)s" '\
                    'AND STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") >= "%(date_begin)s" '\
                    'AND STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") <= "%(date_end)s" '\
                    'ORDER BY dk_points DESC' % {'date_format_year': DATE_FORMAT_YEAR, 'date_begin': date_1, 'date_end': date_2, 'team': team, 'team_matchup': team_matchup}
    return team_query


# team stats against specified team b/w dates
def team_against(team, date_1, date_2):

    team_query = default_team_query()
    team_query += 'INNER JOIN (SELECT game_id FROM traditional_boxscores_team WHERE TEAM_ABBREVIATION = "%(team)s" ORDER BY game_id) as tb3 '\
                        'ON tb3.game_id = ab.game_id '\
                    'WHERE tb2.TEAM_ABBREVIATION = "%(team)s" '\
                    'AND STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") >= "%(date_begin)s" '\
                    'AND STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") <= "%(date_end)s" '\
                    'ORDER BY DATE ASC' % {'date_format_year': DATE_FORMAT_YEAR, 'date_begin': date_1, 'date_end': date_2, 'team': team}
    return team_query


# last n games for player
def player_last_game(player, n):

    player_query = default_player_box_query()
    player_query += 'INNER JOIN (SELECT game_id FROM traditional_boxscores WHERE player_name = "%(player)s" ORDER BY game_id DESC LIMIT %(games)s ) as tb3 '\
                        'ON tb3.game_id = ub.game_id '\
                    'WHERE ub.PLAYER_NAME = "%(player)s"' % {'player': player, 'games': n}

    return player_query

# matchup results for player b/w dates based on the starting position
def player_last_matchups(player, date_1, date_2):

    player_query = default_player_box_query()
    player_query += 'WHERE ub.game_id IN (SELECT game_id FROM usage_boxscores WHERE player_name = "%(player)s") '\
                        'AND ub.start_position = (SELECT start_position FROM usage_boxscores WHERE player_name = "%(player)s" LIMIT 1) '\
                        'AND ub.player_name != "%(player)s" '\
                        'AND ub.team_abbreviation != (SELECT TEAM_ABBREVIATION FROM usage_boxscores WHERE player_name = "%(player)s" LIMIT 1) '\
                        'AND STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") >= "%(date_begin)s" '\
                        'AND STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") <= "%(date_end)s" '\
                        'ORDER BY dk_points DESC' % {'date_format_year': DATE_FORMAT_YEAR, 'date_begin': date_1, 'date_end': date_2, 'player': player}

    return player_query

# matchup results for player vs another player b/w dates
def player_direct_matchup(player, player_matchup, date_1, date_2):

    player_query = default_player_box_query()
    player_query += 'WHERE ub.game_id IN (SELECT game_id FROM usage_boxscores WHERE player_name = "%(player)s") '\
                        'AND ub.player_name = "%(player_matchup)s" '\
                        'AND STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") >= "%(date_begin)s" '\
                        'AND STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") <= "%(date_end)s" '\
                        'ORDER BY dk_points DESC' % {'date_format_year': DATE_FORMAT_YEAR, 'date_begin': date_1, 'date_end': date_2, 'player': player, 'player_matchup': player_matchup}

    return player_query

# matchup results for player vs another player b/w dates
def full_player_log(player, date_1, date_2, is_national, last_n):

    player_query = default_player_box_query()
    player_query += 'INNER JOIN (SELECT game_id FROM traditional_boxscores WHERE player_name = "%(player)s" ) as tb3 '\
                    'ON tb3.game_id = ub.game_id '\
                    'AND STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") >= "%(date_begin)s" '\
                    'AND STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") <= "%(date_end)s" '\
                    'WHERE ub.PLAYER_NAME = "%(player)s" ' % {'date_format_year': DATE_FORMAT_YEAR, 'player': player, 'date_begin': date_1, 'date_end': date_2}

    if is_national == 1:
        player_query += 'AND gs.NATL_TV_BROADCASTER_ABBREVIATION IS NOT NULL '


    if last_n != 0:
        player_query += 'ORDER BY DATE DESC LIMIT %(last_n)s' % {'last_n': last_n}


    return player_query

# query for either a player or team/s
def player_game_queries(date_1, date_2, is_player, teams):

    date_format_min = str("%i:%s")

    avg_player_query = 'SELECT gs.GAME_ID, '\
            'STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") as DATE, '\
            'ub.PLAYER_NAME as NAME, ub.TEAM_ABBREVIATION as TEAM, ub.START_POSITION, '\
            'ROUND(avg(ub.MIN), 4) as MIN, ROUND(avg(ub.USG_PCT), 4) as USG_PCT, ROUND(avg(ub.PCT_FGA), 4) as PCT_FGA, ROUND(avg(ub.PCT_FG3A), 4) as PCT_FG3A, '\
            'ROUND(avg(ub.PCT_FTA), 4) as PCT_FTA, ROUND(avg(ub.PCT_REB), 4) as PCT_REB, ROUND(avg(ub.PCT_AST), 4) as PCT_AST, ROUND(avg(ub.PCT_TOV), 4) as PCT_TOV, '\
            'ROUND(avg(ub.PCT_STL), 4) as PCT_STL, ROUND(avg(ub.PCT_BLK), 4) as PCT_BLK, ROUND(avg(ub.PCT_PF), 4) as PCT_PF, ROUND(avg(ub.PCT_PTS), 4) as PCT_PTS, '\
            'ROUND(avg(tb.FGA), 4) as FGA, ROUND(avg(tb.FG_PCT), 4) as FG_PCT, ROUND(avg(tb.FG3M), 4) as FG3M, ROUND(avg(tb.FG3A), 4) as FG3A, '\
            'ROUND(avg(tb.FG3_PCT), 4) as FG3_PCT, ROUND(avg(tb.FTA), 4) as FTA, ROUND(avg(tb.FT_PCT), 4) as FT_PCT, ROUND(avg(tb.FG3M), 4) as FG3M, '\
            'ROUND(avg(tb.REB), 4) as REB, ROUND(avg(tb.AST), 4) as AST, ROUND(avg(tb.STL), 4) as STL, ROUND(avg(tb.BLK), 4) as BLK, '\
            'ROUND(avg(tb.TO), 4) as TOV, ROUND(avg(tb.PF), 4) as PF, ROUND(avg(tb.PTS), 4) as PTS, ROUND(avg(tb.PLUS_MINUS), 4) as PLUS_MINUS, '\
            'ROUND(avg(tb.FG3M*0.5 + tb.REB*1.25 + tb.AST*1.25 + tb.STL*2 + tb.BLK*2 + tb.TO*-0.5 + tb.PTS*1), 4) as DK_POINTS, '\
            'ROUND(avg(ptb.RBC), 4) as REB_CHANCES, ROUND(avg(ptb.TCHS), 4) as TOUCHES, ROUND(avg(ptb.PASS), 4) as PASS, '\
            'ROUND(avg(ptb.AST) / avg(ptb.PASS), 4) as AST_PER_PASS, ROUND(avg(ptb.CFGA), 4) as CONTESTED_FGA, '\
            'ROUND(avg(ptb.CFG_PCT), 4) as CONTESTED_FG_PCT, ROUND(avg(ptb.FG_PCT), 4) as FG_PCT, '\
            'ROUND(avg(ab.OFF_RATING), 4) as OFF_RATING, ROUND(avg(ab.DEF_RATING), 4) as DEF_RATING, ROUND(avg(ab.NET_RATING), 4) as NET_RATING, '\
            'ROUND(avg(ab.AST_PCT), 4) as AST_PCT, ROUND(avg(ab.REB_PCT), 4) as REB_PCT, ROUND(avg(ab.EFG_PCT), 4) as EFG_PCT, '\
            'ROUND(avg(ab.USG_PCT), 4) as USG_PCT, ROUND(avg(ab.PACE), 4) as PACE, '\
            'ROUND(avg(sb.PCT_FGA_2PT), 4) as PCT_FGA_2PT, ROUND(avg(sb.PCT_FGA_3PT), 4) as PCT_FGA_3PT, ROUND(avg(sb.PCT_PTS_2PT), 4) as PCT_PTS_2PT, '\
            'ROUND(avg(sb.PCT_PTS_3PT), 4) as PCT_PTS_3PT, ROUND(avg(sb.PCT_PTS_OFF_TOV), 4) as PCT_PTS_OFF_TOV, ROUND(avg(sb.PCT_PTS_PAINT), 4) as PCT_PTS_PAINT, '\
            'count(ub.PLAYER_NAME) as NUM_GAMES '\
        'FROM usage_boxscores as ub '\
            'LEFT JOIN game_summary as gs '\
                'ON gs.game_id = ub.game_id '\
            'LEFT JOIN traditional_boxscores as tb '\
                'ON tb.game_id = ub.game_id AND tb.player_id = ub.player_id '\
            'LEFT JOIN player_tracking_boxscores as ptb '\
                'ON ptb.game_id = ub.game_id AND ptb.player_id = ub.player_id '\
            'LEFT JOIN advanced_boxscores as ab '\
                'ON ab.game_id = ub.game_id AND ab.player_id = ub.player_id '\
            'LEFT JOIN scoring_boxscores as sb '\
                'ON sb.game_id = ub.game_id AND sb.player_id = ub.player_id '\
        'WHERE STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") >= "%(date_begin)s" AND STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") <= "%(date_end)s" ' % {
            'date_format_year': DATE_FORMAT_YEAR, 'date_begin': date_1, 'date_end': date_2
            }

    # compare teams if passed
    if is_player == 1:
        avg_player_query += 'AND ub.PLAYER_NAME = "%(player)s" ' % {
            'player': teams,
        }
    else:
        avg_player_query += 'AND (ub.TEAM_ABBREVIATION = "%(team_one)s" OR ub.TEAM_ABBREVIATION = "%(team_two)s") ' % {
            'team_one': teams[0],
            'team_two': teams[1]
        }
    avg_player_query += 'GROUP BY NAME'

    return avg_player_query


def process_query_result(log_results, avg_results):

    for result in log_results:
        result['DATE'] = str(result['DATE'])
        if result['NAME'] in PLAYER_GAME_LOG:
            PLAYER_GAME_LOG[result['NAME']]['game_log'].append({
                'name': result['NAME'],
                'team': result['TEAM'],
                'date': result['DATE'],
                'starter': result['START_POSITION'],
                'data': result
            })
        else:
            PLAYER_GAME_LOG[result['NAME']] = {}
            PLAYER_GAME_LOG[result['NAME']]['game_log'] = []
            PLAYER_GAME_LOG[result['NAME']]['game_log'].append({
                'name': result['NAME'],
                'team': result['TEAM'],
                'date': result['DATE'],
                'starter': result['START_POSITION'],
                'data': result
            })

    for avg in avg_results:
        PLAYER_GAME_LOG[avg['NAME']]['avg'] = avg


def compare_team_stats(teams, threshold):
    diff_result = {}
    diff = 0
    team_one = teams[0]
    team_two = teams[1]

    # compare the two
    for stat in zip(team_one, team_two):
        stat = stat[0]
        if type(team_one[stat]) is not str:

            if team_one[stat] > team_two[stat]:
                diff = (team_two[stat] / team_one[stat]) * 100
            elif team_two[stat] > team_one[stat]:
                diff = (team_one[stat] / team_two[stat]) * 100
            else:
                diff = 100

            if diff <= threshold:
                diff_result[stat] = {
                    team_one['TEAM_NAME']: team_one[stat],
                    team_two['TEAM_NAME']: team_two[stat]
                }

    return diff_result


def compare_player_stats(result_season, result_playoffs, threshold):

    diff_result = {}
    diff = 0

    temp_hash = {}
    # put all data in a temp hash for players
    # this is done to make sure all the names match
    for stat in result_season:
        temp_hash[stat['NAME']] = {
            'season': stat,
            'playoffs': {}
        }

    for stat in result_playoffs:
        if stat['NAME'] in temp_hash:
            temp_hash[stat['NAME']]['playoffs'] = stat
        else:
            temp_hash[stat['NAME']] = {
                'season': {},
                'playoffs': stat
            }

    for players in temp_hash:
        for stat in zip(temp_hash[players]['playoffs'], temp_hash[players]['season']):
            stat = stat[0]
            if type(temp_hash[players]['playoffs'][stat]) is not str:
                if temp_hash[players]['playoffs'][stat] > temp_hash[players]['season'][stat]:
                    diff = (temp_hash[players]['season'][stat] / temp_hash[players]['playoffs'][stat]) * 100
                elif temp_hash[players]['season'][stat] > temp_hash[players]['playoffs'][stat]:
                    diff = (temp_hash[players]['playoffs'][stat] / temp_hash[players]['season'][stat]) * 100
                else:
                    diff = 100
                if diff <= threshold:
                    if players in diff_result:
                        diff_result[players][stat] = {
                            'playoffs': temp_hash[players]['playoffs'][stat],
                            'season': temp_hash[players]['season'][stat]
                        }
                    else:
                        diff_result[players] = {
                            stat: {
                                'playoffs': temp_hash[players]['playoffs'][stat],
                                'season': temp_hash[players]['season'][stat]
                            }
                        }

    return diff_result

# shot_made: int
# shot_distance, shot_zone_basic, shot_zone_area
def shot_selection(query_type, name, shot_made, column, last_n):
    query_dict = {
        'query_for': ''
    }

    if query_type == 'player':
        query_dict['query_for'] = 'PLAYER_NAME'
        query_type = ''
    else:
        # there need to be a translation for the team neam
        name = TEAMS_DICT[name]
        query_dict['query_for'] = 'TEAM_NAME'
        query_type = '_team'

    shot_query = 'SELECT %(query_for)s as NAME, %(column)s, COUNT(%(column)s) as NUM_ACTIONS '\
        'FROM shots ' % {'query_for': query_dict['query_for'], 'column': column}

    if last_n != 0:
        shot_query += 'INNER JOIN (SELECT game_id FROM traditional_boxscores%(query_type)s WHERE %(query_for)s = "%(name)s" '\
                'ORDER BY game_id DESC LIMIT %(last_n)s ) as tb3 ON tb3.game_id = shots.game_id ' % {
                    'name': name, 'query_for': query_dict['query_for'], 'query_type': query_type, 'last_n': last_n
                }

    shot_query += 'WHERE %(query_for)s = "%(name)s" '\
        'AND SHOT_MADE_FLAG = %(shot_made)s '\
        'GROUP BY %(column)s '\
        'ORDER BY COUNT(%(column)s) DESC' % {'name': name, 'shot_made': shot_made, 'column': column, 'query_for': query_dict['query_for']}

    return shot_query


# last_n
def shot_selection_time(query_type, name, shot_made, last_n):
    query_dict = {
        'query_for': ''
    }

    if query_type == 'player':
        query_dict['query_for'] = 'PLAYER_NAME'
        query_type = ''
    else:
        name = TEAMS_DICT[name]
        query_dict['query_for'] = 'TEAM_NAME'
        query_type = '_team'

    shot_query = 'SELECT %(query_for)s as NAME, PERIOD, MINUTES_REMAINING, COUNT(PERIOD) as NUM_ACTIONS '\
        'FROM shots ' % {'query_for': query_dict['query_for']}

    if last_n != 0:
        shot_query += 'INNER JOIN (SELECT game_id FROM traditional_boxscores%(query_type)s WHERE %(query_for)s = "%(name)s" '\
                'ORDER BY game_id DESC LIMIT %(last_n)s ) as tb3 ON tb3.game_id = shots.game_id ' % {
                    'name': name, 'query_for': query_dict['query_for'], 'query_type': query_type, 'last_n': last_n
                }

    shot_query += 'WHERE %(query_for)s = "%(name)s" '\
        'AND SHOT_MADE_FLAG = %(shot_made)s '\
        'GROUP BY PERIOD, MINUTES_REMAINING '\
        'ORDER BY COUNT(PERIOD) DESC' % {'name': name, 'shot_made': shot_made, 'query_for': query_dict['query_for']}

    return shot_query

# split into teams and player
def shot_selection_type_detailed(name, shot_made, last_n):

    shot_query = 'SELECT PLAYER_NAME as NAME, SHOT_TYPE, SHOT_ZONE_AREA, SHOT_ZONE_BASIC, CONCAT(SHOT_ZONE_BASIC, ", ", SHOT_ZONE_AREA) as SHOT_LOCATION, COUNT(SHOT_ZONE_AREA) as NUM_ACTIONS FROM shots '

    if last_n != 0:
        shot_query += 'INNER JOIN (SELECT game_id FROM traditional_boxscores WHERE PLAYER_NAME = "%(name)s" '\
                'ORDER BY game_id DESC LIMIT %(last_n)s ) as tb3 ON tb3.game_id = shots.game_id ' % {
                    'name': name, 'last_n': last_n
                }

    shot_query += 'WHERE PLAYER_NAME = "%(name)s" '\
        'AND SHOT_MADE_FLAG = %(shot_made)s '\
        'GROUP BY SHOT_ZONE_AREA, SHOT_ZONE_BASIC, SHOT_TYPE '\
        'ORDER BY NUM_ACTIONS DESC' % {'name': name, 'shot_made': shot_made}

    return shot_query

# split into teams and player
def shot_selection_type_detailed_team(name, shot_made, last_n):

    shot_query = 'SELECT TEAM_NAME, SHOT_TYPE, SHOT_ZONE_AREA, SHOT_ZONE_BASIC, CONCAT(SHOT_ZONE_BASIC, ", ", SHOT_ZONE_AREA) as SHOT_LOCATION, COUNT(SHOT_ZONE_AREA) as NUM_ACTIONS FROM shots '

    if last_n != 0:
        shot_query += 'INNER JOIN (SELECT game_id FROM traditional_boxscores_team WHERE CONCAT(TEAM_CITY, " ", TEAM_NAME) = "%(name)s" '\
                'ORDER BY game_id DESC LIMIT %(last_n)s ) as tb3 ON tb3.game_id = shots.game_id ' % {
                    'name': name, 'last_n': last_n
                }

    shot_query += 'WHERE TEAM_NAME = "%(name)s" '\
        'AND SHOT_MADE_FLAG = %(shot_made)s '\
        'GROUP BY SHOT_ZONE_AREA, SHOT_ZONE_BASIC, SHOT_TYPE '\
        'ORDER BY NUM_ACTIONS DESC' % {'name': name, 'shot_made': shot_made}

    print shot_query
    return shot_query


def player_pass_made(name, is_regular_season):

    name = reverse_name(name)

    # -- pass/FGA i want to know how many times the player shoots when he is passed the ball
    pass_query = 'SELECT PASS_TO, FREQUENCY, PASS, AST as AST_MADE, ROUND(AST/PASS,4) as AST_MADE_PER_PASS, ROUND(FGA/PASS,4) as FGA_CREATED_PER_PASS, FG_PCT, FG2A, FG3A '\
            'FROM player_tracking_passes_made '\
            'WHERE is_regular_season = %(is_regular_season)s AND player_name_last_first = "%(name)s" '\
            'ORDER BY FREQUENCY DESC' % {'name': name, 'is_regular_season': is_regular_season}

    return pass_query

def player_pass_received(name, is_regular_season):

    name = reverse_name(name)

    # -- pass/FGA i want to know how many times the player shoots when he is passed the ball
    pass_query = 'SELECT PASS_FROM, FREQUENCY, PASS, AST as AST_CREATED, ROUND(AST/PASS,4) as AST_CREATED_PER_PASS, ROUND(FGA/PASS,4) as FGA_FROM_PASS, FG_PCT, FG2A, FG3A '\
            'FROM player_tracking_passes_received '\
            'WHERE is_regular_season = %(is_regular_season)s AND player_name_last_first = "%(name)s" '\
            'ORDER BY FREQUENCY DESC' % {'name': name, 'is_regular_season': is_regular_season}

    return pass_query


def reverse_name(name):
    # translate the game in correct format for query
    # Last, First
    split_name = name.split(' ')
    temp = split_name[0]
    split_name[0] = split_name[1]
    split_name[1] = temp

    return split_name[0] + ', ' + split_name[1]


def execute_query(sql_query):
    query_result = None

    try:
        db = MySQLdb.connect("127.0.0.1","root","","nba_scrape", conv=conv)

        # prepare a cursor object using cursor() method
        cursor = db.cursor()
        # Execute the SQL command
        cursor.execute(sql_query)
        query_result = [dict(line) for line in [zip([column[0] for column in cursor.description],
                     row) for row in cursor.fetchall()]]
    except:
        print "Error: unable to fetch data"

    return query_result

def write_to_csv(sql_query, source, name):

    try:
        db = MySQLdb.connect("127.0.0.1","root","","nba_scrape", conv=conv)

        # prepare a cursor object using cursor() method
        cursor = db.cursor()
        # Execute the SQL command
        cursor.execute(sql_query)
        header = []
        for column in cursor.description:
            header.append(column[0])
        rows = cursor.fetchall()

        with open('nba_scrape/'+ source +'/'+ name +'.csv', 'wb') as f:
            myFile = csv.writer(f)
            # write to the header
            myFile.writerow(header)
            myFile.writerows(rows)

    except:
        print "Error: unable to fetch data"

def get_shot_detailed_team():
    shot_detailed_team_dict = {}
    for team, team_name in TEAMS_DICT.iteritems():

        shot_detailed_team_dict[team] = {}
        # last game
        shot_detailed_team_dict[team]['Last 1'] = format_to_json(execute_query(shot_selection_type_detailed_team(team_name, 1, 1)), 'SHOT_LOCATION')
        # last 3 games
        shot_detailed_team_dict[team]['Last 3'] = format_to_json(execute_query(shot_selection_type_detailed_team(team_name, 1, 3)), 'SHOT_LOCATION')
        # all
        shot_detailed_team_dict[team]['All'] = format_to_json(execute_query(shot_selection_type_detailed_team(team_name, 1, 0)), 'SHOT_LOCATION')

    with open('../scrape/json_files/shots/shot_selection_type_detailed_team_data.json', 'w') as outfile:
        logger.info('Writing synergy to json file: shot_selection_type_detailed_team_data')
        json.dump(shot_detailed_team_dict, outfile)


def player_shot_types_general(name, date, is_regular_season):

    name = reverse_name(name)

    # -- pass/FGA i want to know how many times the player shoots when he is passed the ball
    pass_query = 'SELECT GP, SHOT_TYPE, FGA_FREQUENCY, FGM, FGA, FG_PCT, EFG_PCT, FG2A_FREQUENCY, FG2M, FG2A, FG2_PCT, FG3A_FREQUENCY, FG3M, FG3A, FG3_PCT '\
            'FROM player_tracking_shots_general '\
            'WHERE is_regular_season = %(is_regular_season)s AND player_name_last_first = "%(name)s" AND DATE = "%(date)s" '\
            'ORDER BY FGA_FREQUENCY DESC' % {'name': name, 'is_regular_season': is_regular_season, 'date': date}

    return pass_query

def player_shot_types_defender(name, date, is_regular_season):

    name = reverse_name(name)

    # -- pass/FGA i want to know how many times the player shoots when he is passed the ball
    pass_query = 'SELECT GP, CLOSE_DEF_DIST_RANGE, FGA_FREQUENCY, FGM, FGA, FG_PCT, EFG_PCT, FG2A_FREQUENCY, FG2M, FG2A, FG2_PCT, FG3A_FREQUENCY, FG3M, FG3A, FG3_PCT '\
            'FROM player_tracking_shots_defender '\
            'WHERE is_regular_season = %(is_regular_season)s AND player_name_last_first = "%(name)s" AND DATE = "%(date)s" '\
            'ORDER BY FGA_FREQUENCY DESC' % {'name': name, 'is_regular_season': is_regular_season, 'date': date}

    return pass_query

def player_shot_types_defender_ten(name, date, is_regular_season):

    name = reverse_name(name)

    # -- pass/FGA i want to know how many times the player shoots when he is passed the ball
    pass_query = 'SELECT GP, CLOSE_DEF_DIST_RANGE, FGA_FREQUENCY, FGM, FGA, FG_PCT, EFG_PCT, FG2A_FREQUENCY, FG2M, FG2A, FG2_PCT, FG3A_FREQUENCY, FG3M, FG3A, FG3_PCT '\
            'FROM player_tracking_shots_defender_ten '\
            'WHERE is_regular_season = %(is_regular_season)s AND player_name_last_first = "%(name)s" AND DATE = "%(date)s" '\
            'ORDER BY FGA_FREQUENCY DESC' % {'name': name, 'is_regular_season': is_regular_season, 'date': date}

    return pass_query

def player_shot_types_dribble(name, date, is_regular_season):

    name = reverse_name(name)

    # -- pass/FGA i want to know how many times the player shoots when he is passed the ball
    pass_query = 'SELECT GP, DRIBBLE_RANGE, FGA_FREQUENCY, FGM, FGA, FG_PCT, EFG_PCT, FG2A_FREQUENCY, FG2M, FG2A, FG2_PCT, FG3A_FREQUENCY, FG3M, FG3A, FG3_PCT '\
            'FROM player_tracking_shots_dribble '\
            'WHERE is_regular_season = %(is_regular_season)s AND player_name_last_first = "%(name)s" AND DATE = "%(date)s" '\
            'ORDER BY FGA_FREQUENCY DESC' % {'name': name, 'is_regular_season': is_regular_season, 'date': date}

    return pass_query

def player_shot_types_shot_clock(name, date, is_regular_season):

    name = reverse_name(name)

    # -- pass/FGA i want to know how many times the player shoots when he is passed the ball
    pass_query = 'SELECT GP, SHOT_CLOCK_RANGE, FGA_FREQUENCY, FGM, FGA, FG_PCT, EFG_PCT, FG2A_FREQUENCY, FG2M, FG2A, FG2_PCT, FG3A_FREQUENCY, FG3M, FG3A, FG3_PCT '\
            'FROM player_tracking_shots_shot_clock '\
            'WHERE is_regular_season = %(is_regular_season)s AND player_name_last_first = "%(name)s" AND DATE = "%(date)s" '\
            'ORDER BY FGA_FREQUENCY DESC' % {'name': name, 'is_regular_season': is_regular_season, 'date': date}

    return pass_query


def player_shot_types_touch_time(name, date, is_regular_season):

    name = reverse_name(name)

    # -- pass/FGA i want to know how many times the player shoots when he is passed the ball
    pass_query = 'SELECT GP, TOUCH_TIME_RANGE, FGA_FREQUENCY, FGM, FGA, FG_PCT, EFG_PCT, FG2A_FREQUENCY, FG2M, FG2A, FG2_PCT, FG3A_FREQUENCY, FG3M, FG3A, FG3_PCT '\
            'FROM player_tracking_shots_touch_time '\
            'WHERE is_regular_season = %(is_regular_season)s AND player_name_last_first = "%(name)s" AND DATE = "%(date)s" '\
            'ORDER BY FGA_FREQUENCY DESC' % {'name': name, 'is_regular_season': is_regular_season, 'date': date}

    return pass_query

# http://stats.nba.com/stats/teamdashptshots?DateFrom=&DateTo=&GameSegment=&LastNGames=0&LeagueID=00&Location=&MeasureType=Base&Month=0&OpponentTeamID=0&Outcome=&PaceAdjust=N&PerMode=PerGame&Period=0&PlusMinus=N&Rank=N&Season=2015-16&SeasonSegment=&SeasonType=Playoffs&TeamID=1610612738&VsConference=&VsDivision=

def test():
    # query = 'SELECT gs.GAME_ID, STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") as DATE, ub.PLAYER_NAME as NAME, ub.TEAM_ABBREVIATION as TEAM, '\
    # 'tb2.TEAM_ABBREVIATION as TEAM_AGAINST, ub.START_POSITION, ub.MIN, tb.FTA, tb4.avgPF FROM usage_boxscores as ub '\
    # 'LEFT JOIN game_summary as gs ON gs.game_id = ub.game_id LEFT JOIN traditional_boxscores as tb ON tb.game_id = ub.game_id AND tb.player_id = ub.player_id '\
    # 'LEFT JOIN player_tracking_boxscores as ptb ON ptb.game_id = ub.game_id AND ptb.player_id = ub.player_id '\
    # 'LEFT JOIN advanced_boxscores as ab ON ab.game_id = ub.game_id AND ab.player_id = ub.player_id '\
    # 'LEFT JOIN scoring_boxscores as sb ON sb.game_id = ub.game_id AND sb.player_id = ub.player_id '\
    # 'LEFT JOIN four_factors_boxscores as ff ON ff.game_id = ub.game_id AND ff.player_id = ub.player_id '\
    # 'LEFT JOIN misc_boxscores as mb ON mb.game_id = ub.game_id AND mb.player_id = ub.player_id '\
    # 'INNER JOIN (SELECT tbt.game_id, tbt.TEAM_ABBREVIATION FROM traditional_boxscores_team as tbt) as tb2 '\
    #     'ON tb2.game_id = ub.game_id and tb2.TEAM_ABBREVIATION != ub.TEAM_ABBREVIATION '\
    #     'INNER JOIN (SELECT game_id FROM traditional_boxscores WHERE player_name = "DeMar DeRozan" ) as tb3 '\
    #     'ON tb3.game_id = ub.game_id AND STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") >= "2015-10-27" AND STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") <= "2016-04-15" '\
    #     'INNER JOIN (select tb.TEAM_ABBREVIATION as TEAM, avg(tb.PF) as avgPF FROM `traditional_boxscores_team` as tb GROUP BY TEAM) as tb4 ON tb4.TEAM = tb2.TEAM_ABBREVIATION WHERE ub.PLAYER_NAME = "DeMar DeRozan" and ub.MIN >= 20' % {'date_format_year': DATE_FORMAT_YEAR}

    # query = 'select ptb.MIN, ptb.REB, ptb.OREB, ptb.OREB_CHANCES, ptb.OREB_CHANCE_PCT_ADJ, ptb.REB_CHANCES, ptb.REB_CHANCE_PCT_ADJ, tb2.TEAM_ABBREVIATION as TEAM_AGAINST, tb4.avgFGA, ab.avgPace from `sportvu_rebounding_game_logs` as ptb INNER JOIN (SELECT tbt.game_id, tbt.TEAM_ABBREVIATION FROM traditional_boxscores_team as tbt) as tb2 ON tb2.game_id = ptb.game_id and tb2.TEAM_ABBREVIATION != ptb.TEAM_ABBREVIATION INNER JOIN (select tb.TEAM_ABBREVIATION as TEAM, avg(tb.FGA) as avgFGA FROM `traditional_boxscores_team` as tb GROUP BY TEAM) as tb4 ON tb4.TEAM = tb2.TEAM_ABBREVIATION INNER JOIN (select ab.TEAM_ABBREVIATION as TEAM, avg(ab.pace) as avgPace FROM `advanced_boxscores_team` as ab GROUP BY TEAM) as ab on ab.TEAM = tb2.TEAM_ABBREVIATION where ptb.player_name = "Bismack Biyombo" and ptb.MIN <= 30 and ptb.MIN >= 20'

    # When face against a BIG. For example, Rudy Gobert. Do drives, paint points affect player behavior?
    query = 'SELECT STR_TO_DATE(gs.game_date_est,"%Y-%m-%d") as DATE, ub.PLAYER_NAME as NAME, ub.TEAM_ABBREVIATION as TEAM_NAME, tb2.TEAM_ABBREVIATION as TEAM_AGAINST, ub.START_POSITION, ub.MIN, ub.USG_PCT, ub.PCT_FTA, ub.PCT_PTS, tb.FGA, tb.FG_PCT, tb.FG3A, tb.FTA, tb.FT_PCT,tb.PTS, tb.PLUS_MINUS, tb.FG3M*0.5 + tb.REB*1.25+tb.AST*1.25+tb.STL*2+tb.BLK*2+tb.TO*-0.5+tb.PTS*1 as DK_POINTS, mb.PTS_PAINT, mb.PFD, dgl.DRIVES, ptb.TCHS as TOUCHES, ptb.CFGA as CONTESTED_FGA, ptb.CFG_PCT as CONTESTED_FG_PCT, ab.OFF_RATING, ab.DEF_RATING, ab.PACE, sb.PCT_PTS_PAINT, sb.PCT_AST_FGM, sb.PCT_UAST_FGM, mb.PTS_2ND_CHANCE,  gs.NATL_TV_BROADCASTER_ABBREVIATION as NATIONAL_TV FROM usage_boxscores as ub LEFT JOIN game_summary as gs ON gs.game_id = ub.game_id LEFT JOIN traditional_boxscores as tb ON tb.game_id = ub.game_id AND tb.player_id = ub.player_id LEFT JOIN player_tracking_boxscores as ptb ON ptb.game_id = ub.game_id AND ptb.player_id = ub.player_id LEFT JOIN advanced_boxscores as ab ON ab.game_id = ub.game_id AND ab.player_id = ub.player_id LEFT JOIN scoring_boxscores as sb ON sb.game_id = ub.game_id AND sb.player_id = ub.player_id LEFT JOIN four_factors_boxscores as ff ON ff.game_id = ub.game_id AND ff.player_id = ub.player_id LEFT JOIN misc_boxscores as mb ON mb.game_id = ub.game_id AND mb.player_id = ub.player_id INNER JOIN (SELECT tbt.game_id, tbt.TEAM_ABBREVIATION FROM traditional_boxscores_team as tbt) as tb2 ON tb2.game_id = ub.game_id and tb2.TEAM_ABBREVIATION != ub.TEAM_ABBREVIATION AND STR_TO_DATE(gs.game_date_est,"%Y-%m-%d") >= "2015-10-27" AND STR_TO_DATE(gs.game_date_est,"%Y-%m-%d") <= "2016-04-15" LEFT JOIN sportvu_drives_game_logs as dgl ON dgl.game_id = ub.game_id AND dgl.player_id = ub.player_id WHERE tb2.TEAM_ABBREVIATION = "UTA" and ub.MIN >= 20 and ub.START_POSITION = "G" order by mb.PTS_PAINT DESC'

    print query
    return query

# test()
# print test()
# write_to_csv(test(), 'test', 'againstUTA')

def get_data_against_based_on_position():
    db_team_names = ['BKN', 'POR', 'CHI', 'OKC', 'HOU', 'LAC', 'NOP', 'DEN', 'CLE', 'ORL', 'MIN', 'SAS', 'TOR', 'NYK', 'PHX', 'ATL', 'LAL', 'IND', 'WAS', 'BOS', 'PHI', 'MEM', 'MIA', 'DAL', 'UTA', 'CHA', 'SAC', 'GSW', 'DET', 'MIL']
    # for each team and position
    for team in db_team_names:
        for position in POSITIONS:
            query = 'SELECT STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") as DATE, ub.PLAYER_NAME as NAME, ub.TEAM_ABBREVIATION as TEAM_NAME, tb2.TEAM_ABBREVIATION as TEAM_AGAINST, '\
            'ub.START_POSITION, ub.MIN, ub.USG_PCT, ub.PCT_FTA, ub.PCT_PTS, tb.FGA, tb.FG_PCT, tb.FG3A, tb.FTA, tb.FT_PCT,tb.PTS, tb.PLUS_MINUS, '\
            'tb.FG3M*0.5 + tb.REB*1.25+tb.AST*1.25+tb.STL*2+tb.BLK*2+tb.TO*-0.5+tb.PTS*1 as DK_POINTS, mb.PTS_PAINT, mb.PFD, dgl.DRIVES, ptb.TCHS as TOUCHES, '\
            'ptb.CFGA as CONTESTED_FGA, ptb.CFG_PCT as CONTESTED_FG_PCT, ab.OFF_RATING, ab.DEF_RATING, ab.PACE, sb.PCT_PTS_PAINT, sb.PCT_AST_FGM, sb.PCT_UAST_FGM, mb.PTS_2ND_CHANCE, '\
            'gs.NATL_TV_BROADCASTER_ABBREVIATION as NATIONAL_TV FROM usage_boxscores as ub LEFT JOIN game_summary as gs ON gs.game_id = ub.game_id '\
            'LEFT JOIN traditional_boxscores as tb ON tb.game_id = ub.game_id AND tb.player_id = ub.player_id '\
            'LEFT JOIN player_tracking_boxscores as ptb ON ptb.game_id = ub.game_id AND ptb.player_id = ub.player_id '\
            'LEFT JOIN advanced_boxscores as ab ON ab.game_id = ub.game_id AND ab.player_id = ub.player_id '\
            'LEFT JOIN scoring_boxscores as sb ON sb.game_id = ub.game_id AND sb.player_id = ub.player_id '\
            'LEFT JOIN four_factors_boxscores as ff ON ff.game_id = ub.game_id AND ff.player_id = ub.player_id '\
            'LEFT JOIN misc_boxscores as mb ON mb.game_id = ub.game_id AND mb.player_id = ub.player_id '\
            'INNER JOIN (SELECT tbt.game_id, tbt.TEAM_ABBREVIATION FROM traditional_boxscores_team as tbt) as tb2 ON tb2.game_id = ub.game_id '\
                'AND tb2.TEAM_ABBREVIATION != ub.TEAM_ABBREVIATION AND STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") >= "2015-10-27" '\
                'AND STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") <= "2016-04-15" '\
                'LEFT JOIN sportvu_drives_game_logs as dgl ON dgl.game_id = ub.game_id AND dgl.player_id = ub.player_id '\
            'WHERE tb2.TEAM_ABBREVIATION = "%(team)s" and ub.MIN >= 20 and ub.START_POSITION = "%(position)s" order by mb.PTS_PAINT DESC' % {'team': team, 'position': position, 'date_format_year': DATE_FORMAT_YEAR}
            filename = 'players_against_%(team)s_%(position)s' % {'team': team, 'position': position}
            write_to_csv(query, 'test', filename)


def get_synergy_wrt_dk(name):
    query = 'SELECT tb.GAME_ID, tb.PLAYER_NAME, tb2.TEAM_ABBREVIATION as TEAM_AGAINST, '\
            'sctd.PossG as CUT_PossG, sctd.PPP as CUT_PPP, sctd.FG as CUT_FG, '\
            'shtd.PossG as HANDOFF_PossG, shtd.PPP as HANDOFF_PPP, shtd.FG as HANDOFF_FG, '\
            'sitd.PossG as ISO_PossG, sitd.PPP as ISO_PPP, sitd.FG as ISO_FG, '\
            'smtd.PossG as MISC_PossG, smtd.PPP as MISC_PPP, smtd.FG as MISC_FG, '\
            'sostd.PossG as OFF_SCREEN_PossG, sostd.PPP as OFF_SCREEN_PPP, sostd.FG as OFF_SCREEN_FG, '\
            'sputd.PossG as POST_UP_PossG, sputd.PPP as POST_UP_PPP, sputd.FG as POST_UP_FG, '\
            'tb.FG3M*0.5 + tb.REB*1.25+tb.AST*1.25+tb.STL*2+tb.BLK*2+tb.TO*-0.5+tb.PTS*1 as DK_POINTS FROM `traditional_boxscores` as tb  '\
            'INNER JOIN (SELECT tbt.game_id, tbt.TEAM_ABBREVIATION FROM traditional_boxscores_team as tbt) as tb2 ON tb2.game_id = tb.game_id and tb2.TEAM_ABBREVIATION != tb.TEAM_ABBREVIATION '\
            'INNER JOIN (SELECT TeamName as NAME, TeamNameAbbreviation as TEAM_NAME, GP, ROUND(PossG,2) as POSSG, ROUND(PPP,4) as PPP, ROUND(FG,2) as FG, BetterPPP+1 as PPP_RANK '\
                'FROM synergy_cut_team_defense as V WHERE DATE = "2016-04-15" ORDER BY PossG DESC) as sctd ON sctd.TEAM_NAME = tb2.TEAM_ABBREVIATION '\
            'INNER JOIN (SELECT TeamName as NAME, TeamNameAbbreviation as TEAM_NAME, GP, ROUND(PossG,2) as POSSG, ROUND(PPP,4) as PPP, ROUND(FG,2) as FG, BetterPPP+1 as PPP_RANK '\
                'FROM synergy_handoff_team_defense as V WHERE DATE = "2016-04-15" ORDER BY PossG DESC) as shtd ON shtd.TEAM_NAME = tb2.TEAM_ABBREVIATION '\
            'INNER JOIN (SELECT TeamName as NAME, TeamNameAbbreviation as TEAM_NAME, GP, ROUND(PossG,2) as POSSG, ROUND(PPP,4) as PPP, ROUND(FG,2) as FG, BetterPPP+1 as PPP_RANK '\
                'FROM synergy_isolation_team_defense as V WHERE DATE = "2016-04-15" ORDER BY PossG DESC) as sitd ON sitd.TEAM_NAME = tb2.TEAM_ABBREVIATION '\
            'INNER JOIN (SELECT TeamName as NAME, TeamNameAbbreviation as TEAM_NAME, GP, ROUND(PossG,2) as POSSG, ROUND(PPP,4) as PPP, ROUND(FG,2) as FG, BetterPPP+1 as PPP_RANK '\
                'FROM synergy_misc_team_defense as V WHERE DATE = "2016-04-15" ORDER BY PossG DESC) as smtd ON smtd.TEAM_NAME = tb2.TEAM_ABBREVIATION '\
            'INNER JOIN (SELECT TeamName as NAME, TeamNameAbbreviation as TEAM_NAME, GP, ROUND(PossG,2) as POSSG, ROUND(PPP,4) as PPP, ROUND(FG,2) as FG, BetterPPP+1 as PPP_RANK '\
                'FROM synergy_off_screen_team_defense as V WHERE DATE = "2016-04-15" ORDER BY PossG DESC) as sostd ON sostd.TEAM_NAME = tb2.TEAM_ABBREVIATION '\
            'INNER JOIN (SELECT TeamName as NAME, TeamNameAbbreviation as TEAM_NAME, GP, ROUND(PossG,2) as POSSG, ROUND(PPP,4) as PPP, ROUND(FG,2) as FG, BetterPPP+1 as PPP_RANK '\
                'FROM synergy_post_up_team_defense as V WHERE DATE = "2016-04-15" ORDER BY PossG DESC) as sputd ON sputd.TEAM_NAME = tb2.TEAM_ABBREVIATION '\
            'WHERE PLAYER_NAME = "%(name)s"' % {'name': name}

    query_two = 'SELECT tb.GAME_ID, tb.PLAYER_NAME, tb2.TEAM_ABBREVIATION as TEAM_AGAINST, '\
                'spbhtd.PossG as PR_HANDLER_PossG, spbhtd.PPP as PR_HANDLER_PPP, spbhtd.FG as PR_HANDLER_FG, '\
                'sprmtd.PossG as PR_ROLL_PossG, sprmtd.PPP as PR_ROLL_PPP, sprmtd.FG as PR_ROLL_FG, '\
                'spbtd.PossG as PUT_BACK_PossG, spbtd.PPP as PUT_BACK_PPP, spbtd.FG as PUT_BACK_FG , '\
                'ssutd.PossG as SPOT_UP_PossG, ssutd.PPP as SPOT_UP_PPP, ssutd.FG as SPOT_UP_FG, '\
                'sttd.PossG as TRANS_PossG, sttd.PPP as TRANS_PPP, sttd.FG as TRANS_FG, '\
                'tb.FG3M*0.5 + tb.REB*1.25+tb.AST*1.25+tb.STL*2+tb.BLK*2+tb.TO*-0.5+tb.PTS*1 as DK_POINTS FROM `traditional_boxscores` as tb  '\
                'INNER JOIN (SELECT tbt.game_id, tbt.TEAM_ABBREVIATION FROM traditional_boxscores_team as tbt) as tb2 ON tb2.game_id = tb.game_id and tb2.TEAM_ABBREVIATION != tb.TEAM_ABBREVIATION '\
                'INNER JOIN (SELECT TeamName as NAME, TeamNameAbbreviation as TEAM_NAME, GP, ROUND(PossG,2) as POSSG, ROUND(PPP,4) as PPP, ROUND(FG,2) as FG, BetterPPP+1 as PPP_RANK '\
                    'FROM synergy_pr_ball_handler_team_defense as V WHERE DATE = "2016-04-15" ORDER BY PossG DESC) as spbhtd ON spbhtd.TEAM_NAME = tb2.TEAM_ABBREVIATION '\
                'INNER JOIN (SELECT TeamName as NAME, TeamNameAbbreviation as TEAM_NAME, GP, ROUND(PossG,2) as POSSG, ROUND(PPP,4) as PPP, ROUND(FG,2) as FG, BetterPPP+1 as PPP_RANK '\
                    'FROM synergy_pr_roll_man_team_defense as V WHERE DATE = "2016-04-15" ORDER BY PossG DESC) as sprmtd ON sprmtd.TEAM_NAME = tb2.TEAM_ABBREVIATION '\
                'INNER JOIN (SELECT TeamName as NAME, TeamNameAbbreviation as TEAM_NAME, GP, ROUND(PossG,2) as POSSG, ROUND(PPP,4) as PPP, ROUND(FG,2) as FG, BetterPPP+1 as PPP_RANK '\
                    'FROM synergy_put_back_team_defense as V WHERE DATE = "2016-04-15" ORDER BY PossG DESC) as spbtd ON spbtd.TEAM_NAME = tb2.TEAM_ABBREVIATION '\
                'INNER JOIN (SELECT TeamName as NAME, TeamNameAbbreviation as TEAM_NAME, GP, ROUND(PossG,2) as POSSG, ROUND(PPP,4) as PPP, ROUND(FG,2) as FG, BetterPPP+1 as PPP_RANK '\
                    'FROM synergy_spot_up_team_defense as V WHERE DATE = "2016-04-15" ORDER BY PossG DESC) as ssutd ON ssutd.TEAM_NAME = tb2.TEAM_ABBREVIATION '\
                'INNER JOIN (SELECT TeamName as NAME, TeamNameAbbreviation as TEAM_NAME, GP, ROUND(PossG,2) as POSSG, ROUND(PPP,4) as PPP, ROUND(FG,2) as FG, BetterPPP+1 as PPP_RANK '\
                    'FROM synergy_transition_team_defense as V WHERE DATE = "2016-04-15" ORDER BY PossG DESC) as sttd ON sttd.TEAM_NAME = tb2.TEAM_ABBREVIATION ' \
                'WHERE PLAYER_NAME = "%(name)s"' % {'name': name}

    write_to_csv(query, 'player_synergy', name)
    write_to_csv(query_two, 'player_synergy', name+'2')


def get_team_synergy_ranks():
    query = 'SELECT ostd.TeamNameAbbreviation as TEAM_NAME, ostd.BetterPPP+1 as OFFSCREEN_RANK, '\
        'ctd.BetterPPP+1 as CUT_RANK, '\
        'htd.BetterPPP+1 as HAND_RANK, '\
        'itd.BetterPPP+1 as ISO_RANK, '\
        'mtd.BetterPPP+1 as MISC_RANK, '\
        'putd.BetterPPP+1 as POST_RANK, '\
        'phtd.BetterPPP+1 as PR_HANDLER_RANK, '\
        'prtd.BetterPPP+1 as PR_ROLL_RANK, '\
        'pbtd.BetterPPP+1 as PUT_BACK_RANK, '\
        'std.BetterPPP+1 as SPOTUP_RANK, '\
        'ttd.BetterPPP+1 as TRANS_RANK '\
        'FROM synergy_off_screen_team_defense as ostd '\
            'LEFT JOIN synergy_cut_team_defense as ctd ON ostd.TeamNameAbbreviation = ctd.TeamNameAbbreviation AND ostd.DATE = ctd.DATE '\
            'LEFT JOIN synergy_handoff_team_defense as htd ON ostd.TeamNameAbbreviation = htd.TeamNameAbbreviation AND ostd.DATE = htd.DATE '\
            'LEFT JOIN synergy_isolation_team_defense as itd ON ostd.TeamNameAbbreviation = itd.TeamNameAbbreviation AND ostd.DATE = itd.DATE '\
            'LEFT JOIN synergy_misc_team_defense as mtd ON ostd.TeamNameAbbreviation = mtd.TeamNameAbbreviation AND ostd.DATE = mtd.DATE '\
            'LEFT JOIN synergy_post_up_team_defense as putd ON ostd.TeamNameAbbreviation = putd.TeamNameAbbreviation AND ostd.DATE = putd.DATE '\
            'LEFT JOIN synergy_pr_ball_handler_team_defense as phtd ON ostd.TeamNameAbbreviation = phtd.TeamNameAbbreviation AND ostd.DATE = phtd.DATE '\
            'LEFT JOIN synergy_pr_roll_man_team_defense as prtd ON ostd.TeamNameAbbreviation = prtd.TeamNameAbbreviation AND ostd.DATE = prtd.DATE '\
            'LEFT JOIN synergy_put_back_team_defense as pbtd ON ostd.TeamNameAbbreviation = pbtd.TeamNameAbbreviation AND ostd.DATE = pbtd.DATE '\
            'LEFT JOIN synergy_spot_up_team_defense as std ON ostd.TeamNameAbbreviation = std.TeamNameAbbreviation AND ostd.DATE = std.DATE '\
            'LEFT JOIN synergy_transition_team_defense as ttd ON ostd.TeamNameAbbreviation = ttd.TeamNameAbbreviation AND ostd.DATE = ttd.DATE '\
        'WHERE ostd.DATE = "%(date)s" '% {'date': LAST_DATE_REG_SEASON}
    return query

def get_starter_defensive_stats(players):
    query = 'SELECT DISTINCT ostd.PLAYER_ID, CONCAT(ostd.PlayerFirstName, " ", ostd.PlayerLastName) as PLAYER_NAME, '\
            'ostd.TeamNameAbbreviation as TEAM_NAME, '\
            'ostd.BetterPPP+1 as OFFSCREEN_RANK, '\
            'ROUND(ostd.PPP, 2) as OFFSCREEN_ALLOWED_PPP, '\
            'ROUND(ostd.PossG, 2) as OFFSCREEN_ALLOWED_PossG, '\
            'htd.BetterPPP+1 as HAND_RANK, '\
            'ROUND(htd.PPP, 2) as HAND_OFF_ALLOWED_PPP, '\
            'ROUND(htd.PossG, 2) as HAND_OFF_ALLOWED_PossG, '\
            'iso.BetterPPP+1 as ISO_RANK, '\
            'ROUND(iso.PPP, 2) as ISO_ALLOWED_PPP, '\
            'ROUND(iso.PossG, 2) as ISO_ALLOWED_PossG, '\
            'putd.BetterPPP+1 as POST_RANK, '\
            'ROUND(putd.PPP, 2) as POST_ALLOWED_PPP, '\
            'ROUND(putd.PossG, 2) as POST_ALLOWED_PossG, '\
            'phtd.BetterPPP+1 as PR_HANDLER_RANK, '\
            'ROUND(phtd.PPP, 2) as PR_HANDLER_ALLOWED_PPP, '\
            'ROUND(phtd.PossG, 2) as PR_HANDLER_ALLOWED_PossG, '\
            'prtd.BetterPPP+1 as PR_ROLL_RANK, '\
            'ROUND(prtd.PPP, 2) as PR_ROLL_ALLOWED_PPP, '\
            'ROUND(prtd.PossG, 2) as PR_ROLL_ALLOWED_PossG, '\
            'std.BetterPPP+1 as SPOTUP_RANK, '\
            'ROUND(std.PPP, 2) as SPOTUP_ALLOWED_PPP, '\
            'ROUND(std.PossG, 2) as SPOTUP_ALLOWED_PossG '\
            'FROM synergy_off_screen_defense as ostd  '\
                'LEFT JOIN synergy_handoff_defense as htd ON ostd.player_id = htd.player_id AND ostd.DATE = htd.DATE '\
                'LEFT JOIN synergy_isolation_defense as iso ON ostd.player_id = iso.player_id AND ostd.DATE = iso.DATE '\
                'LEFT JOIN synergy_post_up_defense as putd ON ostd.player_id = putd.player_id AND ostd.DATE = putd.DATE '\
                'LEFT JOIN synergy_pr_ball_handler_defense as phtd ON ostd.player_id = phtd.player_id AND ostd.DATE = phtd.DATE '\
                'LEFT JOIN synergy_pr_roll_man_defense as prtd ON ostd.player_id = prtd.player_id AND ostd.DATE = prtd.DATE '\
                'LEFT JOIN synergy_spot_up_defense as std ON ostd.player_id = std.player_id AND ostd.DATE = std.DATE '\
            'WHERE ostd.DATE = "2016-04-15" and CONCAT(ostd.PlayerFirstName, " ", ostd.PlayerLastName) '\
            'IN ("%(players)s") AND ostd.IS_REGULAR_SEASON = 1 GROUP BY(PLAYER_NAME)' % {'players': players}
    return query

def get_starter_offensive_stats(players):
    query = 'SELECT DISTINCT ostd.PLAYER_ID, CONCAT(ostd.PlayerFirstName, " ", ostd.PlayerLastName) as PLAYER_NAME, ostd.TeamNameAbbreviation as TEAM_NAME, '\
            'ostd.BetterPPP+1 as OFFSCREEN_RANK, '\
            'ROUND(ostd.PPP, 2) as OFFSCREEN_PPP, '\
            'ROUND(ostd.PossG, 2) as OFFSCREEN_PossG, '\
            'htd.BetterPPP+1 as HAND_RANK, '\
            'ROUND(htd.PPP, 2) as HAND_OFF_PPP, '\
            'ROUND(htd.PossG, 2) as HAND_OFF_PossG, '\
            'itd.BetterPPP+1 as ISO_RANK, '\
            'ROUND(itd.PPP, 2) as ISO_PPP, '\
            'ROUND(itd.PossG, 2) as ISO_PossG, '\
            'putd.BetterPPP+1 as POST_RANK, '\
            'ROUND(putd.PPP, 2) as POST_PPP, '\
            'ROUND(putd.PossG, 2) as POST_PossG, '\
            'phtd.BetterPPP+1 as PR_HANDLER_RANK, '\
            'ROUND(phtd.PPP, 2) as PR_HANDLER_PPP, '\
            'ROUND(phtd.PossG, 2) as PR_HANDLER_PossG, '\
            'prtd.BetterPPP+1 as PR_ROLL_RANK, '\
            'ROUND(prtd.PPP, 2) as PR_ROLL_PPP, '\
            'ROUND(prtd.PossG, 2) as PR_ROLL_PossG, '\
            'std.BetterPPP+1 as SPOTUP_RANK, '\
            'ROUND(std.PPP, 2) as SPOTUP_PPP, '\
            'ROUND(std.PossG, 2) as SPOTUP_PossG, '\
            'cut.BetterPPP+1 as CUT_RANK, '\
            'ROUND(cut.PPP, 2) as CUT_PPP, '\
            'ROUND(cut.PossG, 2) as CUT_PossG, '\
            'misc.BetterPPP+1 as MISC_RANK, '\
            'ROUND(misc.PPP, 2) as MISC_PPP, '\
            'ROUND(misc.PossG, 2) as MISC_PossG, '\
            'putback.BetterPPP+1 as PUT_BACK_RANK, '\
            'ROUND(putback.PPP, 2) as PUT_BACK_PPP, '\
            'ROUND(putback.PossG, 2) as PUT_BACK_PossG, '\
            'trans.BetterPPP+1 as TRANSITION_RANK, '\
            'ROUND(trans.PPP, 2) as TRANSITION_PPP, '\
            'ROUND(trans.PossG, 2) as TRANSITION_PossG '\
            'FROM synergy_off_screen_offense as ostd '\
                'LEFT JOIN synergy_handoff_offense as htd ON ostd.player_id = htd.player_id AND ostd.DATE = htd.DATE '\
                'LEFT JOIN synergy_isolation_offense as itd ON ostd.player_id = itd.player_id AND ostd.DATE = itd.DATE '\
                'LEFT JOIN synergy_post_up_offense as putd ON ostd.player_id = putd.player_id AND ostd.DATE = putd.DATE '\
                'LEFT JOIN synergy_pr_ball_handler_offense as phtd ON ostd.player_id = phtd.player_id AND ostd.DATE = phtd.DATE '\
                'LEFT JOIN synergy_pr_roll_man_offense as prtd ON ostd.player_id = prtd.player_id AND ostd.DATE = prtd.DATE '\
                'LEFT JOIN synergy_spot_up_offense as std ON ostd.player_id = std.player_id AND ostd.DATE = std.DATE '\
                'LEFT JOIN synergy_cut_offense as cut ON ostd.player_id = cut.player_id AND ostd.DATE = cut.DATE '\
                'LEFT JOIN synergy_misc_offense as misc ON ostd.player_id = misc.player_id AND ostd.DATE = misc.DATE '\
                'LEFT JOIN synergy_put_back_offense as putback ON ostd.player_id = putback.player_id AND ostd.DATE = putback.DATE '\
                'LEFT JOIN synergy_transition_offense as trans ON ostd.player_id = trans.player_id AND ostd.DATE = trans.DATE '\
            'WHERE ostd.DATE = "2016-04-15" and CONCAT(ostd.PlayerFirstName, " ", ostd.PlayerLastName) '\
                            'IN ("%(players)s") AND ostd.IS_REGULAR_SEASON = 1 GROUP BY(PLAYER_NAME)' % {'players': players}
    return query

def get_player_names():
    query = 'SELECT PLAYER_ID, '\
       'PLAYER_NAME '\
        'FROM   traditional_boxscores '\
        'WHERE  GAME_ID IN (SELECT GAME_ID '\
                    'FROM   game_summary '\
                    'WHERE  GAME_DATE_EST >= "2015-10-27" '\
                                  'AND GAME_DATE_EST <= "2016-04-15") '\
        'GROUP  BY PLAYER_ID '
    return query

def get_player_id_by_team(team):
    query = 'SELECT PLAYER_ID '\
        'FROM   traditional_boxscores '\
        'WHERE  GAME_ID IN (SELECT GAME_ID '\
                           'FROM   game_summary '\
                           'WHERE  GAME_DATE_EST >= "2015-10-27" '\
                                  'AND GAME_DATE_EST <= "2016-04-15") '\
               'AND TEAM_ABBREVIATION = "%(team)s" '\
        'GROUP  BY PLAYER_ID ' % {'team': team}
    return query

def get_lineups_per_action(player_id, team, event):
    query = 'SELECT GAME_ID, '\
        'HOME_PLAYER1, '\
        'HOME_PLAYER2, '\
        'HOME_PLAYER3, '\
        'HOME_PLAYER4, '\
        'HOME_PLAYER5 '\
        'FROM   pbp '\
        'WHERE  GAME_ID IN (SELECT GAME_ID '\
            'FROM   game_summary '\
            'WHERE  GAME_DATE_EST >= "2015-10-27" '\
               'AND GAME_DATE_EST <= "2016-04-15" '\
               'AND HOME_TEAM_ID = (SELECT TEAM_ID '\
                                    'FROM '\
                                      'traditional_boxscores_team ' \
                                          'WHERE  TEAM_ABBREVIATION = "%(team)s" ' \
                                          'GROUP  BY TEAM_ID)) '\
                'AND ( PLAYER1_ID = "%(player_id)s" ) '\
            'AND EVENTMSGTYPE IN (%(event)s) ' % {'player_id': player_id, 'team': team, 'event': event}
    return query

def get_totals_by_home_lineup(team, event):
    query = 'SELECT GAME_ID, '\
               'HOME_PLAYER1, '\
               'HOME_PLAYER2, '\
               'HOME_PLAYER3, '\
               'HOME_PLAYER4, '\
               'HOME_PLAYER5 '\
        'FROM   pbp '\
        'WHERE  GAME_ID IN (SELECT GAME_ID '\
                           'FROM   game_summary '\
                           'WHERE  GAME_DATE_EST >= "%(date_begin)s" '\
                                  'AND GAME_DATE_EST <= "%(date_end)s" '\
                                  'AND HOME_TEAM_ID = (SELECT TEAM_ID '\
                                                      'FROM '\
                                      'traditional_boxscores_team '\
                                                      'WHERE  TEAM_ABBREVIATION = "%(team)s" '\
                                                      'GROUP  BY TEAM_ID)) '\
               'AND ( PLAYER1_ID IN (SELECT PLAYER_ID '\
                                    'FROM   traditional_boxscores '\
                                    'WHERE  GAME_ID IN (SELECT GAME_ID '\
                                                       'FROM   game_summary '\
                                                       'WHERE '\
                                           'GAME_DATE_EST >= "%(date_begin)s" '\
                                           'AND GAME_DATE_EST <= "%(date_end)s" '\
                                                      ') '\
                                           'AND TEAM_ABBREVIATION = "%(team)s" '\
                                    'GROUP  BY PLAYER_ID) ) '\
               'AND EVENTMSGTYPE IN (%(event)s) ' % {'team': team, 'event': event, 'date_begin': FIRST_DATE_REG_SEASON, 'date_end': LAST_DATE_REG_SEASON}

    return query

def get_totals_by_away_lineup(team, event):
    query = 'SELECT GAME_ID, '\
               'VISITOR_PLAYER1, '\
               'VISITOR_PLAYER2, '\
               'VISITOR_PLAYER3, '\
               'VISITOR_PLAYER4, '\
               'VISITOR_PLAYER5 '\
        'FROM   pbp '\
        'WHERE  GAME_ID IN (SELECT GAME_ID '\
                           'FROM   game_summary '\
                           'WHERE  GAME_DATE_EST >= "%(date_begin)s" '\
                                  'AND GAME_DATE_EST <= "%(date_end)s" '\
                                  'AND VISITOR_TEAM_ID = (SELECT TEAM_ID '\
                                                      'FROM '\
                                      'traditional_boxscores_team '\
                                                      'WHERE  TEAM_ABBREVIATION = "%(team)s" '\
                                                      'GROUP  BY TEAM_ID)) '\
               'AND ( PLAYER1_ID IN (SELECT PLAYER_ID '\
                                    'FROM   traditional_boxscores '\
                                    'WHERE  GAME_ID IN (SELECT GAME_ID '\
                                                       'FROM   game_summary '\
                                                       'WHERE '\
                                           'GAME_DATE_EST >= "%(date_begin)s" '\
                                           'AND GAME_DATE_EST <= "%(date_end)s" '\
                                                      ') '\
                                           'AND TEAM_ABBREVIATION = "%(team)s" '\
                                    'GROUP  BY PLAYER_ID) ) '\
               'AND EVENTMSGTYPE IN (%(event)s) ' % {'team': team, 'event': event, 'date_begin': FIRST_DATE_REG_SEASON, 'date_end': LAST_DATE_REG_SEASON}

    return query

def get_player_against_team_log(team, players):
    query = 'SELECT  ub.PLAYER_NAME, ub.START_POSITION, ub.USG_PCT, '\
            'tb.MIN, tb.FGA, tb.FG_PCT, tb.FG3A, tb.OREB, tb.REB, tb.AST, tb.STL, tb.PTS, tb.TO, tb.PF, '\
            'tb.FG3M * 0.5 + tb.REB * 1.25 + tb.AST * 1.25 + tb.STL * 2 + tb.BLK * 2 + tb.TO * -0.5 + tb.PTS * 1 AS DK_POINTS, '\
            'ROUND((tb.FG3M * 0.5 + tb.REB * 1.25 + tb.AST * 1.25 + tb.STL * 2 + tb.BLK * 2 + tb.TO *-0.5 + tb.PTS * 1)/tb.MIN, 2) AS FP_PER_MIN, '\
            'mb.PTS_PAINT, mb.PFD, '\
            'dgl.DRIVES, dgl.DRIVE_FGA, dgl.DRIVE_FG_PCT, dr.DRIVE_PTS, '\
            'ptb.TCHS AS TOUCHES, ptb.CFGA AS CONTESTED_FGA, ptb.CFG_PCT AS CONTESTED_FG_PCT, ab.PACE, '\
            'ROUND(prho.PossG, 2) as PNR_POSSG, ROUND(iso.PossG, 2) as ISO_POSSG, ROUND(spot.PossG, 2) as SPOT_POSSG, ROUND(screen.PossG, 2) as OFF_SCREEN_POSSG, '\
            'cs.CATCH_SHOOT_FGA / cs.GP AS "CATCH_SHOOT_FGA", cs.CATCH_SHOOT_FG_PCT, cs.CATCH_SHOOT_FG3A / cs.GP AS "CATCH_SHOOT_3FGA", '\
            'pass.PASSES_MADE / cs.GP AS "PASSES_MADE", pass.PASSES_RECEIVED / cs.GP AS "PASSES_RECEIVED", poss.TIME_OF_POSS / cs.GP AS "TIME_OF_POSS", '\
            'pot.POST_TOUCH_FGA / cs.GP AS "POST_TOUCH_FGA", pus.PULL_UP_FGA / cs.GP AS "PULL_UP_FGA", pus.PULL_UP_FG3A / cs.GP AS "PULL_UP_3FGA", '\
            'gs.NATL_TV_BROADCASTER_ABBREVIATION AS NATIONAL_TV '\
            'FROM   usage_boxscores AS ub '\
            'LEFT JOIN game_summary AS gs '\
            'ON gs.game_id = ub.game_id '\
            'LEFT JOIN traditional_boxscores AS tb '\
            'ON tb.game_id = ub.game_id '\
                    'AND tb.player_id = ub.player_id '\
            'LEFT JOIN player_tracking_boxscores AS ptb '\
            'ON ptb.game_id = ub.game_id '\
                    'AND ptb.player_id = ub.player_id '\
            'LEFT JOIN advanced_boxscores AS ab '\
            'ON ab.game_id = ub.game_id '\
                    'AND ab.player_id = ub.player_id '\
            'LEFT JOIN misc_boxscores AS mb '\
            'ON mb.game_id = ub.game_id '\
                    'AND mb.player_id = ub.player_id '\
            'LEFT JOIN synergy_pr_ball_handler_offense AS prho '\
            'ON prho.player_id = ub.player_id '\
            'AND prho.team_id = ub.team_id '\
                    'AND prho.DATE = "2016-04-15" '\
            'LEFT JOIN synergy_isolation_offense AS iso '\
            'ON iso.player_id = ub.player_id '\
            'AND iso.team_id = ub.team_id '\
                    'AND iso.DATE = "2016-04-15" '\
            'LEFT JOIN synergy_spot_up_offense AS spot '\
            'ON spot.player_id = ub.player_id '\
            'AND spot.team_id = ub.team_id '\
                    'AND spot.DATE = "2016-04-15" '\
            'LEFT JOIN synergy_off_screen_offense AS screen '\
            'ON screen.player_id = ub.player_id '\
            'AND screen.team_id = ub.team_id '\
            'AND screen.DATE = "2016-04-15" '\
            'LEFT JOIN sportvu_catch_shoot_game_logs AS cs '\
            'ON cs.player_id = ub.player_id '\
            'AND cs.game_id = ub.game_id '\
            'LEFT JOIN sportvu_drives_game_logs AS dr '\
            'ON dr.player_id = ub.player_id '\
            'AND dr.game_id = ub.game_id '\
            'LEFT JOIN sportvu_paint_touches_game_logs AS pt '\
            'ON pt.player_id = ub.player_id '\
            'AND pt.game_id = ub.game_id '\
            'LEFT JOIN sportvu_passing_game_logs AS pass '\
            'ON pass.player_id = ub.player_id '\
            'AND pass.game_id = ub.game_id '\
            'LEFT JOIN sportvu_possessions_game_logs AS poss '\
            'ON poss.player_id = ub.player_id '\
            'AND poss.game_id = ub.game_id '\
            'LEFT JOIN sportvu_post_touches_game_logs AS pot '\
            'ON pot.player_id = ub.player_id '\
            'AND pot.game_id = ub.game_id '\
            'LEFT JOIN sportvu_pull_up_shoot_game_logs AS pus '\
            'ON pus.player_id = ub.player_id '\
            'AND pus.game_id = ub.game_id '\
            'INNER JOIN (SELECT tbt.game_id, tbt.TEAM_ABBREVIATION '\
            'FROM traditional_boxscores_team AS tbt) AS tb2 '\
            'ON tb2.game_id = ub.game_id '\
                    'AND tb2.TEAM_ABBREVIATION != ub.TEAM_ABBREVIATION '\
                    'AND Str_to_date(gs.game_date_est, "%(date_format_year)s") >= "2015-10-27" '\
                    'AND Str_to_date(gs.game_date_est, "%(date_format_year)s") <= "2016-04-15" '\
            'LEFT JOIN sportvu_drives_game_logs AS dgl '\
            'ON dgl.game_id = ub.game_id '\
            'AND dgl.player_id = ub.player_id '\
            'WHERE tb2.TEAM_ABBREVIATION = "%(team)s" '\
            'AND ub.MIN >= 15 '\
            'AND ub.PLAYER_NAME in ("%(players)s") '\
            'AND ub.game_id NOT LIKE "%(season_id)s" '\
        'ORDER  BY DK_POINTS DESC' % {'team': team, 'players': players, 'date_format_year': DATE_FORMAT_YEAR, 'season_id': '001%'}

    return query

# get_synergy_wrt_dk('DeMar DeRozan')
# get_data_against_based_on_position()
# /* shooting fouls  */
# -- 1=personal foul, 2=shooting foul, 3=blocking foul
# select * from pbp INNER JOIN (SELECT game_id FROM traditional_boxscores_team WHERE TEAM_ABBREVIATION = "TOR" ORDER BY game_id DESC LIMIT 3 ) as tb3 ON tb3.game_id = pbp.game_id where `EVENTMSGTYPE` = 6 and `EVENTMSGACTIONTYPE`= 2 and `PLAYER1_TEAM_ABBREVIATION` = "TOR"

# -- 1 = bad pass, 2= lost ball
# select * from pbp INNER JOIN (SELECT game_id FROM traditional_boxscores_team WHERE TEAM_ABBREVIATION = "TOR" ORDER BY game_id DESC LIMIT 3 ) as tb3 ON tb3.game_id = pbp.game_id where `EVENTMSGTYPE` = 5 and `EVENTMSGACTIONTYPE` = 1 and `PLAYER1_TEAM_ABBREVIATION` = "TOR"

# officials and fouls per game
# select off_fouls.OFFICIAL, count(off_fouls.OFFICIAL) as num_games, sum(off_fouls.fouls)/count(off_fouls.OFFICIAL) as total_fouls from (Select off.GAME_ID, CONCAT(off.`FIRST_NAME`, off.`LAST_NAME`) as OFFICIAL, g2.fouls from officials as off inner join (select game_id, sum(pf) as fouls from `traditional_boxscores_team` group by game_id) as g2 on g2.game_id = off.game_id) as off_fouls group by off_fouls.OFFICIAL

# -- passes to slowness of the game what about posessions?
# select pass.`TEAM_ABBREVIATION`, pass.PASSES_MADE/pass.GP, poss.TOUCHES/poss.GP, poss.TIME_OF_POSS/poss.GP, AVG_SEC_PER_TOUCH from `sportvu_passing_team` as pass left join sportvu_possessions_team as poss on poss.team_id = pass.team_id and poss.date = pass.date where pass.date = '2016-04-15'
# avg pass per fga
# select gl.`TEAM_ABBREVIATION` as TEAM, avg(gl.`PASSES_MADE`/tb.FGA) as PASS_PER_FGA from `sportvu_passing_team_game_logs` as gl left join traditional_boxscores_team as tb on tb.game_id = gl.game_id and tb.team_id = gl.team_id WHERE gl.date <= '2016-04-15' and gl.date >= '2015-10-27' group by TEAM
# with orb and teams against and pace
# select gl.`TEAM_ABBREVIATION`, tb2.TEAM_ABBREVIATION as TEAM_AGAIN0ST, gl.`PASSES_MADE`/tb.FGA as PASS_PER_FGA, gl.W, gl.L, tb.FGA, tb.OREB, mb.`PTS_2ND_CHANCE`, tb2.FGA as TEAM_AGAINST_FGA, tb2.OREB as TEAM_AGAINST_OREB, ab.PACE from `sportvu_passing_team_game_logs` as gl left join traditional_boxscores_team as tb on tb.game_id = gl.game_id and tb.team_id = gl.team_id left join advanced_boxscores_team as ab on ab.game_id = gl.game_id and ab.team_id = gl.team_id left join misc_boxscores_team as mb on mb.game_id = gl.game_id and mb.team_id = gl.team_id INNER JOIN (SELECT tbt.game_id, tbt.TEAM_ABBREVIATION, tbt.FGA, tbt.OREB FROM traditional_boxscores_team as tbt) as tb2 ON tb2.game_id = gl.game_id and tb2.TEAM_ABBREVIATION != gl.TEAM_ABBREVIATION WHERE tb2.TEAM_ABBREVIATION = 'ATL'

# -- if the opponent takes many threes
# select PLAYER_NAME, tb.MIN, tb2.TEAM_ABBREVIATION as TEAM_AGAINST, tb2.FG3A as OPP_FG3A, tb.FTA, tb.REB, tb.FG3A from traditional_boxscores as tb INNER JOIN (SELECT tbt.game_id, tbt.TEAM_ABBREVIATION, tbt.FG3A FROM traditional_boxscores_team as tbt) as tb2 ON tb2.game_id = tb.game_id and tb2.TEAM_ABBREVIATION != tb.TEAM_ABBREVIATION
'''
Can be used for visualization (not needed for now)
# shot_selection('team', 'CHO', 1, 'SHOT_DISTANCE', 1)
# shot_selection_time('teams', 'BRK', 1, 2)
'''
# detailed shot selection
# for team
# print get_shot_detailed_team()
# for players
# print shot_selection_type_detailed('DeMar DeRozan', 1, 1)

# synergy
# synergy_queries()

# player games
# player_last_game('DeMar DeRozan', 1)
# player_last_game('DeMar DeRozan', 3)
# get_sportvu_game_logs('Jeremy Lin', 'player', 1, 1)
# print get_sportvu_game_logs('Jeremy Lin', 'player', 1, 3)
# get_sportvu_game_logs('DeMar DeRozan', 'player', 1, 0)
# write_to_csv(get_sportvu_game_logs('DeMar DeRozan', 'player', 1, 0), 'player_sportvu', 'DeMar DeRozan')

# print full_player_log('Brandon Knight', FIRST_DATE_REG_SEASON, LAST_DATE_REG_SEASON, 0, 0)
# full_player_log('Jeremy Lin', FIRST_DATE_REG_SEASON, LAST_DATE_REG_SEASON, 0, 3)
# get_synergy_player('Jeremy Lin', FIRST_DATE_REG_SEASON, LAST_DATE_REG_SEASON, 1)
# get_synergy_player('Jeremy Lin', FIRST_DATE_REG_SEASON, LAST_DATE_REG_SEASON, 3)

# team games
# team_last_game('TOR', 1)
# team_last_game('TOR', 3)

# player_pass_received('DeMar DeRozan', 1)
# player_pass_made('DeMar DeRozan', 1)


# print player_shot_types_dribble('Jeremy Lin', DATE, 1)
'''
    For processing

team_against('TOR', FIRST_DATE_REG_SEASON, DATE)
team_direct_matchup('TOR','MIA', FIRST_DATE_REG_SEASON, DATE)
player_last_matchups('DeMar DeRozan', FIRST_DATE_REG_SEASON, LAST_DATE_REG_SEASON)
player_direct_matchup('DeMar DeRozan', 'Luol Deng', FIRST_DATE_REG_SEASON, DATE)
'''


# get_synergy_player('Jeremy Lin', FIRST_DATE_REG_SEASON, LAST_DATE_REG_SEASON, 3)

# player games
# print full_player_log('Jimmy Butler', FIRST_DATE_REG_SEASON, LAST_DATE_REG_SEASON, 0, 0)
# write_to_csv(full_player_log('Jeremy Lin', FIRST_DATE_REG_SEASON, LAST_DATE_REG_SEASON, 0), 'box', 'Jeremy Lin')
# full_player_log('Jeremy Lin', FIRST_DATE_REG_SEASON, LAST_DATE_REG_SEASON, 0)

# print get_game_line('TOR', 0, FIRST_DATE_REG_SEASON, LAST_DATE_REG_SEASON)

# print player_game_queries(LAST_DATE_REG_SEASON, DATE, 0, ['TOR', 'MIA'])
# ''' sportvu - team and players '''
# regular_teams = execute_query(sportvu_queries('team', 1, 0, ['TOR', 'MIA'], LAST_DATE_REG_SEASON))
# playoffs_teams = execute_query(sportvu_queries('team', 0, 0, ['TOR', 'MIA'], DATE))

# # all players
# regular_players = execute_query(sportvu_queries('player', 1, 0, ['TOR', 'MIA'], LAST_DATE_REG_SEASON))
# playoffs_players = execute_query(sportvu_queries('player', 0, 0, ['TOR', 'MIA'], DATE))

# # individual players
# regular_players = execute_query(sportvu_queries('player', 1, 1, 'DeMar DeRozan', LAST_DATE_REG_SEASON))
# print sportvu_queries('player', 1, 1, 'DeMar DeRozan', LAST_DATE_REG_SEASON)
# playoffs_players = execute_query(sportvu_queries('player', 0, 1, 'DeMar DeRozan', DATE))


# between two teams
# compare_team_stats(regular_teams, 75)
# compare_team_stats(playoffs_teams, 100)

# between regular season and playoffs
# compare_player_stats(regular_players, playoffs_players, 100)

# player stats - players - average between two teams
# playoffs
# result_playoffs = execute_query(player_game_queries(LAST_DATE_REG_SEASON, DATE, 0, ['TOR', 'MIA']))
# regular season
# result_season = execute_query(player_game_queries(FIRST_DATE_REG_SEASON, LAST_DATE_REG_SEASON, 0, ['TOR', 'MIA']))
# compare_player_stats(result_playoffs, result_season, 100)

db.close()