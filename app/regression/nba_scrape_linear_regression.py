import pandas as pd
import glob
# import matplotlib.pyplot as plt
import numpy as np
# this is the standard import if you're using "formula notation" (similar to R)
import statsmodels.formula.api as smf
from sklearn.linear_model import LinearRegression


# read data into a DataFrame
data = pd.read_csv('test/file.csv')

data.columns = ['GAME_ID','DATE','NAME','TEAM','TEAM_AGAINST','START_POSITION','MIN',
                'USG_PCT','PCT_FGA','PCT_FG3A','PCT_FTA','PCT_REB','PCT_AST','PCT_TOV','PCT_STL','PCT_BLK','PCT_PF','PCT_PTS',
                'FGA','FG_PCT','FG3M','FG3A','FG3_PCT','FTA','FT_PCT','REB','AST','STL','BLK','TO','PF','PTS','DK_POINTS',
                'PLUS_MINUS','REB_CHANCES','TOUCHES','PASS','AST_PER_PASS','CONTESTED_FGA','CONTESTED_FG_PCT',
                'OFF_RATING','DEF_RATING','NET_RATING','AST_PCT','REB_PCT','EFG_PCT','PACE',
                'PCT_FGA_2PT','PCT_FGA_3PT','PCT_PTS_2PT','PCT_PTS_3PT','PCT_PTS_OFF_TOV','PCT_PTS_PAINT',
                'OPP_EFG_PCT','OPP_FTA_RATE','OPP_TOV_PCT','OPP_OREB_PCT',
                'PTS_OFF_TOV','PTS_FB','PTS_2ND_CHANCE','PTS_PAINT',
                'OPP_PTS_OFF_TOV','OPP_PTS_2ND_CHANCE','OPP_PTS_FB','OPP_PTS_PAINT','OPP_PTS_2ND_CHANCE',
                'PFD','NATIONAL_TV']

if not data.empty and len(data.index) > 1:
    try:
        opp_bucket = {}
        opp_data = smf.ols(formula='DK_POINTS ~ PCT_FGA + PCT_FG3A + PCT_FTA + PCT_REB + PCT_AST + PCT_TOV + PCT_STL + PCT_BLK + PCT_PF + PCT_PTS', data=data).fit()
        for key, value in opp_data.pvalues.iteritems():
            if value < 0.05 and key != 'Intercept':
                opp_bucket[key] = value

        # player movement
        opp_def_bucket = {}
        opp_def_data = smf.ols(formula='DK_POINTS ~ REB_CHANCES + TOUCHES + PASS + PFD', data=data).fit()
        print opp_def_data.summary()
        for key, value in opp_def_data.pvalues.iteritems():
            if value < 0.05 and key != 'Intercept':
                opp_def_bucket[key] = value

        opp_team_bucket = {}
        opp_team_data = smf.ols(formula='DK_POINTS ~ PTS_OFF_TOV + PTS_FB + PTS_2ND_CHANCE + PTS_PAINT', data=data).fit()
        for key, value in opp_team_data.pvalues.iteritems():
            if value < 0.05 and key != 'Intercept':
                opp_team_bucket[key] = value

    except ValueError:  #raised if `y` is empty.
        pass
