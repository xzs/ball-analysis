
import pandas as pd
import glob
# import matplotlib.pyplot as plt
# import numpy as np
# this is the standard import if you're using "formula notation" (similar to R)
import statsmodels.formula.api as smf
# from sklearn.linear_model import LinearRegression
YEAR = '2016'

ISSUE_NAMES = ['../scrape/mod_player_logs/'+YEAR+'/Kelly Oubre Jr..csv', '../scrape/mod_player_logs/'+YEAR+'/Nene.csv', '../scrape/mod_player_logs/'+YEAR+'/Patty Mills.csv']

for file in glob.glob('../scrape/mod_player_logs/'+YEAR+'/*.csv'):

    # issue with names
    if file not in ISSUE_NAMES:
    # read data into a DataFrame
        data = pd.read_csv(file)

        # we also need to do it for past n games
        # Maybes:
        # How many times was the player in last game

        # Players vary in terms of which component correlates best to FPS
        # Ex. a player like marreese speights is strongly correlated to FGA
        # Whereas other players might be strongly correlated to MP

        if not data.empty and len(data.index) > 1:
            try:
                print file
                oppData = smf.ols(formula='DFS ~ OppPace + OppDvP + OppPF + OppFGA + OppDRtg + OppORtg + OppTOVPercent + OppDefgPercent + Opp3PPercent + OppTRB + OppAST + OppPTSPerG + OppFGPercent + OppSTL + OppFTA + OppBLK + OppTOV', data=data).fit()
                for key, value in oppData.pvalues.iteritems():
                    if value <= 0.2:
                        print key, value

                playerData = smf.ols(formula='DFS ~ G + isHome + Margin + GS + MP', data=data).fit()
                for key, value in playerData.pvalues.iteritems():
                    if value <= 0.2:
                        print key, value
            except ValueError:  #raised if `y` is empty.
                pass




# scikit-learn
# create X and y
# feature_cols = ['OppPace','OppDvP','OppPF','OppFGA','OppDRtg','OppORtg','OppTOVPercent','OppDefgPercent','Opp3PPercent','OppTRB','OppAST','OppPTSPerG','OppFGPercent','OppSTL','OppFTA','OppBLK','OppTOV']
# X = data[feature_cols]
# y = data.DFS

# # instantiate, fit
# regr = LinearRegression()
# regr.fit(X, y)

# # The coefficients
# print('Coefficients: \n', regr.coef_)
# # The mean square error
# print("Residual sum of squares: %.2f"
#       % np.mean((regr.predict(X) - y) ** 2))
# # Explained variance score: 1 is perfect prediction
# print('Variance score: %.2f' % regr.score(X, y))


# plt.show()