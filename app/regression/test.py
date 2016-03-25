import json
import logging
import pandas as pd
import glob
# import matplotlib.pyplot as plt
import numpy as np
# this is the standard import if you're using "formula notation" (similar to R)
import statsmodels.formula.api as smf
from sklearn.linear_model import LinearRegression
from sklearn.cross_validation import cross_val_score
YEAR = '2016'
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ISSUE_NAMES = ['Kelly Oubre Jr.', 'Nene', 'Patty Mills', 'Xavier Munford']

for file in glob.glob('../scrape/mod_player_logs/'+YEAR+'/*.csv'):
    player_name = file.split('/')[4].split('.c')[0]

    # issue with names
    if player_name not in ISSUE_NAMES:
    # read data into a DataFrame
        data = pd.read_csv(file)
        # python variables cannot start with a number sp 3PA -> ThreePA
        data.columns = ['Rk','G','Date','Age','Tm','isHome','Opp','Margin','GS','MP','FG','FGA',
        'FGPercent','ThreeP','ThreePA','ThreePPercent','FT','FTA','FTPercent','ORB','DRB','TRB','AST','STL','BLK','TOV','PF',
        'PTS','GmSc','+/-','DFS','Pos','OppDvP','OppPace','OppPF','OppFGA','OppDRtg','OppORtg','OppTOVPercent',
        'OppDefgPercent','Opp3PPercentAllowed','OppTRBAllowed','OppASTAllowed','OppPTSPerGAllowed','OppFGPercentAllowed','OppSTLAllowed','OppFTAAllowed','OppBLKAllowed','OppTOVAllowed','TRBPercent','isConference']

        # we also need to do it for past n games
        # Maybes:
        # How many times was the player in last game

        # Players vary in terms of which component correlates best to FPS
        # Ex. a player like marreese speights is strongly correlated to FGA
        # Whereas other players might be strongly correlated to MP
        # 'Opp3PPercent',OppTRB + OppAST + OppPTSPerG + OppFGPercent + OppSTL + OppFTA + OppBLK
        if not data.empty and len(data.index) > 1:
            try:
                opp_bucket = {}
                opp_data = smf.ols(formula='DFS ~ OppPace + OppDvP', data=data).fit()
                for key, value in opp_data.pvalues.iteritems():
                    if value < 0.05 and key != 'Intercept':
                        opp_bucket[key] = value

                opp_team_bucket = {}
                opp_team_data = smf.ols(formula='DFS ~ OppPF + OppFGA + OppDRtg + OppORtg + OppDefgPercent', data=data).fit()
                for key, value in opp_team_data.pvalues.iteritems():
                    if value < 0.05 and key != 'Intercept':
                        opp_team_bucket[key] = value

                opp_def_bucket = {}
                opp_def_data = smf.ols(formula='DFS ~ Opp3PPercentAllowed + OppTRBAllowed + OppASTAllowed + OppPTSPerGAllowed + OppFGPercentAllowed + OppSTLAllowed + OppFTAAllowed + OppBLKAllowed', data=data).fit()
                for key, value in opp_def_data.pvalues.iteritems():
                    if value < 0.05 and key != 'Intercept':
                        opp_def_bucket[key] = value

                game_bucket = {}
                game_data = smf.ols(formula='DFS ~ G + isHome + Margin + GS', data=data).fit()
                for key, value in game_data.pvalues.iteritems():
                    if value < 0.05 and key != 'Intercept':
                        game_bucket[key] = value

                temp_bucket = {}
                player_box_score = smf.ols(formula='DFS ~ FTA + TRB + FGA + ThreePA + AST + STL + BLK + PTS + MP', data=data).fit()
                for key, value in player_box_score.pvalues.iteritems():
                    if value < 0.05 and key != 'Intercept':
                        temp_bucket[key] = value

                stat_bucket = {}
                # get the top 3 things that matter
                for stat in sorted(temp_bucket.items(), key=lambda x: x[1])[:3]:
                    stat_bucket[stat[0]] = stat[1]

            except ValueError:  #raised if `y` is empty.
                pass

    with open('../scrape/json_files/player_logs/'+YEAR+'/'+player_name+'.json') as data_file:
        PLAYER_DICT = json.load(data_file)

        PLAYER_DICT['regression'] = {}
        PLAYER_DICT['regression']['opp_data'] = opp_bucket
        PLAYER_DICT['regression']['opp_team_data'] = opp_team_bucket
        PLAYER_DICT['regression']['opp_def_data'] = opp_def_bucket
        PLAYER_DICT['regression']['game_data'] = game_bucket
        PLAYER_DICT['regression']['player_box_score'] = stat_bucket

    logger.info('Dumping json for: '+player_name)
    with open('../scrape/json_files/player_logs/'+YEAR+'/'+player_name+'.json', 'w') as outfile:
        json.dump(PLAYER_DICT, outfile)

'''
    # scikit-learn
    # create X and y
    opp_data_feature_cols = ['OppPace', 'OppDvP']
    opp_team_data_feature_cols = ['OppPF', 'OppFGA', 'OppDRtg', 'OppORtg', 'OppDefgPercent']
    opp_def_data_feature_cols = ['Opp3PPercentAllowed', 'OppTRBAllowed', 'OppASTAllowed', 'OppPTSPerGAllowed', 'OppFGPercentAllowed', 'OppSTLAllowed', 'OppFTAAllowed', 'OppBLKAllowed']
    player_box_score_feature_cols = ['FTA', 'TRB', 'FGA', 'ThreePA', 'AST', 'STL', 'BLK', 'PTS', 'MP']
    # feature_cols = ['G', 'isHome', 'Margin', 'GS']
    opp_data_X = data[opp_data_feature_cols]
    opp_team_data_X = data[opp_team_data_feature_cols]
    opp_def_data_X = data[opp_def_data_feature_cols]
    player_box_score_X = data[player_box_score_feature_cols]
    y = data.DFS

    # # instantiate, fit
    regr = LinearRegression()

    try:
        opp_data_rmse_scores = np.sqrt(-cross_val_score(regr, opp_data_X, y, cv=10, scoring='mean_squared_error')).mean()
        opp_team_data_rmse_scores = np.sqrt(-cross_val_score(regr, opp_team_data_X, y, cv=10, scoring='mean_squared_error')).mean()
        opp_def_data_rmse_scores = np.sqrt(-cross_val_score(regr, opp_def_data_X, y, cv=10, scoring='mean_squared_error')).mean()
        player_box_score_rmse_scores = np.sqrt(-cross_val_score(regr, player_box_score_X, y, cv=10, scoring='mean_squared_error')).mean()
        # opp_data_rmse_scores = np.sqrt(-cross_val_score(regr, X, y, cv=10, scoring='mean_squared_error')).mean()

        print 'opp_data: %s' % opp_data_rmse_scores.mean()
        print 'opp_team_data: %s' % opp_team_data_rmse_scores.mean()
        print 'opp_def_data: %s' % opp_def_data_rmse_scores.mean()
        print 'player_box_score: %s' % player_box_score_rmse_scores.mean()
        # print 'game_data: %s' % rmse_scores.mean()
        # print 'player_box_score: %s' % rmse_scores.mean()
        # regr.fit(X, y)
        # print regr.score(X, y)
    except ValueError:  #raised if `y` is empty.
        pass
'''
# # The coefficients
# # The mean square error
#       % np.mean((regr.predict(X) - y) ** 2))
# # Explained variance score: 1 is perfect prediction


# plt.show()