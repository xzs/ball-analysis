import pandas as pd
import glob
# import matplotlib.pyplot as plt
import numpy as np
# this is the standard import if you're using "formula notation" (similar to R)
import statsmodels.formula.api as smf
from sklearn.linear_model import LinearRegression
from sklearn.datasets import load_iris

iris = load_iris()
# print iris.data
# print 4 * len(iris.data)
# print iris.target
def get_simple_player_log_regression(player):
    # read data into a DataFrame
    data = pd.read_csv('nba_scrape/player_logs/'+player+'.csv', header=0)
    data['IsNational'] = data.NATIONAL_TV.map({'NBA TV':1, 'ESPN':1, 'TNT':1, 'ABC':1})
    if not data.empty and len(data.index) > 1:
        try:
            opp_bucket = {}
            opp_data = smf.ols(formula='DK_POINTS ~ PCT_FGA + PCT_FG3A + PCT_FTA + PCT_REB + PCT_AST + PCT_TOV + PCT_STL + PCT_BLK + PCT_PF + PCT_PTS', data=data).fit()
            for key, value in opp_data.pvalues.iteritems():
                if value < 0.05 and key != 'Intercept':
                    opp_bucket[key] = value

            opp_team_bucket = {}
            opp_team_data = smf.ols(formula='DK_POINTS ~ FTA + PFD', data=data).fit()
            for key, value in opp_team_data.pvalues.iteritems():
                if value < 0.05 and key != 'Intercept':
                    opp_bucket[key] = value

            # opp_team_data = smf.ols(formula='DK_POINTS ~ IsNational', data=data).fit()
            pace_bucket = {}
            pace_data = smf.ols(formula='DK_POINTS ~ PACE', data=data).fit()
            for key, value in pace_data.pvalues.iteritems():
                if value < 0.05 and key != 'Intercept':
                    opp_bucket[key] = value

            return opp_bucket
        except ValueError:  #raised if `y` is empty.
            pass
