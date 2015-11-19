'use strict';

app.controller('MainCtrl',
    [
        'fetch',
        'processing',
        '$scope',
        function (
            fetch,
            processing,
            $scope
        )
    {

    // Set salary
    var local = this;
    local.allPlayers = {};
    $scope.years = ['2015', '2016'];
    $scope.year = '2016';
    $scope.team = 'GSW';
    $scope.player = 'Stephen Curry';
    $scope.teamnews = {};
    $scope.alerts = {
        message: null,
        type: null
    };
    $scope.today = moment().format("YYYY-MM-DD");

    function processDepthChart() {
        fetch.getStarters().then(function (data){
            local.starters = data;
        });
    }

    // do a fetch everytime we switch teams
    function getTeamSchedule(year, team) {
        fetch.getTeamSchedule(year, team).then(function (data) {
            $scope.todayGame = data.by_date[$scope.today] ? data.by_date[$scope.today] : false;
        });
    }

    // get seasons schedule
    function getLeagueSchedule(year) {
        fetch.getLeagueSchedule(year).then(function (data) {
            $scope.todaySchedule = data[$scope.today] ? data[$scope.today] : false;
        });
    }

    function getTeamAdvancedStats(team) {
        var validList = ['ORtg', 'DRtg', 'Pace', 'MOV', 'FGA', 'TRB', 'AST', 'STL', 'BLK', 'PTS'];
        // ORtg DRtg Pace MOV FGA TRB AST STL BLK PTS
        $scope.teamAdvancedStats[team] = {};
        $scope.teamAdvancedStats['header'] = [];
        fetch.getTeamAdvancedStats(team).then(function (data) {
            for (var i=0; i<validList.length; i++) {
                var stat = validList[i];
                $scope.teamAdvancedStats[team][stat] = data[stat];
            }
            $scope.teamAdvancedStats['header'] = validList;
        });
    }

    $scope.getTeamStats = function(teams) {
        $scope.teamAdvancedStats = {};
        getTeamAdvancedStats(teams.opp);
        getTeamAdvancedStats(teams.team);
    }

    function getTeamNews(team) {
        if (!$scope.teamnews[team]) {
            fetch.getTeamNews(team).then(function (data) {
                $scope.teamnews[team] = data;
            });
        } else {
            return $scope.teamnews[team];
        }

    }

    $scope.getPlayers = function(team) {
        $scope.teamPlayers = local.allPlayers[team];
        getTeamSchedule($scope.year, $scope.team);
        getTeamNews($scope.team);
        // getTeamAdvancedStats($scope.team);
        return $scope.teamPlayers
    }

    $scope.getPlayerData = function(year, name) {
        $scope.player = name;

        fetch.getPlayer(year, name).then(function (data) {
            $scope.alerts = isPlayerOnTeam(name);
            // temp use of object.keys until I determine the final structure of the json
            var isStarter = _.includes(Object.keys(local.starters), name);

            // Player info
            $scope.playerInfo = data.basic_info;
            $scope.playerInfo.isStarter = isStarter;
            $scope.playerInfo.status = local.starters[name] ? local.starters[name].status : '';
            // Base stats
            $scope.playerStats = data.stats;
            $scope.playerCov = data.cov;
            $scope.playerLast5 = data.last_5_games;

            $scope.playerStatsOther = {
                'playerStatsHome': {
                    'playtime': data.home_playtime,
                    'gmsc': data.average_home_gmsc
                },
                'playerStatsAway': {
                    'playtime': data.away_playtime,
                    'gmsc': data.average_away_gmsc
                },
                'playerPreAllStar': data.pre_all_star.stats,
                'playerPostAllStar': data.post_all_star.stats,
                'playerAgainstEast': {
                    'games': data.eastern_conf.games,
                    'gmsc': data.eastern_conf.gmsc
                },
                'playerAgainstWest': {
                    'games': data.western_conf.games,
                    'gmsc': data.western_conf.gmsc
                }
            };

            // Data for against opponents
            var playerTeamData = data.teams_against;
            $scope.teamDataHeader = Object.keys(playerTeamData);
            // add an array of your data objects to enable sorting
            // http://stackoverflow.com/a/27779633
            $scope.teamData = Object.keys(playerTeamData)
             .map(function (key) {
               return playerTeamData[key];
            });

            // get advanced stats for player
            getPlayerAdvancedStats(year, name);

        }, function(error) {
            $scope.alerts.message = 'The player does not exist';
            $scope.alerts.type = 'danger';
        });


    }

    function getPlayerAdvancedStats(year, name) {
        $scope.playerAdvancedStats = {};
        fetch.getPlayerAdvancedStats(year, name).then(function (data) {
            // TS%, PER, OWS, DWS, OBM, DBM, USG%
            $scope.playerAdvancedStats = {
                'OWS': data[name]['OWS'],
                'DWS': data[name]['DWS'],
                'OBPM': data[name]['OBPM'],
                'DBPM': data[name]['DBPM'],
                'TS': data[name]['TS%'],
                'PER': data[name]['PER'],
                'USG': data[name]['USG%']
            };
        });
    }

    function isPlayerOnTeam(name) {
        var alertObj = {};
        // Check if player exists on team
        if (!_.find($scope.teamPlayers, {'name': name})) {
            alertObj.message = 'The player did not play on this team for the season/team selected';
            alertObj.type = 'warning';
        } else {
            alertObj.message = null;
            alertObj.type = null;
        }
        return alertObj;
    }

    function init(year) {
        fetch.getAllPlayers(year).then(function (data) {
            local.allPlayers = data;
            $scope.teams = Object.keys(data).sort();
            $scope.getPlayers($scope.team);
            $scope.getPlayerData(year, $scope.player);
        });
    }

    $scope.changeYear = function(year) {
        init(year);
    }

    init($scope.year);
    processDepthChart();
    getLeagueSchedule($scope.year);

}]);
