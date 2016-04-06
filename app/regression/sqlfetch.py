import MySQLdb
import json
import itertools
import pprint

pp = pprint.PrettyPrinter(indent=4)

# Open database connection
db = MySQLdb.connect("127.0.0.1","root","","nba_scrape" )

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
            process_query('SELECT CONCAT(PlayerFirstName, " ", PlayerLastName) as PlayerName, TeamNameAbbreviation as TeamName, GP, PPP, PossG, PPG '\
                        'FROM %(table)s WHERE P = "%(position)s" AND DATE = "%(date)s" ORDER BY PossG DESC' % {'position': position, 'date': DATE, 'table': table})
    # player defense
    for table in PLAYER_SYNERGY_TABLES_DEFENSE:
        for position in POSITIONS:
            process_query('SELECT CONCAT(PlayerFirstName, " ", PlayerLastName) as PlayerName, TeamNameAbbreviation as TeamName, GP, PPP, PossG, PPG '\
                        'FROM %(table)s WHERE P = "%(position)s" AND DATE = "%(date)s" ORDER BY PPP ASC' % {'position': position, 'date': DATE, 'table': table})

    # team
    for table in TEAM_SYNERGY_TABLES_OFFENSE:
        process_query('SELECT TeamName, TeamNameAbbreviation as Team, GP, PossG, PPP, FG FROM %(table)s '\
                    'WHERE DATE = "%(date)s" ORDER BY PossG DESC' % {'date': DATE, 'table': table})
    for table in TEAM_SYNERGY_TABLES_DEFENSE:
        process_query('SELECT TeamName, TeamNameAbbreviation as Team, GP, PossG, PPP, FG FROM %(table)s '\
                    'WHERE DATE = "%(date)s" ORDER BY PPP ASC' % {'date': DATE, 'table': table})

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

    sportvu_query = 'SELECT cs.%(query_for)s, cs.TEAM_ABBREVIATION, cs.GP, '\
            'cs.CATCH_SHOOT_FGA/cs.GP as "FGA_PER_GAME", '\
            'cs.CATCH_SHOOT_FG_PCT, '\
            'cs.CATCH_SHOOT_FG3A/cs.GP as "FG3A_PER_GAME", '\
            'cs.CATCH_SHOOT_FG3_PCT, '\
            'cs.CATCH_SHOOT_EFG_PCT, '\
            'def.DEF_RIM_FGM/cs.GP as "FGAllowedPerGame", '\
            'def.DEF_RIM_FGA/cs.GP as "FGFacedPerGame", '\
            'def.DEF_RIM_FG_PCT, '\
            'dr.DRIVES/cs.GP as "DrivesPerGame", '\
            'dr.DRIVE_FGA/cs.GP as "DriveFGAPerGame", '\
            'dr.DRIVE_FG_PCT, '\
            'dr.DRIVE_PTS/cs.GP as "DrivePtsPerGame", '\
            'dr.DRIVE_PF/cs.GP as "DrivePFPerGame", '\
            'dr.DRIVE_PF_PCT, '\
            'et.ELBOW_TOUCHES/cs.GP as "ElbowTouchesPerGame", '\
            'et.ELBOW_TOUCH_FGA/cs.GP as "ElbowTouchesFGAPerGame", '\
            'et.ELBOW_TOUCH_FG_PCT, '\
            'et.ELBOW_TOUCH_PASSES/cs.GP as "ElbowTouchesPassesPerGame", '\
            'pt.PAINT_TOUCHES/cs.GP as "PaintTouchesPerGame", '\
            'pt.PAINT_TOUCH_FGA/cs.GP as "PaintTouchesFGAPerGame", '\
            'pt.PAINT_TOUCH_FG_PCT, '\
            'pt.PAINT_TOUCH_PASSES/cs.GP as "PaintTouchesPassesPerGame", '\
            'pass.PASSES_MADE/cs.GP as "PassesMadePerGame", '\
            'pass.PASSES_RECEIVED/cs.GP as "PassesRecPerGame", '\
            'pass.AST_PTS_CREATED/cs.GP as "PtsCreatedPerGame", '\
            'poss.TOUCHES/cs.GP as "TouchesPerGame", '\
            'poss.TIME_OF_POSS/cs.GP AS "PossTimePerGame", '\
            'poss.AVG_SEC_PER_TOUCH, '\
            'poss.PTS_PER_TOUCH, '\
            'pot.POST_TOUCHES/cs.GP as "PostTouchesPerGame", '\
            'pot.POST_TOUCH_FGA/cs.GP as "PostTouchesFGAPerGame", '\
            'pot.POST_TOUCH_FG_PCT, '\
            'pot.POST_TOUCH_PASSES/cs.GP as "PostTouchesPassesPerGame", '\
            'pus.PULL_UP_FGA/cs.GP as "PullUpsPerGame", '\
            'pus.PULL_UP_FG_PCT, '\
            'pus.PULL_UP_PTS/cs.GP as "PullUpPtsPerGame", '\
            'pus.PULL_UP_FG3A/cs.GP as "PullUpFG3APerGame", '\
            'pus.PULL_UP_FG3_PCT, '\
            'pus.PULL_UP_EFG_PCT, '\
            'reb.OREB/cs.GP as "OREBPerGame", '\
            'reb.OREB_CHANCE_PCT, '\
            'reb.AVG_OREB_DIST, '\
            'reb.DREB/cs.GP as "DREBPerGame", '\
            'reb.DREB_CHANCE_PCT, '\
            'reb.AVG_DREB_DIST, '\
            'reb.REB/cs.GP as "REBPerGame", '\
            'reb.REB_CHANCE_PCT, '\
            'reb.AVG_REB_DIST, '\
            'sp.DIST_MILES/cs.GP as "MilesPerGame", '\
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
    process_query(sportvu_query)

def process_query(sql_query):
    try:
        # Execute the SQL command
        pp.pprint(sql_query)

        cursor.execute(sql_query)
        query_result = [dict(line) for line in [zip([column[0] for column in cursor.description],
                     row) for row in cursor.fetchall()]]
        # Fetch all the rows in a list of lists.
    except:
       print "Error: unable to fetch data"

    return query_result

FINAL_DATA = {}
synergy_queries()
sportvu_queries('player')
sportvu_queries('team')


db.close()