app.factory('processing', ['common', 'fetch', '$q', function(common, fetch, $q) {
    var finalData = {};
    var positions = ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'All'];

    finalData.players = [];
    finalData.permArr = [];
    finalData.usedChars = [];
    finalData.dvpRank = {
        positions: {},
        categories: {}
    };
    finalData.activeTeams = {};

    var calcPlayerCostToPoints = function(player) {
        // round to 4 decimals while maintaining as an integer
        return +((player.appg / player.salary * 100).toFixed(4))
    }

    // find last smallest value in a list of objects
    var findMinInList = function(data, value) {
        var result = false;
        _.some(data, function (player) {
            if (player.appgCostRatio < value) {
                result = player;
            }
        });
        return result;
    }

    finalData.setAllPlayersByTeam = function(data) {

        finalData['team'] = {};
        var dataLength = data.length;

        for (var i=0; i<dataLength; i++) {
            var dataItem = data[i];
            // get the team name
            var team = common.translateDkDict()[dataItem[5]];
            var player = {
                name: dataItem[1],
                salary: dataItem[2],
                appg: dataItem[4]
            }
            if (!finalData['team'][team]) {
                finalData['team'][team] = {};

                finalData['team'][team][player.name] = player;
            } else {
                finalData['team'][team][player.name] = player;
            }
        }
        return finalData;
    }

    // this is more so the constructor
    finalData.setAllPlayersByPosition = function(data) {
        var dataLength = data.length;
        // sub categories
        finalData['G'] = [];
        finalData['F'] = [];
        finalData['All'] = [];
        // parse the string and match the team
        for (var i=0; i<dataLength; i++) {
            var dataItem = data[i];
            var playerPosition = dataItem[0];
            // "Atl@NO 08:00PM ET"
            // If the team starts with the player's team then its home else away
            var gameInfo = _.words(dataItem[3]);
            var locGame = gameInfo[0] == dataItem[5] ? 'Home' : 'Away';
            var gametime = gameInfo[2] + ':' + gameInfo[3] + gameInfo[4] + gameInfo[5];
            var player = {
                pos: playerPosition,
                name: dataItem[1],
                salary: dataItem[2],
                location: locGame,
                gametime: gametime,
                appg: dataItem[4],
                team: dataItem[5],
            };

            player.appgCostRatio = calcPlayerCostToPoints(player);

            // categorize them by position
            if (!finalData[playerPosition]) {
                finalData[playerPosition] = [];
                // If G
                if (playerPosition == 'PG' || playerPosition == 'SG') {
                    finalData['G'].push(player);
                }
                // If F
                if (playerPosition == 'SF' || playerPosition == 'PF') {
                    finalData['F'].push(player);
                }
                finalData[playerPosition].push(player);
            } else {
                // If G
                if (playerPosition == 'PG' || playerPosition == 'SG') {
                    finalData['G'].push(player);
                }
                // If F
                if (playerPosition == 'SF' || playerPosition == 'PF') {
                    finalData['F'].push(player);
                }
                finalData[playerPosition].push(player);
            }

            // Push to all
            finalData['All'].push(player);
        }
        return finalData;
    }

    finalData.getPlayersByPosition = function(position) {
        if (finalData[position]) {
            return finalData[position];
        } else {
            return null;
        }
    }

    // Get the most cost effective players, @position, @numberresults
    finalData.getCostEffectivePlayersByPosition = function(position, num) {
        var positionLength = finalData[position].length;
        // create list
        var resultsList = [];
        for (var i=0; i<positionLength; i++) {
            var player = finalData[position][i];
            if (resultsList.length < num) {
                resultsList.push(player);
            } else {
                var appgCostRatio = player.appgCostRatio;
                // if the player's ratio is higher than that in the list
                var findMin = findMinInList(resultsList, appgCostRatio);
                if (findMin) {
                    // remove last element
                    resultsList = _.reject(resultsList, findMin);
                    resultsList.push(player);
                }
            }
        }
        return resultsList;
    }

    finalData.getExpensivePlayersByPosition = function(position, num) {
        return _.take(finalData[position], num);
    }

    finalData.getEqualDistributionLineUp = function(salary) {
        // divide by the 8 positions
        var posSalary = salary / 8;
        var lineup = {};
        var blacklist = [];
        var positionLength = positions.length;
        for (var i=0; i<positionLength; i++) {
            var playerList = finalData[positions[i]];
            var playersLength = playerList.length;
            // set min to first player salary
            var min = Math.abs(posSalary - playerList[0].salary);
            lineup[positions[i]] = {};
            // find minimum difference in the dataset
            for (var j=0; j<playersLength; j++) {
                var player = playerList[j];
                // Because of equal distribution we only account for those players less or equal
                if (posSalary >= player.salary) {
                    var diff = posSalary - player.salary
                    // if the player isn't on the blacklist
                    if (min >= diff && !(_.includes(blacklist, player))) {
                        min = diff;
                        // add the player
                        lineup[positions[i]] = player;
                        // add player to blacklist
                        blacklist.push(player);
                    }
                }
            }
        }
        return lineup;
    }

    finalData.calcDkPoints = function(stats) {
        /*
            Point = +1 PT
            Made 3pt. shot = +0.5 PTs
            Rebound = +1.25 PTs
            Assist = +1.5 PTs
            Steal = +2 PTs
            Block = +2 PTs
            Turnover = -0.5 PTs
            Double-Double = +1.5PTs (MAX 1 PER PLAYER: Points, Rebounds, Assists, Blocks, Steals)
            Triple-Double = +3PTs (MAX 1 PER PLAYER: Points, Rebounds, Assists, Blocks, Steals)
        */

        // for now excluding double/triple doubles
        var dkPoints = 0;
        var dkScoring = {
            points: 1,
            threes: 0.5,
            rebounds: 1.25,
            assists: 1.25,
            steals: 2,
            blocks: 2,
            turnovers: -0.5
        };

        _.forEach(stats, function(value, key) {
            if (dkScoring[key]) {
                dkPoints += (value * dkScoring[key]);
            }
        });

        return dkPoints.toFixed(2);
    }

    finalData.getMaxVAL = function(data) {

        finalData['maxVAL'] = {};
        var dataLength = data.length;
        for (var i=0; i<dataLength; i++) {
            var dataItem = data[i];
            // get the team name

            var team = common.translateDkDict()[dataItem[5]];
            var player = {
                name: dataItem[1],
                salary: dataItem[2],
                appg: dataItem[4]
            }
            finalData['maxVAL'][dataItem[1]] = player;
        }
        return finalData.maxVAL;
    }

    finalData.getAllCurrentPlayers = function(teams, games) {
        // get league average
        finalData.players = [];
        getLeagueAverageDefenseVsPositionStats();
        var opponents = {};
        for (var i=0; i<teams.length; i++) {
            getDefenseVsPositionStats(team);
            var team = teams[i];
            // get opponents
            if (!opponents[team]) {
                opponents[team] = {};
                _.forEach(games, function(game) {
                    if (game.opp == team && game.team != team) {
                        opponents[team].opponent = game.team;
                        if (game.location == 'Away'){
                            opponents[team].location = 'vs';
                        } else {
                            opponents[team].location = '@';
                        }
                    } else if (game.opp != team && game.team == team) {
                        opponents[team].opponent = game.opp;
                        if (game.location == 'Away'){
                            opponents[team].location = '@';
                        } else {
                            opponents[team].location = 'vs';
                        }
                    }
                });
            }
            finalData.activeTeams[team] = {};
            getTeamDepthChart(team, opponents);
        }

        console.log(finalData);
        return finalData;
    }

    function getTeamDepthChart(team, opponents){
        fetch.getDepthChartByTeam(team).then(function (data){
            finalData.activeTeams[team] = data;
            _.forEach(data, function(players, position) {
                for (var i=0; i<players.length; i++) {
                    var player = players[i].player;
                    var status = players[i].status;
                    var rank = i;
                    getPlayerStats(player, position, opponents, status, rank);
                }
            })
        });
    }

    function getLeagueAverageDefenseVsPositionStats() {
        fetch.getDefenseVsPositionStats('league').then(function (data){
            finalData['leagueAverageDvP'] = data;
        });
    }

    function getPlayerStats(player, position, opponent, status, rank) {
        var playerObj;
        fetch.getPlayerAdvancedStats('2016', player).then(function (advData) {
            // grab the name of the current player since the player variable has moved on
            fetch.getPlayer('2016', player).then(function (data) {
                playerObj = data;
                playerObj.status = status;
                playerObj.rank = rank;

                playerObj.dvp = {};
                playerObj.opponent = opponent[data.basic_info.team];
                playerObj.stats.fouls = parseFloat(playerObj.stats.fouls / playerObj.stats.playtime * 36).toFixed(2);

                // get opponent stats
                fetch.getDepthChartByTeam(playerObj.opponent.opponent).then(function (data){
                    if (data[playerPosition][playerObj.rank]){
                        var oppData = _.find(finalData.players,
                            {
                                'basic_info': {
                                    'name': data[playerPosition][playerObj.rank].player
                                }
                            }
                        );
                        playerObj.matchup = {
                            player: data[playerPosition][playerObj.rank].player,
                            data: oppData
                        }
                    }
                });

                playerObj.bpm = {
                    dbpm: parseFloat(advData[player]['DBPM']),
                    obpm: parseFloat(advData[player]['OBPM']),
                    net: parseFloat(parseFloat(advData[player]['OBPM']) + parseFloat(advData[player]['DBPM'])).toFixed(2)
                }
                playerObj.fppPerMinute = parseFloat(data.stats.dk_points / data.stats.playtime).toFixed(2);
                playerObj.fppPerMinute3 = parseFloat(data.last_3_games.dk_points / data.last_3_games.playtime).toFixed(2);
                playerObj.lastGameBetterThanAverage = lastGameVsAverage(data);

                playerObj.minuteIncrease = minuteIncrease(data);
                playerObj.usageIncrease = usageIncrease(data);
                playerObj.bestAt = getPlayerBestAt(data, player, opponent);
                playerObj.opportunityScore = parseFloat(playerObj.last_3_games.playtime / playerObj.stats.playtime * playerObj.fppPerMinute3).toFixed(2);
                playerObj.usage = parseInt(advData[player]['USG%']);

                if (finalData.maxVAL[player]) {
                    playerObj.val = parseFloat(data.last_3_games.dk_points / parseFloat(finalData.maxVAL[player].salary) * 1000).toFixed(2);
                    playerObj.salary = finalData.maxVAL[player].salary;
                }

                fetch.getTeamNews(data.basic_info.team).then(function (data) {
                    playerObj.news = _.find(data, { 'player': player});
                });

                var playerPosition = data.basic_info.position;
                fetch.getDefenseVsPositionStats(opponent[data.basic_info.team].opponent).then(function (data){
                    playerObj.dvp.last_5 = data[playerPosition]['Last 5'];
                    playerObj.dvp.last_5_ratio = parseFloat(data[playerPosition]['Last 5']/ finalData.leagueAverageDvP['position'][playerPosition].average).toFixed(2);
                    playerObj.dvp.season = data[playerPosition]['Season'];
                    playerObj.dvp.season_ratio = parseFloat(data[playerPosition]['Season']/ finalData.leagueAverageDvP['position'][playerPosition].average).toFixed(2);

                    playerObj.tempWeightedNet;
                    if (playerObj.opportunityScore && playerObj.val && playerObj.salary) {
                        playerObj.tempWeightedNet = parseFloat(0.35*playerObj.opportunityScore + 0.1*playerObj.dvp.last_5 + 0.1*playerObj.last_3_games.playtime
                            + 0.2*playerObj.val + 0.1*playerObj.stats.dk_points + 0.15*playerObj.usage);

                        if (playerObj.lastGameBetterThanAverage.last_1_games == 'up') {
                            playerObj.tempWeightedNet += 0.5;
                        } else if (playerObj.lastGameBetterThanAverage.last_1_games == 'down') {
                            playerObj.tempWeightedNet -= 0.5;
                        }

                        if (playerObj.lastGameBetterThanAverage.last_3_games == 'up') {
                            playerObj.tempWeightedNet += 0.5;
                        } else if (playerObj.lastGameBetterThanAverage.last_3_games == 'down') {
                            playerObj.tempWeightedNet -= 0.5;
                        }

                        if (playerObj.minuteIncrease.last_1_games == 'up') {
                            playerObj.tempWeightedNet += 0.5;
                        } else if (playerObj.minuteIncrease.last_1_games == 'down') {
                            playerObj.tempWeightedNet -= 0.5;
                        }

                        if (playerObj.minuteIncrease.last_3_games == 'up') {
                            playerObj.tempWeightedNet += 0.5;
                        } else if (playerObj.minuteIncrease.last_3_games == 'down') {
                            playerObj.tempWeightedNet -= 0.5;
                        }
                        playerObj.tempWeightedNet = playerObj.tempWeightedNet.toFixed(2);
                    } else {
                        playerObj.tempWeightedNet = 0;
                    }

                });

                console.log(playerObj.dvp.last_5);

                finalData.players.push(playerObj);

            });
        });
    };

    function getDefenseVsPositionByTeam(player, team, playerPosition) {
        fetch.getDefenseVsPositionStats(team).then(function (data){
            player.last_5 = data[playerPosition]['Last 5'];
            player.last_5_ratio = parseFloat(data[playerPosition]['Last 5']/ finalData.leagueAverageDvP['position'][playerPosition].average).toFixed(2);
            player.season = data[playerPosition]['Season'];
            player.season_ratio = parseFloat(data[playerPosition]['Season']/ finalData.leagueAverageDvP['position'][playerPosition].average).toFixed(2);
            return player;
        });
    };

    function getMaxUsage(advData, data, player) {
        if (parseInt(advData[player]['USG%']) > 20 && parseInt(data.stats.playtime) > 20) {
            finalData.maxUsage.push({
                player : player,
                usage : parseInt(advData[player]['USG%'])
            })
        }
        return finalData.maxUsage;
    };

    function lastGameVsAverage(data) {
        var tempObj = {};
        if ((data.last_1_games.dk_points - data.stats.dk_points) > 5) {
            tempObj.last_1_games = 'up';
        } else if ((data.stats.dk_points - data.last_1_games.dk_points) > 5){
            tempObj.last_1_games = 'down';
        } else {
            tempObj.last_1_games = 'none';
        }

        if ((data.last_3_games.dk_points - data.stats.dk_points) > 5) {
            tempObj.last_3_games = 'up';
        } else if ((data.stats.dk_points - data.last_3_games.dk_points) > 5){
            tempObj.last_3_games = 'down';
        } else {
            tempObj.last_3_games = 'none';
        }

        return tempObj;
    };

    function minuteIncrease(data) {
        var tempObj = {};
        if ((data.last_1_games.playtime - data.stats.playtime) > 5) {
            tempObj.last_1_games = 'up';
        } else if ((data.stats.playtime - data.last_1_games.playtime > 5)){
            tempObj.last_1_games = 'down';
        } else {
            tempObj.last_1_games = 'none';
        }

        if ((data.last_3_games.playtime - data.stats.playtime) > 5) {
            tempObj.last_3_games = 'up';
        } else if ((data.stats.playtime - data.last_1_games.playtime > 5)){
            tempObj.last_3_games = 'down';
        } else {
            tempObj.last_3_games = 'none';
        }

        return tempObj;
    };

    function usageIncrease(data) {
        var tempObj = {};
        if ((data.last_1_games.usage - data.usage) > 3) {
            tempObj.last_1_games = 'up';
        } else if ((data.usage - data.last_1_games.usage > 3)){
            tempObj.last_1_games = 'down';
        }

        if ((data.last_3_games.usage - data.usage) > 3) {
            tempObj.last_3_games = 'up';
        } else if ((data.usage - data.last_1_games.usage > 3)){
            tempObj.last_3_games = 'down';
        }

        return tempObj;
    };


    function getPlayerConsistency(data, player) {
        if (parseFloat(data.stats.playtime) > 20) {
            finalData.playerCov.push({
                player : player,
                cov : parseFloat(data.cov).toFixed(2)
            })
        }
        return finalData.playerCov;
    };

    function getPlayerBestAt(data, player, opponent) {
        var tempObj = {};
        var away = data.average_away_gmsc;
        var home = data.average_home_gmsc;
        var diff = Math.abs(parseFloat(data.average_away_gmsc - data.average_home_gmsc));

        if ((away > home) && (diff > 1.75)) {
            tempObj.location = 'Away';
            tempObj.diff = diff.toFixed(2);
        } else if ((away < home) && (diff > 1.75)) {
            tempObj.location = 'Home';
            tempObj.diff = diff.toFixed(2);
        } else {
            tempObj.location = 'Neutral';
            if (opponent.location == '@') {
                tempObj.diff = parseFloat(data.average_away_gmsc - data.average_home_gmsc).toFixed(2)
            } else {
                tempObj.diff = parseFloat(data.average_home_gmsc - data.average_away_gmsc).toFixed(2)
            }
        }
        return tempObj;
    };

    function getDkPoints(data, player) {
        finalData.dkPoints.push({
            player : player,
            dk_points : {
                average: data.stats.dk_points,
                last_3 : data.last_3_games.dk_points
            }
        });
        return finalData.dkPoints;
    };

    function getDefenseVsPositionStats(team) {
        var validList = ['3PM', 'AST', 'BLK', 'FG%', 'PTS', 'REB', 'STL'];

        // set categories
        for (var i=0; i<validList.length; i++) {
            // determined the rank based on stat categories
            var category = validList[i];
            finalData.dvpRank['categories'][category] = {};
        }

        fetch.getDefenseVsPositionStats(team).then(function (data){
            _.forEach(data, function(stats, position){
                // determine the rank of tonight's matchups for each position
                if (finalData.dvpRank['positions'] && finalData.dvpRank['positions'][position]) {
                    if (finalData.dvpRank['positions'][position]['max']['rank'] > stats.rank) {
                        finalData.dvpRank['positions'][position]['max'] = stats;
                        calcMatchupStrengthByPosition(finalData.dvpRank['positions'][position]['max'], stats, position);
                    } else if (finalData.dvpRank['positions'][position]['min']['rank'] < stats.rank) {
                        finalData.dvpRank['positions'][position]['min'] = stats;
                        calcMatchupStrengthByPosition(finalData.dvpRank['positions'][position]['min'], stats, position);
                    }
                } else {
                    finalData.dvpRank['positions'][position] = {
                        max: stats,
                        min: stats,
                        average: finalData.leagueAverageDvP['position'][position].average.toFixed(2)
                    };
                    // set initial matchup strength
                    calcMatchupStrengthByPosition(finalData.dvpRank['positions'][position]['max'], stats, position);
                    calcMatchupStrengthByPosition(finalData.dvpRank['positions'][position]['min'], stats, position);
                }

                for (var i=0; i<validList.length; i++) {
                    // determined the rank based on stat categories
                    var category = validList[i];
                    var statObj = {
                        team: common.translateTeamNames()[stats['Team']],
                        stat: category,
                        num: stats[category],
                        position: stats['Vs. Pos'],
                        average: finalData.leagueAverageDvP['category'][position][category].toFixed(2)
                    };
                    // calc categories for each position
                    if (finalData.dvpRank['categories'][category] && finalData.dvpRank['categories'][category][position]) {
                        if (finalData.dvpRank['categories'][category][position]['max']['num'] < stats[category]) {
                            finalData.dvpRank['categories'][category][position]['max'] = statObj;
                            calcMatchupStrengthByCategory(finalData.dvpRank['categories'][category][position]['max'], statObj, position, category);
                        } else if (finalData.dvpRank['categories'][category][position]['min']['num'] > stats[category]) {
                            finalData.dvpRank['categories'][category][position]['min'] = statObj;
                            calcMatchupStrengthByCategory(finalData.dvpRank['categories'][category][position]['min'], statObj, position, category);
                        }
                    } else {
                        finalData.dvpRank['categories'][category][position] = {
                            max: statObj,
                            min: statObj
                        };

                        calcMatchupStrengthByCategory(finalData.dvpRank['categories'][category][position]['max'], statObj, position, category);
                        calcMatchupStrengthByCategory(finalData.dvpRank['categories'][category][position]['min'], statObj, position, category);
                    }

                }
            });
        });

    }

    function calcMatchupStrengthByPosition(dataObj, stats, position) {
        dataObj['matchup'] = parseFloat(stats.Season / finalData.leagueAverageDvP['position'][position].average).toFixed(2);
        dataObj['matchup5'] = parseFloat(stats['Last 5'] / finalData.leagueAverageDvP['position'][position].average).toFixed(2);
        dataObj['matchup10'] = parseFloat(stats['Last 10'] / finalData.leagueAverageDvP['position'][position].average).toFixed(2);
    }

    function calcMatchupStrengthByCategory(dataObj, stats, position, category) {
        dataObj['matchup'] = parseFloat(stats.num / finalData.leagueAverageDvP['category'][position][category]).toFixed(2);
    }

    return finalData
}]);