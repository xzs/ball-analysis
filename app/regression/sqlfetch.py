import MySQLdb
import json
import itertools
import pprint

pp = pprint.PrettyPrinter(indent=4)

# Open database connection
db = MySQLdb.connect("127.0.0.1","root","","nba_scrape" )

# prepare a cursor object using cursor() method
cursor = db.cursor()

# Get top 50 rim defender in the nba, sorted by fg%
sql = 'SELECT * FROM (SELECT * '\
      'FROM sportvu_defense '\
      'ORDER BY DEF_RIM_FGA DESC '\
      'LIMIT 50) vu_defense '\
      'ORDER BY DEF_RIM_FG_PCT ASC '
try:
    # Execute the SQL command
    cursor.execute(sql)
    query_result = [dict(line) for line in [zip([column[0] for column in cursor.description],
                 row) for row in cursor.fetchall()]]
    # Fetch all the rows in a list of lists.
    pp.pprint(query_result)

except:
   print "Error: unable to fetch data"

db.close()