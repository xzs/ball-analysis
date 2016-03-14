import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
# this is the standard import if you're using "formula notation" (similar to R)
import statsmodels.formula.api as smf


# read data into a DataFrame
data = pd.read_csv('/Users/xunzhisun/Documents/Git/ball-analysis/app/scrape/player_logs/2016/Dion Waiters.csv')
data.columns = ['Rk', 'G', 'Date', 'Age', 'Tm', 'Loc', 'Opp', 'Mgn', 'GS', 'MP', 'FG', 'FGA', 'FG%', '3P', '3PA', '3P%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS', 'GmSc', '+/-', 'DFS', 'Pos']


# # visualize the relationship between the features and the response using scatterplots
# fig, axs = plt.subplots(1, 3, sharey=True)
# print axs
data.plot(kind='scatter', x='+/-', y='DFS', figsize=(16, 8))
# data.plot(kind='scatter', x='Radio', y='DFS', ax=axs[1])
# data.plot(kind='scatter', x='Newspaper', y='DFS', ax=axs[2])


# # create a fitted model in one line
# lm = smf.ols(formula='Sales ~ TV', data=data).fit()

# # print the coefficients
# lm.params
# # print lm.params

# # you have to create a DataFrame since the Statsmodels formula interface expects it
# X_new = pd.DataFrame({'TV': [50]})
# X_new.head()

# # use the model to make predictions on a new value
# lm.predict(X_new)

# # create a DataFrame with the minimum and maximum values of TV
# X_new = pd.DataFrame({'TV': [data.TV.min(), data.TV.max()]})

# # make predictions for those x values and store them
# preds = lm.predict(X_new)

# # first, plot the observed data
# data.plot(kind='scatter', x='TV', y='Sales')

# # then, plot the least squares line
# plt.plot(X_new, preds, c='red', linewidth=2)

# # print the confidence intervals for the model coefficients
# print lm.conf_int()

# # print the R-squared value for the model
# print lm.rsquared
plt.show()