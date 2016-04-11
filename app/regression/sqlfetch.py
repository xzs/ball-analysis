import MySQLdb
import json
import itertools
import pprint
import MySQLdb.converters

pp = pprint.PrettyPrinter(indent=4)

conv=MySQLdb.converters.conversions.copy()
conv[246]=float    # convert decimals to floats
conv[10]=str       # convert dates to strings

# Open database connection
db = MySQLdb.connect("127.0.0.1","root","","nba_scrape", conv=conv)

# prepare a cursor object using cursor() method
cursor = db.cursor()
DATE = '2016-04-01'

POSITIONS = ['G', 'F', 'G-F', 'C']

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


def synergy_queries():

    # player
    for table in PLAYER_SYNERGY_TABLES_OFFENSE:
        for position in POSITIONS:
            player_offense_query = 'SELECT CONCAT(PlayerFirstName, " ", PlayerLastName) as NAME, TeamNameAbbreviation as TEAM_NAME, GP, PPP, PossG, PPG '\
                        'FROM %(table)s WHERE P = "%(position)s" AND DATE = "%(date)s" ORDER BY PossG DESC' % {'position': position, 'date': DATE, 'table': table}
            execute_query(player_offense_query)

    # player defense
    for table in PLAYER_SYNERGY_TABLES_DEFENSE:
        for position in POSITIONS:
            player_defense_query = 'SELECT CONCAT(PlayerFirstName, " ", PlayerLastName) as NAME, TeamNameAbbreviation as TEAM_NAME, GP, PPP, PossG, PPG '\
                        'FROM %(table)s WHERE P = "%(position)s" AND DATE = "%(date)s" ORDER BY PPP ASC' % {'position': position, 'date': DATE, 'table': table}
            execute_query(player_defense_query)

    # team
    for table in TEAM_SYNERGY_TABLES_OFFENSE:
        # reset the session variables http://dba.stackexchange.com/a/56609
        team_offense_query = 'SELECT TeamName as NAME, TeamNameAbbreviation as TEAM_NAME, GP, PossG, PPP, FG, '\
                        'CASE '\
                        'WHEN @prev_value = PossG THEN @rank_count '\
                        'WHEN @prev_value := PossG THEN @rank_count := @rank_count + 1 '\
                        'END AS rank '\
                        'FROM %(table)s, (SELECT @prev_value:=NULL, @rank_count:=0) as V '\
                            'WHERE DATE = "%(date)s" ORDER BY PossG DESC' % {'date': DATE, 'table': table}
        execute_query(team_offense_query)

    for table in TEAM_SYNERGY_TABLES_DEFENSE:
        team_defense_query = 'SELECT TeamName as NAME, TeamNameAbbreviation as TEAM_NAME, GP, PossG, PPP, FG, '\
                        'CASE '\
                        'WHEN @prev_value = PPP THEN @rank_count '\
                        'WHEN @prev_value := PPP THEN @rank_count := @rank_count + 1 '\
                        'END AS rank '\
                        'FROM %(table)s, (SELECT @prev_value:=NULL, @rank_count:=0) as V '\
                            'WHERE DATE = "%(date)s" ORDER BY PPP ASC' % {'date': DATE, 'table': table}
        execute_query(team_defense_query)

def sportvu_queries(query_type):

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
            'cs.CATCH_SHOOT_FGA/cs.GP as "FGA_PER_GAME", '\
            'cs.CATCH_SHOOT_FG_PCT, '\
            'cs.CATCH_SHOOT_FG3A/cs.GP as "FG3A_PER_GAME", '\
            'cs.CATCH_SHOOT_FG3_PCT, '\
            'cs.CATCH_SHOOT_EFG_PCT, '\
            'def.DEF_RIM_FGM/cs.GP as "FG_ALLOWED_PER_GAME", '\
            'def.DEF_RIM_FGA/cs.GP as "FG_FACED_PER_GAME", '\
            'def.DEF_RIM_FG_PCT, '\
            'dr.DRIVES/cs.GP as "DRIVES_PER_GAME", '\
            'dr.DRIVE_FGA/cs.GP as "DRIVE_FGA_PER_GAME", '\
            'dr.DRIVE_FG_PCT, '\
            'dr.DRIVE_PTS/cs.GP as "DRIVE_PTS_PER_GAME", '\
            'dr.DRIVE_PF/cs.GP as "DRIVE_PF_PER_GAME", '\
            'dr.DRIVE_PF_PCT, '\
            'et.ELBOW_TOUCHES/cs.GP as "ELBOW_TOUCHES_PER_GAME", '\
            'et.ELBOW_TOUCH_FGA/cs.GP as "ELBOW_TOUCH_FGA_PER_GAME", '\
            'et.ELBOW_TOUCH_FG_PCT, '\
            'et.ELBOW_TOUCH_PASSES/cs.GP as "ELBOW_TOUCH_PASSES_PER_GAME", '\
            'pt.PAINT_TOUCHES/cs.GP as "PAINT_TOUCHES_PER_GAME", '\
            'pt.PAINT_TOUCH_FGA/cs.GP as "PAINT_TOUCH_FGA_PER_GAME", '\
            'pt.PAINT_TOUCH_FG_PCT, '\
            'pt.PAINT_TOUCH_PASSES/cs.GP as "PAINT_TOUCH_PASSES_PER_GAME", '\
            'pass.PASSES_MADE/cs.GP as "PASSES_MADE_PER_GAME", '\
            'pass.PASSES_RECEIVED/cs.GP as "PASSES_RECEIVED_PER_GAME", '\
            'pass.AST_PTS_CREATED/cs.GP as "AST_PTS_CREATED_PER_GAME", '\
            'poss.TOUCHES/cs.GP as "TOUCHES_PER_GAME", '\
            'poss.TIME_OF_POSS/cs.GP AS "TIME_OF_POSS_PER_GAME", '\
            'poss.AVG_SEC_PER_TOUCH, '\
            'poss.PTS_PER_TOUCH, '\
            'pot.POST_TOUCHES/cs.GP as "POST_TOUCHES_PER_GAME", '\
            'pot.POST_TOUCH_FGA/cs.GP as "POST_TOUCH_FGA_PER_GAME", '\
            'pot.POST_TOUCH_FG_PCT, '\
            'pot.POST_TOUCH_PASSES/cs.GP as "POST_TOUCH_PASSES_PER_GAME", '\
            'pus.PULL_UP_FGA/cs.GP as "PULL_UP_FGA_PER_GAME", '\
            'pus.PULL_UP_FG_PCT, '\
            'pus.PULL_UP_PTS/cs.GP as "PULL_UP_PTS_PER_GAME", '\
            'pus.PULL_UP_FG3A/cs.GP as "PULL_UP_FG3A_PER_GAME", '\
            'pus.PULL_UP_FG3_PCT, '\
            'pus.PULL_UP_EFG_PCT, '\
            'reb.OREB/cs.GP as "OREB_PER_GAME", '\
            'reb.OREB_CHANCE_PCT, '\
            'reb.AVG_OREB_DIST, '\
            'reb.DREB/cs.GP as "DREB_PER_GAME", '\
            'reb.DREB_CHANCE_PCT, '\
            'reb.AVG_DREB_DIST, '\
            'reb.REB/cs.GP as "REB_PER_GAME", '\
            'reb.REB_CHANCE_PCT, '\
            'reb.AVG_REB_DIST, '\
            'sp.DIST_MILES/cs.GP as "DIST_MILES_PER_GAME", '\
            'sp.AVG_SPEED '\
    'FROM sportvu_catch_shoot%(query_type)s as cs '\
        'LEFT JOIN sportvu_defense%(query_type)s as def '\
            'ON def.%(query_id)s = cs.%(query_id)s '\
            'AND def.DATE = cs.DATE '\
        'LEFT JOIN sportvu_drives%(query_type)s as dr '\
            'ON dr.%(query_id)s = cs.%(query_id)s '\
            'AND dr.DATE = cs.DATE '\
        'LEFT JOIN sportvu_elbow_touches%(query_type)s as et '\
            'ON et.%(query_id)s = cs.%(query_id)s '\
            'AND et.DATE = cs.DATE '\
        'LEFT JOIN sportvu_paint_touches%(query_type)s as pt '\
            'ON pt.%(query_id)s = cs.%(query_id)s '\
            'AND pt.DATE = cs.DATE '\
        'LEFT JOIN sportvu_passing%(query_type)s as pass '\
            'ON pass.%(query_id)s = cs.%(query_id)s '\
            'AND pass.DATE = cs.DATE '\
        'LEFT JOIN sportvu_possessions%(query_type)s as poss '\
            'ON poss.%(query_id)s = cs.%(query_id)s '\
            'AND poss.DATE = cs.DATE '\
        'LEFT JOIN sportvu_post_touches%(query_type)s as pot '\
            'ON pot.%(query_id)s = cs.%(query_id)s '\
            'AND pot.DATE = cs.DATE '\
        'LEFT JOIN sportvu_pull_up_shoot%(query_type)s as pus '\
            'ON pus.%(query_id)s = cs.%(query_id)s '\
            'AND pus.DATE = cs.DATE '\
        'LEFT JOIN sportvu_rebounding%(query_type)s as reb '\
            'ON reb.%(query_id)s = cs.%(query_id)s '\
            'AND reb.DATE = cs.DATE '\
        'LEFT JOIN sportvu_speed%(query_type)s as sp '\
            'ON sp.%(query_id)s = cs.%(query_id)s '\
            'AND sp.DATE = cs.DATE '\
    'WHERE cs.DATE = "%(date)s"' % {
        'date': DATE,
        'query_for': query_dict['query_for'],
        'query_id': query_dict['query_id'],
        'query_type': query_type,
    }
    execute_query(sportvu_query)

def player_game_queries(date_1, date_2):

    date_format_year = str("%Y-%m-%d")
    date_format_min = str("%i:%s")

    player_query = 'SELECT gs.GAME_ID, '\
            'STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") as DATE, '\
            'ub.PLAYER_NAME as NAME, '\
            'ub.TEAM_ABBREVIATION as TEAM, '\
            'ub.START_POSITION, '\
            'ub.MIN, '\
            'ub.USG_PCT, '\
            'ub.PCT_FGA, '\
            'ub.PCT_FG3A, '\
            'ub.PCT_FTA, '\
            'ub.PCT_REB, '\
            'ub.PCT_AST, '\
            'ub.PCT_TOV, '\
            'ub.PCT_STL, '\
            'ub.PCT_BLK, '\
            'ub.PCT_PF, '\
            'ub.PCT_PTS, '\
            'tb.FGA, '\
            'tb.FG_PCT, '\
            'tb.FG3M, '\
            'tb.FG3A, '\
            'tb.FG3_PCT, '\
            'tb.FTA, '\
            'tb.FT_PCT, '\
            'tb.REB, '\
            'tb.AST, '\
            'tb.STL, '\
            'tb.BLK, '\
            'tb.TO, '\
            'tb.PF, '\
            'tb.PTS, '\
            'tb.FG3M*0.5 + tb.REB*1.25+tb.AST*1.25+tb.STL*2+tb.BLK*2+tb.TO*-0.5+tb.PTS*1 as DK_POINTS, '\
            'tb.PLUS_MINUS, '\
            'ptb.RBC as REB_CHANCES, '\
            'ptb.TCHS as TOUCHES, '\
            'ptb.PASS, '\
            'ptb.AST/ptb.PASS as AST_PER_PASS, '\
            'ptb.CFGA as CONTESTED_FGA, '\
            'ptb.CFG_PCT as CONTESTED_FG_PCT, '\
            'ptb.FG_PCT, '\
            'ab.OFF_RATING, '\
            'ab.DEF_RATING, '\
            'ab.NET_RATING, '\
            'ab.AST_PCT, '\
            'ab.REB_PCT, '\
            'ab.EFG_PCT, '\
            'ab.USG_PCT, '\
            'ab.PACE, '\
            'sb.PCT_FGA_2PT, '\
            'sb.PCT_FGA_3PT, '\
            'sb.PCT_PTS_2PT, '\
            'sb.PCT_PTS_3PT, '\
            'sb.PCT_PTS_OFF_TOV, '\
            'sb.PCT_PTS_PAINT '\
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
        'WHERE STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") >= "%(date_begin)s" AND STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") <= "%(date_end)s" '\
        'ORDER BY STR_TO_DATE(ub.MIN,"%(date_format_min)s") DESC' % {'date_format_year': date_format_year, 'date_format_min': date_format_min, 'date_begin': date_1, 'date_end': date_2}

    log_results = execute_query(player_query)

    avg_player_query = 'SELECT gs.GAME_ID, '\
            'STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") as DATE, '\
            'ub.PLAYER_NAME as NAME, '\
            'ub.TEAM_ABBREVIATION as TEAM, '\
            'ub.START_POSITION, '\
            'ROUND(avg(ub.MIN), 4) as MIN, '\
            'ROUND(avg(ub.USG_PCT), 4) as USG_PCT, '\
            'ROUND(avg(ub.PCT_FGA), 4) as PCT_FGA, '\
            'ROUND(avg(ub.PCT_FG3A), 4) as PCT_FG3A, '\
            'ROUND(avg(ub.PCT_FTA), 4) as PCT_FTA, '\
            'ROUND(avg(ub.PCT_REB), 4) as PCT_REB, '\
            'ROUND(avg(ub.PCT_AST), 4) as PCT_AST, '\
            'ROUND(avg(ub.PCT_TOV), 4) as PCT_TOV, '\
            'ROUND(avg(ub.PCT_STL), 4) as PCT_STL, '\
            'ROUND(avg(ub.PCT_BLK), 4) as PCT_BLK, '\
            'ROUND(avg(ub.PCT_PF), 4) as PCT_PF, '\
            'ROUND(avg(ub.PCT_PTS), 4) as PCT_PTS, '\
            'ROUND(avg(tb.FGA), 4) as FGA, '\
            'ROUND(avg(tb.FG_PCT), 4) as FG_PCT, '\
            'ROUND(avg(tb.FG3M), 4) as FG3M, '\
            'ROUND(avg(tb.FG3A), 4) as FG3A, '\
            'ROUND(avg(tb.FG3_PCT), 4) as FG3_PCT, '\
            'ROUND(avg(tb.FTA), 4) as FTA, '\
            'ROUND(avg(tb.FT_PCT), 4) as FT_PCT, '\
            'ROUND(avg(tb.FG3M), 4) as FG3M, '\
            'ROUND(avg(tb.REB), 4) as REB, '\
            'ROUND(avg(tb.AST), 4) as AST, '\
            'ROUND(avg(tb.STL), 4) as STL, '\
            'ROUND(avg(tb.BLK), 4) as BLK, '\
            'ROUND(avg(tb.TO), 4) as TOV, '\
            'ROUND(avg(tb.PF), 4) as PF, '\
            'ROUND(avg(tb.PTS), 4) as PTS, '\
            'ROUND(avg(tb.FG3M*0.5 + tb.REB*1.25 + tb.AST*1.25 + tb.STL*2 + tb.BLK*2 + tb.TO*-0.5 + tb.PTS*1), 4) as DK_POINTS, '\
            'ROUND(avg(tb.PLUS_MINUS), 4) as PLUS_MINUS, '\
            'ROUND(avg(ptb.RBC), 4) as REB_CHANCES, '\
            'ROUND(avg(ptb.TCHS), 4) as TOUCHES, '\
            'ROUND(avg(ptb.PASS), 4) as PASS, '\
            'ROUND(avg(ptb.AST) / avg(ptb.PASS), 4) as AST_PER_PASS, '\
            'ROUND(avg(ptb.CFGA), 4) as CONTESTED_FGA, '\
            'ROUND(avg(ptb.CFG_PCT), 4) as CONTESTED_FG_PCT, '\
            'ROUND(avg(ptb.FG_PCT), 4) as FG_PCT, '\
            'ROUND(avg(ab.OFF_RATING), 4) as OFF_RATING, '\
            'ROUND(avg(ab.DEF_RATING), 4) as DEF_RATING, '\
            'ROUND(avg(ab.NET_RATING), 4) as NET_RATING, '\
            'ROUND(avg(ab.AST_PCT), 4) as AST_PCT, '\
            'ROUND(avg(ab.REB_PCT), 4) as REB_PCT, '\
            'ROUND(avg(ab.EFG_PCT), 4) as EFG_PCT, '\
            'ROUND(avg(ab.USG_PCT), 4) as USG_PCT, '\
            'ROUND(avg(ab.PACE), 4) as PACE, '\
            'ROUND(avg(sb.PCT_FGA_2PT), 4) as PCT_FGA_2PT, '\
            'ROUND(avg(sb.PCT_FGA_3PT), 4) as PCT_FGA_3PT, '\
            'ROUND(avg(sb.PCT_PTS_2PT), 4) as PCT_PTS_2PT, '\
            'ROUND(avg(sb.PCT_PTS_3PT), 4) as PCT_PTS_3PT, '\
            'ROUND(avg(sb.PCT_PTS_OFF_TOV), 4) as PCT_PTS_OFF_TOV, '\
            'ROUND(avg(sb.PCT_PTS_PAINT), 4) as PCT_PTS_PAINT, '\
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
        'WHERE STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") >= "%(date_begin)s" AND STR_TO_DATE(gs.game_date_est,"%(date_format_year)s") <= "%(date_end)s" '\
        'GROUP BY NAME' % {'date_format_year': date_format_year, 'date_format_min': date_format_min, 'date_begin': date_1, 'date_end': date_2}
    avg_results = execute_query(avg_player_query)
    process_query_result(log_results, avg_results)


def execute_query(sql_query):
    try:
        # Execute the SQL command
        cursor.execute(sql_query)
        query_result = [dict(line) for line in [zip([column[0] for column in cursor.description],
                     row) for row in cursor.fetchall()]]
    except:
        print "Error: unable to fetch data"

    return query_result

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

PLAYER_GAME_LOG = {}
synergy_queries()
sportvu_queries('player')
sportvu_queries('team')
player_game_queries('2015-10-27', '2015-10-30')


db.close()