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

# Get top 50 rim defender in the nba, sorted by fg%
top_50_rim_defenders = 'SELECT PLAYER_NAME, TEAM_ABBREVIATION, GP, DEF_RIM_FGM, DEF_RIM_FGA, DEF_RIM_FG_PCT '\
                    ' FROM (SELECT * '\
                    'FROM sportvu_defense '\
                    'ORDER BY DEF_RIM_FGA DESC '\
                    'LIMIT 50) vu_defense '\
                    'WHERE DATE = "%s" '\
                    'ORDER BY DEF_RIM_FG_PCT ASC ' % DATE

# Get top 50 drivers in the nba, sorted by foul rate
top_50_drivers = 'SELECT PLAYER_NAME, TEAM_ABBREVIATION, DRIVES, DRIVE_PF_PCT, '\
                'DRIVE_PTS_PCT, DRIVE_FT_PCT, DRIVE_FG_PCT '\
                'FROM (SELECT * '\
                'FROM sportvu_drives '\
                'ORDER BY DRIVES DESC '\
                'LIMIT 50) drivers '\
                'WHERE DATE = "%s" '\
                'ORDER BY DRIVE_PF DESC ' % DATE

# -- Get top 50 pr handlers in the nba, sorted by points per possession
top_50_pr_handlers = 'SELECT PlayerFirstName, PlayerLastName, TeamNameAbbreviation, PPP, PossG, PPG '\
                    'FROM (SELECT * '\
                    'FROM synergy_pr_ball_handler_offense '\
                    'ORDER BY poss DESC '\
                    'LIMIT 50) offense_handler '\
                    'WHERE DATE = "%s" '\
                    'ORDER BY PossG DESC ' % DATE

# -- Get top 50 pr defender in the nba, sorted by points per possession
top_50_pr_defenders = 'SELECT PlayerFirstName, PlayerLastName, TeamNameAbbreviation, PPP, PossG, PPG '\
                    'FROM (SELECT * '\
                    'FROM synergy_pr_ball_handler_defense '\
                    'ORDER BY poss DESC '\
                    'LIMIT 50) defense_handler '\
                    'WHERE DATE = "%s" '\
                    'ORDER BY PPP ASC ' % DATE

# -- Get top 50 pr roller in the nba, sorted by points per possession
top_50_pr_roller = 'SELECT PlayerFirstName, PlayerLastName, TeamNameAbbreviation, PPP, PossG, PPG '\
                'FROM (SELECT * '\
                'FROM synergy_pr_roll_man_offense '\
                'ORDER BY poss DESC '\
                'LIMIT 50) offense_roll '\
                'WHERE DATE = "%s" '\
                'ORDER BY PossG DESC ' % DATE

# -- Get top 50 pr roll defender in the nba, sorted by points per possession
top_50_pr_roll_defense = 'SELECT PlayerFirstName, PlayerLastName, TeamNameAbbreviation, PPP, PossG, PPG  '\
                    'FROM (SELECT * '\
                    'FROM synergy_pr_roll_man_defense '\
                    'ORDER BY poss DESC '\
                    'LIMIT 50) defense_roll '\
                    'WHERE DATE = "%s" '\
                    'ORDER BY PPP ASC ' % DATE

# -- Get top 50 post up offense in the nba, sorted by points per possession
top_50_post_up_offense = 'SELECT PlayerFirstName, PlayerLastName, TeamNameAbbreviation, PPP, PossG, PPG '\
                    'FROM (SELECT * '\
                    'FROM synergy_post_up_offense '\
                    'ORDER BY poss DESC '\
                    'LIMIT 50) post_up_offense '\
                    'WHERE DATE = "%s" '\
                    'ORDER BY PossG DESC ' % DATE

# -- Get top 50 post up defender in the nba, sorted by points per possession
top_50_post_up_defense = 'SELECT PlayerFirstName, PlayerLastName, TeamNameAbbreviation, PPP, PossG, PPG '\
                        'FROM (SELECT * '\
                        'FROM synergy_post_up_defense '\
                        'ORDER BY poss DESC '\
                        'LIMIT 50) post_up_defense '\
                        'WHERE DATE = "%s" '\
                        'ORDER BY PPP ASC ' % DATE

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


def synergy_query():

    # player
    for table in PLAYER_SYNERGY_TABLES_OFFENSE:
        for position in POSITIONS:
            print 'SELECT CONCAT(PlayerFirstName, " ", PlayerLastName) as PlayerName, TeamNameAbbreviation as TeamName, GP, PPP, PossG, PPG '\
                        'FROM %(table)s WHERE P = "%(position)s" AND DATE = "%(date)s" ORDER BY PossG DESC' % {'position': position, 'date': DATE, 'table': table}
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

def process_query(sql_query):
    try:
        # Execute the SQL command
        pp.pprint(sql_query)

        cursor.execute(sql_query)
        query_result = [dict(line) for line in [zip([column[0] for column in cursor.description],
                     row) for row in cursor.fetchall()]]
        # Fetch all the rows in a list of lists.
        # pp.pprint(query_result)
    except:
       print "Error: unable to fetch data"

    return query_result

FINAL_DATA = {}
# process_query(top_50_rim_defenders)
synergy_query()
# process_query(top_50_drivers)
# process_query(top_50_pr_handlers)
# process_query(top_50_pr_defenders)
# process_query(top_50_pr_roller)
# process_query(top_50_pr_roll_defense)
# process_query(top_50_post_up_offense)
# process_query(top_50_post_up_defense)

db.close()