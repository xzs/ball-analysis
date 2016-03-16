import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
# this is the standard import if you're using "formula notation" (similar to R)
import statsmodels.formula.api as smf
from sklearn.linear_model import LinearRegression


# read data into a DataFrame
data = pd.read_csv('/Users/xunzhisun/Documents/Git/ball-analysis/app/scrape/mod_player_logs/2016/Stephen Curry.csv')
# data.columns = ['Rk', 'G', 'Date', 'Age', 'Tm', 'Loc', 'Opp', 'Mgn', 'GS', 'MP', 'FG', 'FGA', 'FG%', '3P', '3PA', '3P%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS', 'GmSc', '+/-', 'DFS', 'Pos']


# # visualize the relationship between the features and the response using scatterplots
# fig = plt.subplots(1, 3, sharey=True)
# print axs
data.plot(kind='scatter', x='OppFGA', y='DFS', figsize=(16, 8))
# data.plot(kind='scatter', x='MP', y='DFS', figsize=(16, 8))


# Maybes:
# How many times was the player in last game

# Players vary in terms of which component correlates best to FPS
# Ex. a player like marreese speights is strongly correlated to FGA
# Whereas other players might be strongly correlated to MP

# we need to get matchup strength
lm = smf.ols(formula='DFS ~ OppPace + OppDvP + OppPF + OppFGA + OppDRtg + OppORtg + OppTOVPercent + OppDefgPercent + OppPTS', data=data).fit()
print lm.pvalues

# olm = smf.ols(formula='DFS ~ isHome + isConference + Margin + GS', data=data).fit()
# print olm.pvalues

# create X and y
# feature_cols = ['isHome', 'isConference', 'Margin', 'GS']
feature_cols = ['OppPace','OppDvP','OppPF','OppFGA','OppDRtg','OppORtg','OppTOVPercent','OppDefgPercent','OppPTS']
X = data[feature_cols]
y = data.DFS

# instantiate, fit
regr = LinearRegression()
regr.fit(X, y)

# The coefficients
print('Coefficients: \n', regr.coef_)
# The mean square error
print("Residual sum of squares: %.2f"
      % np.mean((regr.predict(X) - y) ** 2))
# Explained variance score: 1 is perfect prediction
print('Variance score: %.2f' % regr.score(X, y))


plt.show()