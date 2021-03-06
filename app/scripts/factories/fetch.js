app.factory('fetch', ['$http', function($http) {
    return {
        getPlayer: function(year, name) {
            return $http.get('scrape/json_files/player_logs/'+year+'/'+name+'.json').then(function (response) {
                return response.data;
            });
        },
        getAllPlayers: function(year) {
            return $http.get('scrape/json_files/player_logs/'+year+'/all_players.json').then(function (response) {
                return response.data;
            });
        },
        getTeamSchedule: function(year, team) {
            return $http.get('scrape/json_files/team_schedules/'+year+'/'+team+'.json').then(function (response) {
                var data = response.data;
                var newKey;
                // because python's time module is not as convenient as moment
                // format date to yyyy-mm-dd
                _.forEach(data.by_date, function(value, key) {
                    newkey = moment(new Date(key)).format('YYYY-MM-DD');
                    data.by_date[newkey] = data.by_date[key];
                    delete data.by_date[key];
                });
                return data;
            });
        },
        getLeagueSchedule: function(year) {
            return $http.get('scrape/json_files/team_schedules/'+year+'/league_schedule.json').then(function (response) {
                var data = response.data;
                var newKey;
                // because python's time module is not as convenient as moment
                // format date to yyyy-mm-dd
                _.forEach(data, function(value, key) {
                    newkey = moment(new Date(key)).format('YYYY-MM-DD');
                    data[newkey] = data[key];
                    delete data[key];
                });
                return data;
            });
        },
        getTeamNews: function(team) {
            return $http.get('scrape/misc/news/'+team+'.json').then(function (response){
                return response.data;
            })
        },
        getPlayerAdvancedStats: function(year, name) {
            return $http.get('scrape/json_files/player_stats/'+year+'/'+name+'.json').then(function (response){
                return response.data;
            })
        },
        getTeamAdvancedStats: function(team) {
            return $http.get('scrape/misc/team_stats/'+team+'.json').then(function (response){
                return response.data;
            })
        },
        getDepthChartByTeam: function(team) {
            return $http.get('scrape/misc/depth_chart/'+team+'.json').then(function (response){
                return response.data;
            })
        },
        getDefenseVsPositionStats: function(team) {
            return $http.get('scrape/misc/fantasy_stats/'+team+'.json').then(function (response){
                return response.data;
            })
        },
        getTopLineupsByTeam: function(team, n) {
            return $http.get('scrape/misc/lineups/'+team+'-'+n+'.json').then(function (response){
                return response.data;
            })
        },
        getTeamZscores: function() {
            return $http.get('scrape/json_files/stats/league.json').then(function (response){
                return response.data;
            })
        },
        getTeamSynergyOffense: function() {
            return $http.get('scrape/json_files/synergy/team_offense_data.json').then(function (response){
                return response.data;
            })
        },
        getTeamSynergyDefense: function() {
            return $http.get('scrape/json_files/synergy/team_defense_data.json').then(function (response){
                return response.data;
            })
        },
        getPlayerSynergyOffense: function() {
            return $http.get('scrape/json_files/synergy/player_offense_data.json').then(function (response){
                return response.data;
            })
        },
        getPlayerSynergyDefense: function() {
            return $http.get('scrape/json_files/synergy/player_defense_data.json').then(function (response){
                return response.data;
            })
        }
    }
}]);