import pandas as pd
import glob
# import matplotlib.pyplot as plt
import numpy as np
# this is the standard import if you're using "formula notation" (similar to R)
import statsmodels.formula.api as smf
from sklearn.linear_model import LinearRegression


# read data into a DataFrame and set the header of the csv to the columns
data = pd.read_csv('nba_scrape/sportvu/Trevor.csv', header=0)

if not data.empty and len(data.index) > 1:
    try:
        opp_bucket = {}
        # percentages as well? then maybe we can have a trend of on and off

        # # Types of shots FGA
        opp_data = smf.ols(formula='REB ~ avgPace', data=data).fit()
        # opp_data = smf.ols(formula='DK_POINTS ~ DRIVE_FGA + CATCH_SHOOT_FGA + ELBOW_TOUCH_FGA + PAINT_TOUCH_FGA + POST_TOUCH_FGA + PULL_UP_FGA', data=data).fit()

        # # split by 2 and 3 pointer attempts
        # opp_data = smf.ols(formula='DK_POINTS ~ CATCH_SHOOT_FG2A + CATCH_SHOOT_FG3A + PULL_UP_FG2A + PULL_UP_FG3A', data=data).fit()

        # # PTS origin
        # opp_data = smf.ols(formula='DK_POINTS ~ DRIVE_PTS + CATCH_SHOOT_PTS + ELBOW_TOUCH_PTS + PAINT_TOUCH_PTS + POST_TOUCH_PTS + PULL_UP_PTS', data=data).fit()

        # # Shots%
        # opp_data = smf.ols(formula='DK_POINTS ~ DRIVE_FG_PCT + CATCH_SHOOT_FG_PCT + PULL_UP_FG_PCT + PAINT_TOUCH_FG_PCT + POST_TOUCH_FG_PCT + ELBOW_TOUCH_FG_PCT', data=data).fit()

        # # AST origin
        # opp_data = smf.ols(formula='DK_POINTS ~ DRIVE_AST + ELBOW_TOUCH_AST + PAINT_TOUCH_AST + POST_TOUCH_AST', data=data).fit()

        # # Touches
        # opp_data = smf.ols(formula='DK_POINTS ~ ELBOW_TOUCHES + POST_TOUCHES + PAINT_TOUCHES + FRONT_CT_TOUCHES', data=data).fit()

        # # Holding Ball
        # opp_data = smf.ols(formula='DK_POINTS ~ TIME_OF_POSS + AVG_SEC_PER_TOUCH + AVG_DRIB_PER_TOUCH', data=data).fit()

        # # Passing
        # opp_data = smf.ols(formula='DK_POINTS ~ PASSES_MADE + PASSES_RECEIVED', data=data).fit()

        # # Drives
        # opp_data = smf.ols(formula='DK_POINTS ~ DRIVES + DRIVE_PF', data=data).fit()

        # # willingness to rebound
        # opp_data = smf.ols(formula='DK_POINTS ~ OREB_CONTEST + DREB_CONTEST + OREB_UNCONTEST + DREB_UNCONTEST', data=data).fit()
        # opp_data = smf.ols(formula='DK_POINTS ~ OREB_CHANCES + DREB_CHANCES', data=data).fit()


        print opp_data.summary()
        for key, value in opp_data.pvalues.iteritems():
            if value < 0.05 and key != 'Intercept':
                opp_bucket[key] = value


    except ValueError:  #raised if `y` is empty.
        pass
