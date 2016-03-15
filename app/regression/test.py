import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
# this is the standard import if you're using "formula notation" (similar to R)
import statsmodels.formula.api as smf


# read data into a DataFrame
data = pd.read_csv('/Users/xunzhisun/Documents/Git/ball-analysis/app/scrape/mod_player_logs/2016/Dwight Howard.csv')
# data.columns = ['Rk', 'G', 'Date', 'Age', 'Tm', 'Loc', 'Opp', 'Mgn', 'GS', 'MP', 'FG', 'FGA', 'FG%', '3P', '3PA', '3P%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS', 'GmSc', '+/-', 'DFS', 'Pos']


# # visualize the relationship between the features and the response using scatterplots
# fig = plt.subplots(1, 3, sharey=True)
# print axs
# data.plot(kind='scatter', x='OppFGA', y='TRB', figsize=(16, 8))
# data.plot(kind='scatter', x='MP', y='DFS', figsize=(16, 8))
# data.plot(kind='scatter', x='isHome', y='DFS', figsize=(16, 8))
# data.plot(kind='scatter', x='isConference', y='DFS', figsize=(16, 8))


# # create a fitted model in one line
# lm = smf.ols(formula='DFS ~ OppPace', data=data).fit()
TRBvsOppFGA = smf.ols(formula='TRB ~ OppFGA + OppORtg', data=data).fit()
print TRBvsOppFGA.summary()

# Maybes:
# How many times was the player in last game

# Players vary in terms of which component correlates best to FPS
# Ex. a player like marreese speights is strongly correlated to FGA
# Whereas other players might be strongly correlated to MP

lm = smf.ols(formula='DFS ~ OppPace + OppDvP + OppPF + OppFGA + OppDRtg + OppTOV + OppPTS + Margin + isHome + MP + isConference + GS + FTA + FGA + PF', data=data).fit()
print lm.summary()


# # print the coefficients
# lm.params
print lm.params

# # use the model to make predictions on a new value
# lm.predict(X_new)

# # create a DataFrame with the minimum and maximum values of OppPace
# X_new = pd.DataFrame({'OppPace': [data.OppPace.min(), data.OppPace.max()]})

# # make predictions for those x values and store them
# preds = lm.predict(X_new)

# # first, plot the observed data
# data.plot(kind='scatter', x='OppPace', y='DFS', figsize=(16, 8))

# data.plot(kind='scatter', x='TV', y='Sales')

# # then, plot the least squares line
# plt.plot(X_new, preds, c='red', linewidth=2)


# # print the confidence intervals for the model coefficients
# print lm.conf_int()

# # print the R-squared value for the model
# print lm.rsquared
plt.show()