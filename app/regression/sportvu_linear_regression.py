import pandas as pd
import glob
# import matplotlib.pyplot as plt
import numpy as np
# this is the standard import if you're using "formula notation" (similar to R)
import statsmodels.formula.api as smf
from sklearn.linear_model import LinearRegression


# read data into a DataFrame
data = pd.read_csv('nba_scrape/sportvu/MEM.csv')

# data.columns = ['PLAYER_ID','PLAYER_NAME','TEAM_ID','TEAM_ABBREVIATION','GAME_ID','GP','W','L','MIN',
#                 'DRIVES','DRIVE_FGM','DRIVE_FGA','DRIVE_FG_PCT','DRIVE_FTM','DRIVE_FTA','DRIVE_FT_PCT','DRIVE_PTS',
#                 'DRIVE_PTS_PCT','DRIVE_PASSES','DRIVE_PASSES_PCT','DRIVE_AST','DRIVE_AST_PCT','DRIVE_TOV','DRIVE_TOV_PCT',
#                 'DRIVE_PF','DRIVE_PF_PCT','DATE','IS_REGULAR_SEASON','GAME_ID','PLAYER_NAME','DK_POINTS']

# data.columns = ['PLAYER_ID','PLAYER_NAME','TEAM_ID','TEAM_ABBREVIATION','GAME_ID','GP','W','L','MIN',
#                 'CATCH_SHOOT_FGM','CATCH_SHOOT_FGA','CATCH_SHOOT_FG_PCT','CATCH_SHOOT_PTS',
#                 'CATCH_SHOOT_FG3M','CATCH_SHOOT_FG3A','CATCH_SHOOT_FG3_PCT','CATCH_SHOOT_EFG_PCT',
#                 'DATE','IS_REGULAR_SEASON','GAME_ID','PLAYER_NAME','DK_POINTS']

# data.columns = ['PLAYER_ID','PLAYER_NAME','TEAM_ID','TEAM_ABBREVIATION','GAME_ID','GP','W','L','MIN',
#                 'ELBOW_TOUCHES','ELBOW_TOUCH_FGM','ELBOW_TOUCH_FGA','ELBOW_TOUCH_FG_PCT',
#                 'ELBOW_TOUCH_FTM','ELBOW_TOUCH_FTA','ELBOW_TOUCH_FT_PCT','ELBOW_TOUCH_PTS','ELBOW_TOUCH_PTS_PCT',
#                 'ELBOW_TOUCH_PASSES','ELBOW_TOUCH_PASSES_PCT','ELBOW_TOUCH_AST','ELBOW_TOUCH_AST_PCT',
#                 'ELBOW_TOUCH_TOV','ELBOW_TOUCH_TOV_PCT','ELBOW_TOUCH_FOULS','ELBOW_TOUCH_FOULS_PCT',
#                 'DATE','IS_REGULAR_SEASON','GAME_ID','PLAYER_NAME','DK_POINTS']

# data.columns = ['PLAYER_ID','PLAYER_NAME','TEAM_ID','TEAM_ABBREVIATION','GAME_ID','GP','W','L','MIN',
#                 'PAINT_TOUCHES','PAINT_TOUCH_FGM','PAINT_TOUCH_FGA','PAINT_TOUCH_FG_PCT',
#                 'PAINT_TOUCH_FTM','PAINT_TOUCH_FTA','PAINT_TOUCH_FT_PCT','PAINT_TOUCH_PTS','PAINT_TOUCH_PTS_PCT',
#                 'PAINT_TOUCH_PASSES','PAINT_TOUCH_PASSES_PCT','PAINT_TOUCH_AST','PAINT_TOUCH_AST_PCT',
#                 'PAINT_TOUCH_TOV','PAINT_TOUCH_TOV_PCT','PAINT_TOUCH_FOULS','PAINT_TOUCH_FOULS_PCT',
#                 'DATE','IS_REGULAR_SEASON','GAME_ID','PLAYER_NAME','DK_POINTS']

data.columns = ['TEAM_ID','TEAM_NAME','TEAM_ABBREVIATION','GAME_ID','GP','W','L','MIN',
                'PAINT_TOUCHES','PAINT_TOUCH_FGM','PAINT_TOUCH_FGA','PAINT_TOUCH_FG_PCT',
                'PAINT_TOUCH_FTM','PAINT_TOUCH_FTA','PAINT_TOUCH_FT_PCT','PAINT_TOUCH_PTS','PAINT_TOUCH_PTS_PCT',
                'PAINT_TOUCH_PASSES','PAINT_TOUCH_PASSES_PCT','PAINT_TOUCH_AST','PAINT_TOUCH_AST_PCT',
                'PAINT_TOUCH_TOV','PAINT_TOUCH_TOV_PCT','PAINT_TOUCH_FOULS','PAINT_TOUCH_FOULS_PCT',
                'DATE','IS_REGULAR_SEASON','GAME_ID','TEAM_ABBREVIATION','DK_POINTS']


# data.columns = ['PLAYER_ID','PLAYER_NAME','TEAM_ID','TEAM_ABBREVIATION','GAME_ID','GP','W','L','MIN',
#                 'PASSES_MADE','PASSES_RECEIVED','AST','FT_AST','SECONDARY_AST','POTENTIAL_AST',
#                 'AST_PTS_CREATED','AST_ADJ','AST_TO_PASS_PCT','AST_TO_PASS_PCT_ADJ',
#                 'DATE','IS_REGULAR_SEASON','GAME_ID','PLAYER_NAME','DK_POINTS']

# data.columns = ['PLAYER_ID','PLAYER_NAME','TEAM_ID','TEAM_ABBREVIATION','GAME_ID','GP','W','L','MIN',
#                 'POINTS','TOUCHES','FRONT_CT_TOUCHES','TIME_OF_POSS','AVG_SEC_PER_TOUCH','AVG_DRIB_PER_TOUCH',
#                 'PTS_PER_TOUCH','ELBOW_TOUCHES','POST_TOUCHES','PAINT_TOUCHES',
#                 'PTS_PER_ELBOW_TOUCH','PTS_PER_POST_TOUCH','PTS_PER_PAINT_TOUCH',
#                 'DATE','IS_REGULAR_SEASON','GAME_ID','PLAYER_NAME','DK_POINTS']

# data.columns = ['PLAYER_ID','PLAYER_NAME','TEAM_ID','TEAM_ABBREVIATION','GAME_ID','GP','W','L','MIN',
#                 'TOUCHES','POST_TOUCHES','POST_TOUCH_FGM','POST_TOUCH_FGA','POST_TOUCH_FG_PCT',
#                 'POST_TOUCH_FTM','POST_TOUCH_FTA','POST_TOUCH_FT_PCT','POST_TOUCH_PTS','POST_TOUCH_PTS_PCT',
#                 'POST_TOUCH_PASSES','POST_TOUCH_PASSES_PCT','POST_TOUCH_AST','POST_TOUCH_AST_PCT',
#                 'POST_TOUCH_TOV','POST_TOUCH_TOV_PCT','POST_TOUCH_FOULS','POST_TOUCH_FOULS_PCT',
#                 'DATE','IS_REGULAR_SEASON','GAME_ID','PLAYER_NAME','DK_POINTS']

# data.columns = ['PLAYER_ID','PLAYER_NAME','TEAM_ID','TEAM_ABBREVIATION','GAME_ID','GP','W','L','MIN',
#                 'PULL_UP_FGM','PULL_UP_FGA','PULL_UP_FG_PCT','PULL_UP_FG3M','PULL_UP_FG3A','PULL_UP_FG3_PCT',
#                 'PULL_UP_PTS','PULL_UP_EFG_PCT','DATE','IS_REGULAR_SEASON','GAME_ID','PLAYER_NAME','DK_POINTS']


# data.columns = ['PLAYER_ID','PLAYER_NAME','TEAM_ID','TEAM_ABBREVIATION','GAME_ID','GP','W','L','MIN',
#                 'OREB','OREB_CONTEST','OREB_UNCONTEST','OREB_CONTEST_PCT',
#                 'OREB_CHANCES','OREB_CHANCE_PCT','OREB_CHANCE_DEFER','OREB_CHANCE_PCT_ADJ',
#                 'AVG_OREB_DIST','DREB','DREB_CONTEST','DREB_UNCONTEST','DREB_CONTEST_PCT',
#                 'DREB_CHANCES','DREB_CHANCE_PCT','DREB_CHANCE_DEFER','DREB_CHANCE_PCT_ADJ',
#                 'AVG_DREB_DIST','REB','REB_CONTEST','REB_UNCONTEST','REB_CONTEST_PCT',
#                 'REB_CHANCES','REB_CHANCE_PCT','REB_CHANCE_DEFER','REB_CHANCE_PCT_ADJ','AVG_REB_DIST',
#                 'DATE','IS_REGULAR_SEASON','GAME_ID','PLAYER_NAME','DK_POINTS']

# data.columns = ['PLAYER_ID','PLAYER_NAME','TEAM_ID','TEAM_ABBREVIATION','GAME_ID','GP','W','L','MIN',
#                 'DIST_FEET','DIST_MILES','DIST_MILES_OFF','DIST_MILES_DEF','AVG_SPEED','AVG_SPEED_OFF','AVG_SPEED_DEF',
#                 'DATE','IS_REGULAR_SEASON','GAME_ID','PLAYER_NAME','DK_POINTS']

if not data.empty and len(data.index) > 1:
    try:
        opp_bucket = {}
        # percentages as well? then maybe we can have a trend of on and off
        # opp_data = smf.ols(formula='DK_POINTS ~ DRIVES + DRIVE_FGA + DRIVE_FTA + DRIVE_PF + DRIVE_PTS', data=data).fit()
        # opp_data = smf.ols(formula='DK_POINTS ~ DRIVE_FG_PCT + DRIVE_FT_PCT + DRIVE_AST_PCT + DRIVE_PF_PCT', data=data).fit()
        # opp_data = smf.ols(formula='DK_POINTS ~ CATCH_SHOOT_FGA + CATCH_SHOOT_FG3A', data=data).fit()
        # opp_data = smf.ols(formula='DK_POINTS ~ CATCH_SHOOT_FG_PCT + CATCH_SHOOT_FG3_PCT', data=data).fit()
        # opp_data = smf.ols(formula='DK_POINTS ~ ELBOW_TOUCHES + ELBOW_TOUCH_FGA + ELBOW_TOUCH_FTA', data=data).fit()
        # opp_data = smf.ols(formula='DK_POINTS ~ ELBOW_TOUCH_FG_PCT + ELBOW_TOUCH_FT_PCT + ELBOW_TOUCH_PASSES_PCT + ELBOW_TOUCH_AST_PCT + ELBOW_TOUCH_FOULS_PCT', data=data).fit()
        # opp_data = smf.ols(formula='DK_POINTS ~ ELBOW_TOUCH_PASSES + ELBOW_TOUCH_TOV + ELBOW_TOUCH_FOULS', data=data).fit()
        opp_data = smf.ols(formula='DK_POINTS ~ PAINT_TOUCHES + PAINT_TOUCH_FGA + PAINT_TOUCH_FTA', data=data).fit()
        # opp_data = smf.ols(formula='DK_POINTS ~ PAINT_TOUCH_FG_PCT + PAINT_TOUCH_FT_PCT + PAINT_TOUCH_PASSES_PCT + PAINT_TOUCH_AST_PCT + PAINT_TOUCH_FOULS_PCT', data=data).fit()
        # opp_data = smf.ols(formula='DK_POINTS ~ PAINT_TOUCH_PASSES + PAINT_TOUCH_TOV + PAINT_TOUCH_FOULS', data=data).fit()
        # opp_data = smf.ols(formula='DK_POINTS ~ PASSES_MADE + PASSES_RECEIVED', data=data).fit()
        # opp_data = smf.ols(formula='DK_POINTS ~ TOUCHES + TIME_OF_POSS + AVG_SEC_PER_TOUCH + AVG_DRIB_PER_TOUCH', data=data).fit()
        # opp_data = smf.ols(formula='DK_POINTS ~ ELBOW_TOUCHES + POST_TOUCHES + PAINT_TOUCHES + FRONT_CT_TOUCHES', data=data).fit()
        # opp_data = smf.ols(formula='DK_POINTS ~ POST_TOUCHES + POST_TOUCH_FGA + POST_TOUCH_FTA', data=data).fit()
        # opp_data = smf.ols(formula='DK_POINTS ~ POST_TOUCH_PASSES + POST_TOUCH_TOV + POST_TOUCH_FOULS', data=data).fit()
        # opp_data = smf.ols(formula='DK_POINTS ~ PULL_UP_FGA + PULL_UP_FG3A', data=data).fit()
        # opp_data = smf.ols(formula='DK_POINTS ~ PULL_UP_FG_PCT + PULL_UP_FG3_PCT', data=data).fit()
        # see which teams give up the most chance?
        # opp_data = smf.ols(formula='DK_POINTS ~ OREB_CONTEST + DREB_CONTEST', data=data).fit()
        # opp_data = smf.ols(formula='DK_POINTS ~ OREB_CHANCES + DREB_CHANCES', data=data).fit()
        # opp_data = smf.ols(formula='DK_POINTS ~ AVG_SPEED_OFF + AVG_SPEED_DEF', data=data).fit()
        print opp_data.summary()
        for key, value in opp_data.pvalues.iteritems():
            if value < 0.05 and key != 'Intercept':
                opp_bucket[key] = value


    except ValueError:  #raised if `y` is empty.
        pass
