app.factory('processing', ['common', 'fetch', '$q', function(common, fetch, $q) {
    var finalData = {};
    var positions = ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'All'];

    // 
    finalData.maxUsage = {
        player: undefined,
        usage: undefined
    };

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

    finalData.getAllCurrentPlayers = function(teams) {
        var promises = [];
        for (var i=0; i<teams.length; i++) {
            fetch.getDepthChartByTeam(teams[i]).then(function (data){
                _.forEach(data, function(players, position) {
                    for (var i=0; i<players.length; i++) {
                        var player = players[i].player;
                        var status = players[i].status;
                        getPlayerAdvancedStats(player, position, status)
                    }
                })
            });
        }

        return finalData;
    }

    function getPlayerAdvancedStats(player, position, status) {
        // I need to just store the max usage for each player
        fetch.getPlayerAdvancedStats('2016', player).then(function (data) {
            // grab the name of the current player since the player variable has moved on
            var currentPlayer = Object.keys(data)[0];
            getMaxUsage(data, player);
        });
    };

    function getMaxUsage(data, player) {
        if (!(finalData.maxUsage.usage > parseInt(data[player]['USG%']))) {
            finalData.maxUsage.player = player;
            finalData.maxUsage.usage = parseInt(data[player]['USG%']);
        }
        return finalData.maxUsage;
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

    return finalData
}]);