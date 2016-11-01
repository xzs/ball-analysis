import pandas as pd
import glob
# import matplotlib.pyplot as plt
import numpy as np
# this is the standard import if you're using "formula notation" (similar to R)
import statsmodels.formula.api as smf
from sklearn.linear_model import LinearRegression


def get_simple_player_log_regression(player):
    # read data into a DataFrame and set the header of the csv to the columns
    data = pd.read_csv('nba_scrape/player_logs/'+player+'.csv', header=0)
    # data = pd.read_csv('nba_scrape/sportvu/Trevor.csv', header=0)

    if not data.empty and len(data.index) > 1:
        try:
            opp_bucket = {}
            # percentages as well? then maybe we can have a trend of on and off

            # Types of shots FGA
            opp_data = smf.ols(formula='DK_POINTS ~ DRIVE_FGA + CATCH_SHOOT_FGA + ELBOW_TOUCH_FGA + PAINT_TOUCH_FGA + POST_TOUCH_FGA + PULL_UP_FGA', data=data).fit()

            # split by 2 and 3 pointer attempts
            opp_data = smf.ols(formula='DK_POINTS ~ CATCH_SHOOT_FG2A + CATCH_SHOOT_FG3A + PULL_UP_FG2A + PULL_UP_FG3A', data=data).fit()

            # PTS origin
            opp_data = smf.ols(formula='DK_POINTS ~ DRIVE_PTS + CATCH_SHOOT_PTS + ELBOW_TOUCH_PTS + PAINT_TOUCH_PTS + POST_TOUCH_PTS + PULL_UP_PTS', data=data).fit()

            # Shots%
            opp_data = smf.ols(formula='DK_POINTS ~ DRIVE_FG_PCT + CATCH_SHOOT_FG_PCT + PULL_UP_FG_PCT + PAINT_TOUCH_FG_PCT + POST_TOUCH_FG_PCT + ELBOW_TOUCH_FG_PCT', data=data).fit()

            # AST origin
            opp_data = smf.ols(formula='DK_POINTS ~ DRIVE_AST + ELBOW_TOUCH_AST + PAINT_TOUCH_AST + POST_TOUCH_AST', data=data).fit()

            # Touches
            opp_data = smf.ols(formula='DK_POINTS ~ ELBOW_TOUCHES + POST_TOUCHES + PAINT_TOUCHES + FRONT_CT_TOUCHES', data=data).fit()

            # Holding Ball
            opp_data = smf.ols(formula='DK_POINTS ~ TIME_OF_POSS + AVG_SEC_PER_TOUCH + AVG_DRIB_PER_TOUCH', data=data).fit()

            # Passing
            opp_data = smf.ols(formula='DK_POINTS ~ PASSES_MADE + PASSES_RECEIVED', data=data).fit()

            # Drives
            opp_data = smf.ols(formula='DK_POINTS ~ DRIVES + DRIVE_PF', data=data).fit()

            # willingness to rebound
            opp_data = smf.ols(formula='DK_POINTS ~ OREB_CONTEST + DREB_CONTEST + OREB_UNCONTEST + DREB_UNCONTEST', data=data).fit()



            # reb_data = smf.ols(formula='REB ~ avgFGA', data=data).fit()
            # print reb_data.summary()
            # print np.corrcoef(data['avgFGA'],data['REB'])[0,1]

            # test stuff from the /test folder
            # Use r-squared and pvalues to determine how closely the data is linked/fitted (if there are any connection)
            opp_data = smf.ols(formula='DK_POINTS ~ PTS_PAINT', data=data).fit()
            # print opp_data.summary()
            print 'here'
            # find the correlation to see if there is any relation (if one rises so the other other)
            # print np.corrcoef(data['DRIVES'],data['PFD'])[0,1]
            for key, value in opp_data.pvalues.iteritems():
                if value < 0.05 and key != 'Intercept':
                    opp_bucket[key] = value


        except ValueError:  #raised if `y` is empty.
            pass


# # read data into a DataFrame and set the header of the csv to the columns
# data = pd.read_csv('nba_scrape/test/againstUTA.csv', header=0)
# # data = pd.read_csv('nba_scrape/sportvu/Trevor.csv', header=0)

# if not data.empty and len(data.index) > 1:
#     try:
#         opp_bucket = {}
#         # percentages as well? then maybe we can have a trend of on and off

#         # Types of shots FGA
#         opp_data = smf.ols(formula='DK_POINTS ~ DRIVE_FGA + CATCH_SHOOT_FGA + ELBOW_TOUCH_FGA + PAINT_TOUCH_FGA + POST_TOUCH_FGA + PULL_UP_FGA', data=data).fit()

#         # split by 2 and 3 pointer attempts
#         opp_data = smf.ols(formula='DK_POINTS ~ CATCH_SHOOT_FG2A + CATCH_SHOOT_FG3A + PULL_UP_FG2A + PULL_UP_FG3A', data=data).fit()

#         # PTS origin
#         opp_data = smf.ols(formula='DK_POINTS ~ DRIVE_PTS + CATCH_SHOOT_PTS + ELBOW_TOUCH_PTS + PAINT_TOUCH_PTS + POST_TOUCH_PTS + PULL_UP_PTS', data=data).fit()

#         # Shots%
#         opp_data = smf.ols(formula='DK_POINTS ~ DRIVE_FG_PCT + CATCH_SHOOT_FG_PCT + PULL_UP_FG_PCT + PAINT_TOUCH_FG_PCT + POST_TOUCH_FG_PCT + ELBOW_TOUCH_FG_PCT', data=data).fit()

#         # AST origin
#         opp_data = smf.ols(formula='DK_POINTS ~ DRIVE_AST + ELBOW_TOUCH_AST + PAINT_TOUCH_AST + POST_TOUCH_AST', data=data).fit()

#         # Touches
#         opp_data = smf.ols(formula='DK_POINTS ~ ELBOW_TOUCHES + POST_TOUCHES + PAINT_TOUCHES + FRONT_CT_TOUCHES', data=data).fit()

#         # Holding Ball
#         opp_data = smf.ols(formula='DK_POINTS ~ TIME_OF_POSS + AVG_SEC_PER_TOUCH + AVG_DRIB_PER_TOUCH', data=data).fit()

#         # Passing
#         opp_data = smf.ols(formula='DK_POINTS ~ PASSES_MADE + PASSES_RECEIVED', data=data).fit()

#         # Drives
#         opp_data = smf.ols(formula='DK_POINTS ~ DRIVES + DRIVE_PF', data=data).fit()

#         # willingness to rebound
#         opp_data = smf.ols(formula='DK_POINTS ~ OREB_CONTEST + DREB_CONTEST + OREB_UNCONTEST + DREB_UNCONTEST', data=data).fit()



#         # reb_data = smf.ols(formula='REB ~ avgFGA', data=data).fit()
#         # print reb_data.summary()
#         # print np.corrcoef(data['avgFGA'],data['REB'])[0,1]

#         # test stuff from the /test folder
#         # Use r-squared and pvalues to determine how closely the data is linked/fitted (if there are any connection)
#         opp_data = smf.ols(formula='DK_POINTS ~ PTS_PAINT', data=data).fit()
#         print opp_data.summary()
#         # find the correlation to see if there is any relation (if one rises so the other other)
#         print np.corrcoef(data['DRIVES'],data['PFD'])[0,1]
#         for key, value in opp_data.pvalues.iteritems():
#             if value < 0.05 and key != 'Intercept':
#                 opp_bucket[key] = value


#     except ValueError:  #raised if `y` is empty.
#         pass

# # def correlation_matrix(df,file):
# #     import numpy as np
# #     from matplotlib import pyplot as plt
# #     from matplotlib import cm as cm

# #     fig = plt.figure()
# #     ax1 = fig.add_subplot(111)
# #     cmap = cm.get_cmap('jet', 60)
# #     cax = ax1.imshow(df.corr(), interpolation="nearest", cmap=cmap)
# #     ax1.grid(True)
# #     plt.title('Correlation against Position' + file)
# #     # vs
# #     labels=df.columns.tolist()
# #     print labels
# #     ax1.yticks = labels
# #     ax1.xticks = labels
# #     ax1.set_xticklabels(labels,fontsize=12)
# #     ax1.set_yticklabels(labels,fontsize=12)
# #     # Add colorbar, make sure to specify tick locations to match desired ticklabels
# #     cbar = fig.colorbar(cax)
# #     plt.show()

# # # data = pd.read_csv('nba_scrape/player_synergy/DeMar DeRozan2.csv', header=0)
# # # print data.corr()
# # # correlation_matrix(data, 'DeMaR')

# # data = pd.read_csv('nba_scrape/query_result.csv', header=0)
# # print data.corr()
# # correlation_matrix(data, 'DeMaR')
# # # for file in glob.glob('nba_scrape/test/*.csv'):
# # #     data = pd.read_csv(file, header=0)
# # #     print data.columns.tolist()
# # #     if not data.empty and len(data.index) > 1:
# # #         try:
# # #             # print data.corr()
# # #             correlation_matrix(data, file)
# # #             # print np.corrcoef(data['DRIVES'],data['PFD'])[0,1]
# # #         except ValueError:  #raised if `y` is empty.
# # #             pass


