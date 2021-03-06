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
    local.allPlayers = {};
    local.dkPlayers = {};
    $scope.year = 2016;
    $scope.teamnews = {};
    $scope.alerts = {
        message: null,
        type: null
    };
    $scope.lineups = {};
    $scope.today = moment("2016-03-25").format("YYYY-MM-DD");
    // $scope.csvComplete = false;

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
                    var teamDepthChart = $scope.teamDepthChart[team][position][playerIndex];
                    teamDepthChart['status'] = status;
                    // base stats needs to be defined as the directive will render after the first element
                    teamDepthChart['base_stats'] = {};

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

                // get the dk stats for that player
                var dkStats = local.dkPlayers['team'] ? local.dkPlayers['team'][team][tempPlayer] : {};
                // get the index for the current player
                var playerIndex = _.findIndex($scope.teamDepthChart[team][position], {'name': tempPlayer});
                // set it to an obj with the adv data
                if (playerIndex > -1) {
                    var teamDepthChart = $scope.teamDepthChart[team][position][playerIndex];
                    teamDepthChart['base_stats'] = data;
                    teamDepthChart['team'] = (team == local.teamOne) ? local.teamOne : local.teamTwo;
                    teamDepthChart['opponent'] = (team == local.teamOne) ? local.teamTwo : local.teamOne;

                    // if they played this season
                    teamDepthChart['teams_against_season'] =
                        data.teams_against[teamDepthChart['opponent']] ?
                            data.teams_against[teamDepthChart['opponent']].stats :
                            null;
                    if (teamDepthChart['teams_against_season']) {
                        teamDepthChart['teams_against_season']['dk_points'] =
                                processing.calcDkPoints(teamDepthChart['teams_against_season']);
                    }
                    // if they played last season
                    fetch.getPlayer($scope.year-1, tempPlayer).then(function (data) {
                        teamDepthChart['teams_against_last_season'] =
                            data.teams_against[teamDepthChart['opponent']] ?
                                data.teams_against[teamDepthChart['opponent']].stats :
                                null;
                        if (teamDepthChart['teams_against_last_season']) {
                            teamDepthChart['teams_against_last_season']['dk_points'] =
                                processing.calcDkPoints(teamDepthChart['teams_against_last_season']);
                        }
                    })

                    // add the dk stats for that player
                    teamDepthChart['dk_stats'] = dkStats;
                    teamDepthChart['dk_stats']['VAL'] =
                        ((parseFloat(dkStats.appg) / parseFloat(dkStats.salary)) * 1000).toFixed(2);
                    teamDepthChart['USGvsMIN'] =
                        (parseFloat(teamDepthChart['USG']) / parseFloat(data.stats.playtime)).toFixed(2);
                    teamDepthChart['USGvsPER'] =
                        (parseFloat(teamDepthChart['USG']) / parseFloat(teamDepthChart['PER'])).toFixed(2);

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


    function getTeamAdvancedStats(team) {
        var validList = ['ORtg', 'DRtg', 'Pace', 'MOV', 'FGA', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS'];
        // ORtg DRtg Pace MOV FGA TRB AST STL BLK PTS
        // This needs to be removed with because we already do this call in the processing.js factory
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
        $scope.teamLineups = {};

        // we can pass in both teams then store them in $scope variables
        local.teamOne = teams.opp;
        local.teamTwo = teams.team;

        // get advanced stats and depth chart for each team
        processDepthChart(teams.opp);
        processDepthChart(teams.team);

        $scope.teamAdvancedStats[teams.team] = $scope.dfsStats.teamAdvancedStats[teams.team];
        $scope.teamAdvancedStats[teams.opp] = $scope.dfsStats.teamAdvancedStats[teams.opp];

        getDefenseVsPositionStats(teams.team);
        getDefenseVsPositionStats(teams.opp);

        $scope.teamLineups[teams.team] = $scope.dfsStats.teamLineups[teams.team]
        $scope.teamLineups[teams.opp] = $scope.dfsStats.teamLineups[teams.opp]

        getTeamNews(teams.team);
        getTeamNews(teams.opp);
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

    $scope.getGameStats = function(teams) {
        $scope.teamLineups = {};
        $scope.teamAdvancedStats = {};

        $scope.teamLineups[teams.team] = $scope.dfsStats.teamLineups[teams.team]
        $scope.teamLineups[teams.opp] = $scope.dfsStats.teamLineups[teams.opp]

        $scope.teamAdvancedStats[teams.team] = $scope.dfsStats.teamAdvancedStats[teams.team];
        $scope.teamAdvancedStats[teams.opp] = $scope.dfsStats.teamAdvancedStats[teams.opp];
    }

    $scope.getPlayers = function(team) {
        $scope.teamPlayers = local.allPlayers[team];
        getTeamSchedule($scope.year, $scope.team);

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

    function processPlayerAdvancedStats(data, name) {
        var playerAdvancedStats = {};
        // TS%, PER, OWS, DWS, OBM, DBM, USG%
        playerAdvancedStats = {
            'name': name,
            'OWS': data[name]['OWS'],
            'DWS': data[name]['DWS'],
            'OBPM': data[name]['OBPM'],
            'DBPM': data[name]['DBPM'],
            'FTr': data[name]['FTr'],
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

    // get seasons schedule
    function getLeagueSchedule(year, csvData) {
        fetch.getLeagueSchedule(year).then(function (data) {
            $scope.todaySchedule = data[$scope.today] ? data[$scope.today] : false;

            $scope.todaySchedule = _.remove($scope.todaySchedule, function(game) {
                return ( game.time == "10:00p EST" || game.time == "10:30p EST");
            });

            $scope.allTeams = [];
            _.forEach($scope.todaySchedule, function(game, key) {

                $scope.allTeams.push(game.team);
                $scope.allTeams.push(game.opp);
            })
            $scope.getAllStats($scope.allTeams, $scope.todaySchedule, csvData)
        });


    }

    $scope.getAllStats = function(teams, games) {
        $scope.dfsStats = processing.getAllCurrentPlayers(teams, games);
    }

    $scope.getCombinations = function(type) {
        var tempList = [];
        var playersLength = $scope.dfsStats.players.length;
        var position, player;

        if (type == 'modified') {
            for (var i=0; i<playersLength; i++) {
                player = $scope.dfsStats.players[i];
                position = player.basic_info.position;
                if (player.last_3_games.playtime > 10 && player.status == 'Available' && player.opportunityScore > 0.5 &&
                    !(
                        player.lastGameBetterThanAverage.last_1_games == 'down'
                        && player.lastGameBetterThanAverage.last_3_games == 'down'
                        && player.minuteIncrease.last_1_games == 'down'
                        && player.minuteIncrease.last_3_games == 'down'
                    )
                ) {
                    tempList.push($scope.dfsStats.players[i]);
                }
            }
        } else if (type == 'fourFive') {
            for (var i=0; i<playersLength; i++) {
                player = $scope.dfsStats.players[i];
                if (player.salary <= 4500) {
                    tempList.push($scope.dfsStats.players[i]);
                }
            }
        }

        $scope.dfsStats.players = tempList;

    }

    $scope.$watch('file.csv', function(csv) {
        if (csv) {
            Papa.parse(csv, {
                complete: function(results) {
                    var finalResults = _.dropRight(_.drop(results.data));
                    processing.processCSV(finalResults);
                    getLeagueSchedule($scope.year, finalResults)
                    $scope.$apply();
                    $scope.csvComplete = true;
                }
            });
        }

    });

}]);
