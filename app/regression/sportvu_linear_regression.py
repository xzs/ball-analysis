import pandas as pd
import glob
# import matplotlib.pyplot as plt
import numpy as np
# this is the standard import if you're using "formula notation" (similar to R)
import statsmodels.formula.api as smf
from sklearn.linear_model import LinearRegression


# read data into a DataFrame
data = pd.read_csv('test/file.csv')

data.columns = ['PLAYER_ID','PLAYER_NAME','TEAM_ID','TEAM_ABBREVIATION','GAME_ID','GP','W','L','MIN',
                'DRIVES','DRIVE_FGM','DRIVE_FGA','DRIVE_FG_PCT','DRIVE_FTM','DRIVE_FTA','DRIVE_FT_PCT','DRIVE_PTS',
                'DRIVE_PTS_PCT','DRIVE_PASSES','DRIVE_PASSES_PCT','DRIVE_AST','DRIVE_AST_PCT','DRIVE_TOV','DRIVE_TOV_PCT',
                'DRIVE_PF','DRIVE_PF_PCT','DATE','IS_REGULAR_SEASON','GAME_ID','PLAYER_NAME','DK_POINTS']

if not data.empty and len(data.index) > 1:
    try:
        opp_bucket = {}
        opp_data = smf.ols(formula='DK_POINTS ~ DRIVES + DRIVE_FGA + DRIVE_FTA + DRIVE_PF + DRIVE_PTS', data=data).fit()
        print opp_data.summary()
        for key, value in opp_data.pvalues.iteritems():
            if value < 0.05 and key != 'Intercept':
                opp_bucket[key] = value


    except ValueError:  #raised if `y` is empty.
        pass
