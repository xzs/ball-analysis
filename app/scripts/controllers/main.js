'use strict';

app.controller('MainCtrl',
    [
        'fetch',
        'processing',
        '$scope',
        '$q',
        function (
            fetch,
            processing,
            $scope,
            $q
        )
    {

    // Set salary
    var local = this;
    local.salary = 50000;
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
    $scope.lineups = {};
    $scope.today = moment().format("YYYY-MM-DD");

    function processDepthChart(team) {
        $scope.teamDepthChart[team] = {};

        // use $q to queue up the promises to manage the numerous calls to make sure its in order
        var promises = [];

        // function for getting the stats
        function getPlayerAdvancedStats(player, position, status) {
            fetch.getPlayerAdvancedStats($scope.year, player).then(function (data) {
                // grab the name of the current player since the player variable has moved on
                var currentPlayer = Object.keys(data)[0];
                // get the index for the current player
                var playerIndex = _.findIndex($scope.teamDepthChart[team][position], {'player': currentPlayer});
                // set it to an obj with the adv data
                if (playerIndex > -1){
                    $scope.teamDepthChart[team][position][playerIndex] = processPlayerAdvancedStats(data, currentPlayer);
                    $scope.teamDepthChart[team][position][playerIndex]['status'] = status;
                    // base stats needs to be defined as the directive will render after the first element
                    $scope.teamDepthChart[team][position][playerIndex]['base_stats'] = {};
                }
            }, function(err){
                // if player doesn't exist then create empty object
                var playerIndex = _.findIndex($scope.teamDepthChart[team][position], player);
                $scope.teamDepthChart[team][position][playerIndex] = {};
                $scope.teamDepthChart[team][position][playerIndex][player] = {};
            });
        };

        // function for getting the stats
        function getPlayerStats(player, position) {
            fetch.getPlayer($scope.year, player).then(function (data) {
                var tempPlayer = player;
                // get the index for the current player
                var playerIndex = _.findIndex($scope.teamDepthChart[team][position], {'name': tempPlayer});
                // set it to an obj with the adv data
                if (playerIndex > -1) {
                    $scope.teamDepthChart[team][position][playerIndex]['base_stats'] = data.stats;
                    //
                    $scope.teamDepthChart[team][position][playerIndex]['USGvsMIN'] =
                        (parseFloat($scope.teamDepthChart[team][position][playerIndex]['USG']) / parseFloat(data.stats.playtime)).toFixed(2);
                    $scope.teamDepthChart[team][position][playerIndex]['USGvsPER'] =
                        (parseFloat($scope.teamDepthChart[team][position][playerIndex]['USG']) / parseFloat($scope.teamDepthChart[team][position][playerIndex]['PER'])).toFixed(2);

                }
            }, function(err){
                // if player doesn't exist then create empty object
                var playerIndex = _.indexOf($scope.teamDepthChart[team][position], player);
                $scope.teamDepthChart[team][position][playerIndex] = {};
                $scope.teamDepthChart[team][position][playerIndex][player] = {};
            });
        };

        // get the depthChart first
        fetch.getDepthChartByTeam(team).then(function (data){
            $scope.teamDepthChart[team] = data;

            // get the advance stats for the player
            _.forEach(data, function(players, position) {
                for (var i=0; i<players.length; i++) {
                    var player = players[i].player;
                    var status = players[i].status;
                    promises.push(getPlayerAdvancedStats(player, position, status));
                    promises.push(getPlayerStats(player, position));
                }
            })

            $q.all(promises).then(function(response){
                console.log($scope.teamDepthChart);
            });
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

    function getDefenseVsPositionStats(team) {
        $scope.teamFantasyStats[team] = {};
        fetch.getDefenseVsPositionStats(team).then(function (data){
            $scope.teamFantasyStats[team] = data;
            _.forEach(data, function(stats, position){
                var lastFiveDiff = parseFloat(stats['Last 5']) - parseFloat(stats['Season']);
                $scope.teamFantasyStats[team][position]['lastFiveDiff'] = lastFiveDiff.toFixed(2);
            })
        });
    }
    $scope.getTeamStats = function(teams) {
        $scope.teamAdvancedStats = {};
        $scope.teamDepthChart = {};
        $scope.teamFantasyStats = {};
        // get advanced stats and depth chart for each team
        getTeamAdvancedStats(teams.opp);
        processDepthChart(teams.opp);

        getTeamAdvancedStats(teams.team);
        processDepthChart(teams.team);

        getDefenseVsPositionStats(teams.team);
        getDefenseVsPositionStats(teams.opp);
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
            // var isStarter = _.includes(Object.keys(local.starters), name);

            // Player info
            $scope.playerInfo = data.basic_info;
            // $scope.playerInfo.isStarter = isStarter;
            // $scope.playerInfo.status = local.starters[name] ? local.starters[name].status : '';
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
            fetch.getPlayerAdvancedStats(year, name).then(function (data) {
                $scope.playerAdvancedStats = processPlayerAdvancedStats(data, name)
            });

        }, function(error) {
            $scope.alerts.message = 'The player does not exist';
            $scope.alerts.type = 'danger';
        });


    }

    $scope.getCSV = function(csv){
        Papa.parse(csv, {
            complete: function(results) {
                // remove the first element from the list
                processCSV(_.drop(results.data));
            }
        });
    }

    function processCSV(data) {
        // process the data into readable JSON format
        console.log(processing.setAllPlayersByPosition(data));
        // $scope.lineups.equalDistributedLineup = processing.getEqualDistributionLineUp(local.salary);
        // console.log($scope.lineups.equalDistributedLineup);

        // force apply as the file reader API will work asynchronously, outside of the angularjs "flow".
        // Therefore, you have to make apply int he end of the onload function
        // http://stackoverflow.com/a/33038028
        $scope.$apply();

    };

    function processPlayerAdvancedStats(data, name) {
        var playerAdvancedStats = {};
        // TS%, PER, OWS, DWS, OBM, DBM, USG%
        playerAdvancedStats = {
            'name': name,
            'OWS': data[name]['OWS'],
            'DWS': data[name]['DWS'],
            'OBPM': data[name]['OBPM'],
            'DBPM': data[name]['DBPM'],
            'TS': data[name]['TS%'],
            'PER': data[name]['PER'],
            'USG': data[name]['USG%']
        };

        return playerAdvancedStats;
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
    getLeagueSchedule($scope.year);

}]);
