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
    local.dkPlayers = {};
    $scope.year = 2016;
    $scope.team = 'GSW';
    $scope.player = 'Stephen Curry';
    $scope.teamnews = {};
    $scope.alerts = {
        message: null,
        type: null
    };
    $scope.lineups = {};
    $scope.today = moment("2016-02-21").format("YYYY-MM-DD");
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
        console.log('here');
        fetch.getDefenseVsPositionStats(team).then(function (data){
            $scope.teamFantasyStats[team] = data;
            _.forEach(data, function(stats, position){
                var lastFiveDiff = parseFloat(stats['Last 5']) - parseFloat(stats['Season']);
                $scope.teamFantasyStats[team][position]['lastFiveDiff'] = lastFiveDiff.toFixed(2);
            })
        });
    }

    function getLineupsByTeam(team) {
        $scope.teamLineups[team] = {};
        fetch.getTopLineupsByTeam(team).then(function (data){
            $scope.teamLineups[team] = data;
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

        // maybe this should be in $q 
        // get advanced stats and depth chart for each team
        getTeamAdvancedStats(teams.opp);
        processDepthChart(teams.opp);

        getTeamAdvancedStats(teams.team);
        processDepthChart(teams.team);

        getDefenseVsPositionStats(teams.team);
        getDefenseVsPositionStats(teams.opp);

        getLineupsByTeam(teams.team);
        getLineupsByTeam(teams.opp);

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

    $scope.getLineUps = function(teams) {
        $scope.teamLineups = {};
        $scope.teamAdvancedStats = {};

        getLineupsByTeam(teams.team);
        getLineupsByTeam(teams.opp);
        getTeamAdvancedStats(teams.opp);
        getTeamAdvancedStats(teams.team);
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
                return (game.time == "7:00p EST" || game.time == "8:00p EST" || game.time == "9:00p EST");
            });

            $scope.allTeams = [];
            _.forEach($scope.todaySchedule, function(game, key) {

                $scope.allTeams.push(game.team);
                $scope.allTeams.push(game.opp);
            })
            $scope.getSummaryStats($scope.allTeams, $scope.todaySchedule, csvData)
        });


    }

    $scope.getSummaryStats = function(teams, games) {
        $scope.summaryUsage = processing.getAllCurrentPlayers(teams, games);
    }

    $scope.getCombinations = function(type) {
        var tempList = [];
        var playersLength = $scope.summaryUsage.players.length;
        var position, player;

        if (type == 'modified') {
            for (var i=0; i<playersLength; i++) {
                player = $scope.summaryUsage.players[i];
                position = player.basic_info.position;
                if (player.last_3_games.playtime > 10 && player.status == 'Available' && player.opportunityScore > 0.5 &&
                    !(
                        player.lastGameBetterThanAverage.last_1_games == 'down'
                        && player.lastGameBetterThanAverage.last_3_games == 'down'
                        && player.minuteIncrease.last_1_games == 'down'
                        && player.minuteIncrease.last_3_games == 'down'
                    )
                ) {
                    tempList.push($scope.summaryUsage.players[i]);
                }
            }
        } else if (type == 'fourFive') {
            for (var i=0; i<playersLength; i++) {
                player = $scope.summaryUsage.players[i];
                if (player.salary <= 4500) {
                    tempList.push($scope.summaryUsage.players[i]);
                }
            }
        }

        $scope.summaryUsage.players = tempList;

    }

    $scope.getCSV = function(csv){
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

    function processCSV(data) {
        // process the data into readable JSON format
        local.dkPlayers = processing.setAllPlayersByTeam(data);

        // force apply as the file reader API will work asynchronously, outside of the angularjs "flow".
        // Therefore, you have to make apply int he end of the onload function
        // http://stackoverflow.com/a/33038028

    };


    // function init(year) {
    //     fetch.getAllPlayers(year).then(function (data) {
    //         local.allPlayers = data;
    //         $scope.teams = Object.keys(data).sort();
    //         $scope.getPlayers($scope.team);
    //         $scope.getPlayerData(year, $scope.player);
    //     });
    // }

    // $scope.changeYear = function(year) {
    //     init(year);
    // }



    $scope.findBestPack = function(data) {
        console.log(data);
        var m= [[0]]; // maximum pack value found so far
        var b= [[0]]; // best combination found so far
        var opts= [0]; // item index for 0 of item 0
        var P= [1]; // item encoding for 0 of item 0
        var choose= 0;
        for (var j= 0; j<data.length; j++) {
            opts[j+1]= opts[j]+data[j].pieces; // item index for 0 of item j+1
            P[j+1]= P[j]*(1+data[j].pieces); // item encoding for 0 of item j+1
        }
        for (var j= 0; j<opts[data.length]; j++) {
            m[0][j+1]= b[0][j+1]= 0; // best values and combos for empty pack: nothing
        }
        for (var w=1; w<=50000; w++) {
            m[w]= [0];
            b[w]= [0];
            for (var j=0; j<data.length; j++) {
                var N= data[j].pieces; // how many of these can we have?
                var base= opts[j]; // what is the item index for 0 of these?
                for (var n= 1; n<=N; n++) {
                    var W= n*data[j].weight; // how much do these items weigh?
                    var s= w>=W ?1 :0; // can we carry this many?
                    var v= s*n*data[j].value; // how much are they worth?
                    var I= base+n; // what is the item number for this many?
                    var wN= w-s*W; // how much other stuff can we be carrying?
                    var C= n*P[j] + b[wN][base]; // encoded combination
                    m[w][I]= Math.max(m[w][I-1], v+m[wN][base]); // best value
                    choose= b[w][I]= m[w][I]>m[w][I-1] ?C :b[w][I-1];
                }
            }
        }
        var best= [];
        for (var j= data.length-1; j>=0; j--) {
            best[j]= Math.floor(choose/P[j]);
            choose-= best[j]*P[j];
        }
        var out='<table><tr><td><b>Count</b></td><td><b>Item</b></td><th>unit weight</th><th>unit value</th>';
        var wgt= 0;
        var val= 0;
        for (var i= 0; i<best.length; i++) {
            if (0==best[i]) continue;
            out+='</tr><tr><td>'+best[i]+'</td><td>'+data[i].name+'</td><td>'+data[i].weight+'</td><td>'+data[i].value+'</td>'
            wgt+= best[i]*data[i].weight;
            val+= best[i]*data[i].value;
        }
        out+= '</tr></table><br/>Total weight: '+wgt;
        out+= '<br/>Total value: '+val;
        document.body.innerHTML= out;
    }

}]);
