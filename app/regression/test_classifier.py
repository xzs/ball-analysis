import sqlfetch
import logging
import numpy as np
import warnings
import matplotlib.pyplot as plt
from sklearn import tree


# explictly not show warnings
warnings.filterwarnings("ignore")
logging.getLogger("requests").setLevel(logging.WARNING)

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

def process_playtime(playtime_seconds, record):
    playtime = record.split(':')
    if len(playtime) > 1:
        playtime_seconds += int(playtime[0])*60 + int(playtime[1])
    else:
        playtime_seconds = 0

    return playtime_seconds

def sample_test():
    query = """SELECT
            ub.MIN,
            tb.FG3M*0.5 + tb.REB*1.25 + tb.AST*1.25 + tb.STL*2 + tb.BLK*2 + tb.TO*-0.5 + tb.PTS*1 as DK_POINTS,
            padk.AVG_DK_POINTS,
            tb.FGA,
            tb.REB,
            dr.DRIVES,
            cs.CATCH_SHOOT_FGA,
            pt.PAINT_TOUCHES,
            pass.PASSES_MADE,
            pot.POST_TOUCHES,
            pus.PULL_UP_FGA,
            mb.PFD
        FROM
            usage_boxscores as ub
        LEFT JOIN
            game_summary as gs
                ON gs.game_id = ub.game_id
        LEFT JOIN
            player_depth as pd
                ON pd.player_id = ub.player_id
        LEFT JOIN
            traditional_boxscores as tb
                ON tb.game_id = ub.game_id
                AND tb.player_id = ub.player_id
        LEFT JOIN
            misc_boxscores as mb
                ON mb.game_id = ub.game_id
                AND mb.player_id = ub.player_id
        LEFT JOIN
            player_avg_dk as padk
                ON padk.player_id = ub.player_id
        LEFT JOIN
            sportvu_drives_game_logs as dl
                ON dl.GAME_ID = ub.GAME_ID
                and dl.PLAYER_ID = ub.PLAYER_ID
        LEFT JOIN sportvu_catch_shoot_game_logs AS cs
            ON cs.player_id = ub.player_id
            AND cs.game_id = ub.game_id
            LEFT JOIN sportvu_drives_game_logs AS dr
            ON dr.player_id = ub.player_id
            AND dr.game_id = ub.game_id
            LEFT JOIN sportvu_paint_touches_game_logs AS pt
            ON pt.player_id = ub.player_id
            AND pt.game_id = ub.game_id
            LEFT JOIN sportvu_passing_game_logs AS pass
            ON pass.player_id = ub.player_id
            AND pass.game_id = ub.game_id
            LEFT JOIN sportvu_post_touches_game_logs AS pot
            ON pot.player_id = ub.player_id
            AND pot.game_id = ub.game_id
            LEFT JOIN sportvu_pull_up_shoot_game_logs AS pus
            ON pus.player_id = ub.player_id
            AND pus.game_id = ub.game_id
        INNER JOIN
            (
                SELECT
                    tbt.game_id,
                    tbt.TEAM_ID,
                    tbt.TEAM_ABBREVIATION
                FROM
                    traditional_boxscores_team as tbt
            ) as tb2
                ON tb2.game_id = ub.game_id
                and tb2.TEAM_ID != ub.TEAM_ID
        INNER JOIN
            (
                SELECT
                    game_id
                FROM
                    traditional_boxscores
                GROUP BY
                	game_id
            ) as tb3
                ON tb3.game_id = ub.game_id
                AND STR_TO_DATE(gs.game_date_est,
            "%Y-%m-%d") >= "2016-10-25"
        LEFT JOIN
            OPP_STATS_TABLE as os
                ON os.TEAM_NAME = tb2.TEAM_ABBREVIATION
        WHERE
            tb2.TEAM_ABBREVIATION in ("BOS", "HOU", "DAL", "POR", "PHX", "LAC") and (POSITION_1 = 'PG' or POSITION_1 = 'SG')"""

    data_set = sqlfetch.execute_query(query)

    # print data_set
    feature_set = []
    sample_set = []
    minutes_set = []
    dk_set = []
    for data in data_set:
        if data['DK_POINTS'] > data['AVG_DK_POINTS']:
            sample_set.append(1)
        else:
            sample_set.append(0)

        temp_set = [float(data['FGA']), float(data['REB']), float(data['DRIVES']), float(data['CATCH_SHOOT_FGA']), \
                    float(data['PAINT_TOUCHES']), float(data['PASSES_MADE']), float(data['POST_TOUCHES']), \
                    float(data['PULL_UP_FGA']), float(data['PFD'])]
        feature_set.append(temp_set)
        minutes_set.append(process_playtime(0, data['MIN']))
        dk_set.append(data['DK_POINTS'])


    clf = tree.DecisionTreeClassifier()
    clf = clf.fit(feature_set, sample_set)
    print clf
    print clf.predict_proba([[18, 7, 10, 4, 0, 60, 0, 6, 4], [25, 7, 10, 4, 0, 60, 0, 6, 4]])
    # # Fit regression model
    # regr_1 = tree.DecisionTreeRegressor(max_depth=2)
    # regr_1.fit(feature_set, sample_set)

    # # Predict
    # X_test = [[18, 7, 10, 4, 0, 60, 0, 6, 4]]
    # y_1 = regr_1.predict(X_test)
    # # Plot the results
    # plt.figure()
    # plt.scatter(minutes_set, dk_set, c="darkorange", label="data")
    # plt.plot(X_test, y_1, color="cornflowerblue", label="max_depth=2", linewidth=2)
    # plt.xlabel("seconds played")
    # plt.ylabel("dk_points")
    # plt.title("Decision Tree Regression")
    # plt.show()

# THIS WILL BE ON HOLD
def rebound_classifier(team, oppo_fga, oppo_fgpct, oppo_pace):
    sample_query = """SELECT
                ptb.TEAM_ABBREVIATION,
                ptb.game_id,
                tb4.FGA,
                ptb.REB,
                ptb.REB_CHANCES,
                tb2.TEAM_ABBREVIATION as TEAM_AGAINST,
                tb2.FGA as OPPO_FGA,
                tb2.FG_PCT as OPPO_FG_PCT,
                ab.pace as PACE
            from
                `sportvu_rebounding_team_game_logs` as ptb
            INNER JOIN
                (
                    SELECT
                        tbt.game_id,
                        tbt.TEAM_ABBREVIATION,
                        tbt.FGA,
                        tbt.FG_PCT
                    FROM
                        traditional_boxscores_team as tbt
                ) as tb2
                    ON tb2.game_id = ptb.game_id
                    and tb2.TEAM_ABBREVIATION != ptb.TEAM_ABBREVIATION
            LEFT JOIN
                `advanced_boxscores_team` as ab
                    on ab.TEAM_ABBREVIATION = tb2.TEAM_ABBREVIATION
                    and ab.game_id = ptb.game_id
            LEFT JOIN
                traditional_boxscores_team as tb4
                    ON tb4.TEAM_ABBREVIATION = ptb.TEAM_ABBREVIATION
                    and tb4.game_id = ptb.game_id
            WHERE
                ptb.DATE >= '2015-10-25'
                AND tb2.TEAM_ABBREVIATION = '{team}'
    """.format(team=team)

    data_set = sqlfetch.execute_query(sample_query)

    feature_set = []
    sample_set = []

    for data in data_set:
        feature_set.append([int(data['OPPO_FGA']), int(data['OPPO_FG_PCT']), int(data['PACE'])])
        sample_set.append([int(data['REB']), int(data['REB_CHANCES'])])

    clf = tree.DecisionTreeClassifier()
    clf = clf.fit(feature_set, sample_set)

    # look at the possible FGA, REB and REB CHANCES, and NUM_POSS
    # If the opponent has FGA, FG%, PACE, what are the possible FGA, REB and REB CHANCES for the team
    # when other teams face this team, did their stats go up or down? compared to their avg at the time
    test_predict = clf.predict([[float(oppo_fga), float(oppo_fgpct), float(oppo_pace)]])

    return test_predict


def improve_rebound_classifier(player, oppo_fga_stats):

    sample_query = """
        SELECT IFNULL(dtgl.`DRIVE_FGA`,0) as OPP_DRIVE_FGA, 
            IFNULL(csgl.`CATCH_SHOOT_FGA`, 0) as OPP_CATCH_SHOOT_FGA, 
            IFNULL(csgl.`CATCH_SHOOT_FG3A`, 0) as OPP_CATCH_SHOOT_FG3A, 
            IFNULL(etgl.`ELBOW_TOUCH_FGA`, 0) as OPP_ELBOW_TOUCH_FGA, 
            IFNULL(pttgl.`PAINT_TOUCH_FGA`, 0) as OPP_PAINT_TOUCH_FGA, 
            IFNULL(stgl.`PULL_UP_FGA`, 0) as OPP_PULL_UP_FGA, 
            IFNULL(ptgl.`POST_TOUCH_FGA`, 0) as OPP_POST_TOUCH_FGA, 
            IFNULL(gl.`REB_CHANCES`, 0) as REB_CHANCES, 
            IFNULL(gl.`REB`, 0) as REB, 
            ab.PACE 

        FROM sportvu_rebounding_game_logs as gl 
            LEFT JOIN sportvu_post_touches_team_game_logs as ptgl ON gl.GAME_ID = ptgl.GAME_ID
                AND gl.TEAM_ID != ptgl.TEAM_ID 
            LEFT JOIN sportvu_pull_up_shoot_team_game_logs as stgl ON gl.GAME_ID = stgl.GAME_ID
                AND gl.TEAM_ID != stgl.TEAM_ID 
            LEFT JOIN sportvu_paint_touches_team_game_logs as pttgl ON gl.GAME_ID = pttgl.GAME_ID 
                AND gl.TEAM_ID != pttgl.TEAM_ID 
            LEFT JOIN sportvu_elbow_touches_team_game_logs as etgl ON gl.GAME_ID = etgl.GAME_ID
                AND gl.TEAM_ID != etgl.TEAM_ID 
            LEFT JOIN sportvu_drives_team_game_logs as dtgl on gl.GAME_ID = dtgl.GAME_ID
                AND gl.TEAM_ID != dtgl.TEAM_ID 
            LEFT JOIN sportvu_catch_shoot_team_game_logs as csgl on gl.GAME_ID = csgl.GAME_ID
                AND gl.TEAM_ID != csgl.TEAM_ID 
            LEFT JOIN
                `advanced_boxscores_team` as ab
                    on ab.TEAM_ID != gl.TEAM_ID
                    and ab.game_id = gl.game_id
            WHERE gl.PLAYER_NAME="{player}" 
    """.format(player=player)


    data_set = sqlfetch.execute_query(sample_query)

    feature_set = []
    sample_set = []
    test_predict = []
    if len(data_set) >= 1:
        for data in data_set:
            feature_set.append([int(data['OPP_DRIVE_FGA']), int(data['OPP_CATCH_SHOOT_FGA']), int(data['OPP_CATCH_SHOOT_FG3A']), \
                int(data['OPP_ELBOW_TOUCH_FGA']), int(data['OPP_PAINT_TOUCH_FGA']), int(data['OPP_PULL_UP_FGA']), int(data['OPP_POST_TOUCH_FGA']) ])
            sample_set.append([int(data['REB']), int(data['REB_CHANCES'])])

        clf = tree.DecisionTreeClassifier()
        clf = clf.fit(feature_set, sample_set)

        # look at the possible FGA, REB and REB CHANCES, and NUM_POSS
        # If the opponent has FGA, FG%, PACE, what are the possible FGA, REB and REB CHANCES for the team
        # when other teams face this team, did their stats go up or down? compared to their avg at the time
        test_predict = clf.predict([[float(oppo_fga_stats['OPP_AVG_DRIVE_FGA']), float(oppo_fga_stats['OPP_AVG_CATCH_SHOOT_FGA']), \
            float(oppo_fga_stats['OPP_AVG_CATCH_SHOOT_FG3A']), float(oppo_fga_stats['OPP_AVG_ELBOW_TOUCH_FGA']), float(oppo_fga_stats['OPP_AVG_PAINT_TOUCH_FGA']), \
            float(oppo_fga_stats['OPP_AVG_PULL_UP_FGA']), float(oppo_fga_stats['OPP_AVG_POST_TOUCH_FGA'])]])

    return test_predict
