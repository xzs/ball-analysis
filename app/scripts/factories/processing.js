app.factory('processing', ['common', 'fetch', '$q', function(common, fetch, $q) {
    var finalData = {};
    var positions = ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'All'];

    finalData.players = [];
    finalData.tempPlayers = [];
    finalData.permArr = [];
    finalData.usedChars = [];
    finalData.AMB_PLAYERS = {
        'Patty Mills': 'Patrick Mills',
        'Moe Harkless': 'Maurice Harkless',
        'Wes Johnson': 'Wesley Johnson',
        'Amare Stoudemire': "Amar'e Stoudemire"
    };
    finalData.dvpRank = {
        positions: {},
        categories: {}
    };
    // by team
    finalData.dvpStats = {};
    finalData.news = {};
    finalData.activeTeams = {};
    finalData.teamAdvancedStats = {};
    finalData.teamLineups = {};

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

    finalData.processCSV = function(data) {

        finalData['dkPlayers'] = {};
        var dataLength = data.length;
        for (var i=0; i<dataLength; i++) {
            var dataItem = data[i];
            // get the team name

            var team = common.translateDkDict()[dataItem[5]];
            var player = {
                name: dataItem[1],
                position: dataItem[0],
                salary: dataItem[2],
                appg: dataItem[4]
            }
            finalData['dkPlayers'][dataItem[1]] = player;
        }
        return finalData.dkPlayers;
    }

    finalData.getAllCurrentPlayers = function(teams, games) {
        // get league average
        finalData.players = [];
        // get the stats for the league
        getDefenseVsPositionStats('league');
        finalData.getTeamAdvancedStats('league');

        var opponents = {};
        for (var i=0; i<teams.length; i++) {
            var team = teams[i];

            // get all team related stats
            getDefenseVsPositionStats(team);
            getTeamNews(team);

            finalData.getTeamAdvancedStats(team);
            finalData.teamLineups[team] = {};
            finalData.getLineupsByTeam(team, 1);
            finalData.getLineupsByTeam(team, 3);

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
            getTeamDepthChart(team, opponents[team]);
        }

        console.log(finalData);
        return finalData;
    }

    function getTeamDepthChart(team, opponent){
        fetch.getDepthChartByTeam(team).then(function (data){
            finalData.activeTeams[team] = data;
            _.forEach(data, function(players, position) {
                for (var i=0; i<players.length; i++) {
                    var player = players[i].player;
                    var status = players[i].status;
                    var rank = i;
                    if (finalData.AMB_PLAYERS[player]) {
                        player = finalData.AMB_PLAYERS[player];
                    }
                    getPlayerStats(player, position, opponent, status, rank);
                }
            })
        });
    }

    finalData.getTeamAdvancedStats = function(team) {
        var validList = ['ORtg', 'DRtg', 'Pace', 'MOV', 'FGA', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS'];
        // ORtg DRtg Pace MOV FGA TRB AST STL BLK PTS
        finalData.teamAdvancedStats[team] = {};
        finalData.teamAdvancedStats['header'] = [];
        fetch.getTeamAdvancedStats(team).then(function (data) {
            for (var i=0; i<validList.length; i++) {
                var stat = validList[i];
                finalData.teamAdvancedStats[team][stat] = data[stat];
            }
            finalData.teamAdvancedStats['header'] = validList;
        });
    }

    finalData.getLineupsByTeam = function(team, n) {
        finalData.teamLineups[team][n] = {};
        fetch.getTopLineupsByTeam(team, n).then(function (data){
            finalData.teamLineups[team][n] = data;
        });
    }

    function getDefenseVsPositionStats(team) {
        fetch.getDefenseVsPositionStats(team).then(function (data){
            finalData.dvpStats[team] = data;
            // rank the stats
            if (team != 'league') {
                getDefenseVsPositionStatsRank(team, data);
            }
        });
    }

    function getTeamNews(team) {
        fetch.getTeamNews(team).then(function (data) {
            finalData.news[team] = data;
        });
    }

    function getPlayerStats(player, position, opponent, status, rank) {
        var playerObj;
        // we need to get the advanced stats to determine the opportunities (such as the possiblility with rebounds as well as the pace adjusted stats)

        // if the player is even in the csv
        if (finalData.dkPlayers[player]) {
            fetch.getPlayerAdvancedStats('2016', player).then(function (advData) {
                // grab the name of the current player since the player variable has moved on
                fetch.getPlayer('2016', player).then(function (data) {
                    playerObj = data;
                    playerObj.status = status;
                    playerObj.rank = rank;
                    // use DK position
                    playerObj.basic_info.position = finalData.dkPlayers[player].position;

                    playerObj.dvp = {};
                    playerObj.opponent = opponent;
                    playerObj.stats.fouls = parseFloat(playerObj.stats.fouls / playerObj.stats.playtime * 36).toFixed(2);

                    var playerPosition = playerObj.basic_info.position;
                    var playerOpponent = playerObj.opponent['opponent'];
                    // this needs to be refactored outside
                    if (playerOpponent) {
                        var opponentData = finalData.activeTeams[playerOpponent];
                        // Get the opponent data
                        if (opponentData && opponentData[playerPosition][playerObj.rank]) {
                            var oppData = _.find(finalData.players,
                                {
                                    'basic_info': {
                                        'name': opponentData[playerPosition][playerObj.rank].player
                                    }
                                }
                            );
                            playerObj.matchup = {
                                player: opponentData[playerPosition][playerObj.rank].player,
                                data: oppData
                            }
                        }
                    }

                    playerObj.bpm = {
                        dbpm: parseFloat(advData[player]['DBPM']),
                        obpm: parseFloat(advData[player]['OBPM']),
                        net: parseFloat(parseFloat(advData[player]['OBPM']) + parseFloat(advData[player]['DBPM'])).toFixed(2)
                    }
                    playerObj.ftr = parseFloat(advData[player]['FTr']);
                    playerObj.trb = parseFloat(advData[player]['TRB%']);
                    playerObj.usage = parseInt(advData[player]['USG%']);

                    playerObj.ftrVsOppFoul = ftrVsOppFoul(playerObj.ftr, finalData.teamAdvancedStats[playerOpponent]['PF'])
                    playerObj.trbVsOppFGA = trbVsOppFGA(playerObj.trb, finalData.teamAdvancedStats[playerOpponent]['FGA'])

                    playerObj.fppPerMinute = parseFloat(data.stats.dk_points / data.stats.playtime).toFixed(2);
                    playerObj.fppPerMinute3 = parseFloat(data.last_3_games.dk_points / data.last_3_games.playtime).toFixed(2);

                    playerObj.rebPerMinute = parseFloat(data.stats.rebounds / data.stats.playtime).toFixed(2);
                    playerObj.rebPerMinute3 = parseFloat(data.last_3_games.rebounds / data.last_3_games.playtime).toFixed(2);

                    playerObj.opace = data.fantasy_best.pace;
                    playerObj.omargin = data.fantasy_best.margin;
                    playerObj.oresults = data.fantasy_best.results;
                    playerObj.oplaytime = data.fantasy_best.avg_playtime;

                    playerObj.lastGameBetterThanAverage = lastGameVsAverage(data);
                    playerObj.minuteIncrease = minuteIncrease(data);
                    playerObj.usageIncrease = usageIncrease(data);
                    playerObj.bestAt = getPlayerBestAt(data, player, opponent);
                    playerObj.opportunityScore = parseFloat(playerObj.last_3_games.playtime / playerObj.stats.playtime * playerObj.fppPerMinute3).toFixed(2);


                    // regression stats
                    playerObj.regression = data.regression;

                        playerObj.regressionAlert = '';

                        if (data.regression.opp_team_data.OppPF
                            && finalData.teamAdvancedStats[playerOpponent]['PF'].rank >= 20) {
                            console.log(player + ': ' + data.regression.opp_team_data.OppPF);
                            playerObj.regressionAlert += 'OppPF: ' + data.regression.opp_team_data.OppPF;
                        }
                        if (data.regression.opp_team_data.OppFGA
                            && finalData.teamAdvancedStats[playerOpponent]['FGA'].rank >= 20) {
                            console.log(player + ': ' + data.regression.opp_team_data.OppFGA);
                            playerObj.regressionAlert += 'OppFGA: ' + data.regression.opp_team_data.OppFGA;

                        }
                        if (data.regression.opp_team_data.OppDRtg
                            && finalData.teamAdvancedStats[playerOpponent]['DRtg'].rank >= 20) {
                            console.log(player + ': ' + data.regression.opp_team_data.OppDRtg);
                            playerObj.regressionAlert += 'OppDRtg: ' + data.regression.opp_team_data.OppDRtg;

                        }
                        if (data.regression.opp_team_data.OppORtg
                            && finalData.teamAdvancedStats[playerOpponent]['DRtg'].rank >= 20) {
                            console.log(player + ': ' + data.regression.opp_team_data.OppORtg);
                            playerObj.regressionAlert += 'OppORtg: ' + data.regression.opp_team_data.OppORtg;

                        }

                        if (data.regression.opp_data.OppPace
                            && finalData.teamAdvancedStats[playerOpponent]['Pace'].rank <= 10) {
                            console.log(player + ': ' + data.regression.opp_data.OppPace);
                            playerObj.regressionAlert += 'OppPace: ' + data.regression.opp_data.OppPace;

                        }


                    if (finalData.dkPlayers[player]) {
                        playerObj.val = parseFloat(data.last_3_games.dk_points / parseFloat(finalData.dkPlayers[player].salary) * 1000).toFixed(2);
                        playerObj.salary = parseFloat(finalData.dkPlayers[player].salary);
                    }

                    playerObj.news = _.find(finalData.news[data.basic_info.team], { 'player': player});

                    // use DK position
                    if (playerOpponent) {
                        var dvpStats = finalData.dvpStats[playerOpponent];
                        playerObj.dvp.last_5 = dvpStats[playerPosition]['Last 5'];
                        playerObj.dvp.last_5_ratio = parseFloat(dvpStats[playerPosition]['Last 5']/ finalData.dvpStats['league']['position'][playerPosition].average).toFixed(2);
                        playerObj.dvp.season = dvpStats[playerPosition]['Season'];
                        playerObj.dvp.season_ratio = parseFloat(dvpStats[playerPosition]['Season']/ finalData.dvpStats['league']['position'][playerPosition].average).toFixed(2);

                        if (data.regression.opp_data.OppDvP
                            && playerObj.dvp.last_5_ratio >= 1.15) {
                            console.log(player + ': ' + data.regression.opp_data.OppDvP);
                            playerObj.regressionAlert += 'OppDvP: ' + data.regression.opp_data.OppDvP;
                        }

                        playerObj.simpleProjection = parseFloat(playerObj.last_3_games.dk_points * playerObj.dvp.last_5_ratio);
                        var tempWeightedNet, avgWeightedNet;
                        if (playerObj.opportunityScore && playerObj.val && playerObj.salary) {
                            tempWeightedNet = parseFloat(0.35*playerObj.opportunityScore + 0.1*playerObj.dvp.last_5 + 0.1*playerObj.last_3_games.playtime
                                + 0.2*playerObj.val + 0.1*playerObj.last_3_games.dk_points + 0.15*playerObj.last_3_games.usage);

                            avgWeightedNet = parseFloat(0.35*playerObj.fppPerMinute + 0.1*playerObj.dvp.season + 0.1*playerObj.stats.playtime
                                + 0.2*playerObj.val + 0.1*playerObj.stats.dk_points + 0.15*playerObj.usage);

                            if (playerObj.lastGameBetterThanAverage.last_1_games == 'up') {
                                tempWeightedNet += 0.5;
                            } else if (playerObj.lastGameBetterThanAverage.last_1_games == 'down') {
                                tempWeightedNet -= 0.5;
                            }

                            if (playerObj.lastGameBetterThanAverage.last_3_games == 'up') {
                                tempWeightedNet += 0.5;
                            } else if (playerObj.lastGameBetterThanAverage.last_3_games == 'down') {
                                tempWeightedNet -= 0.5;
                            }

                            if (playerObj.minuteIncrease.last_1_games == 'up') {
                                tempWeightedNet += 0.5;
                            } else if (playerObj.minuteIncrease.last_1_games == 'down') {
                                tempWeightedNet -= 0.5;
                            }

                            if (playerObj.minuteIncrease.last_3_games == 'up') {
                                tempWeightedNet += 0.5;
                            } else if (playerObj.minuteIncrease.last_3_games == 'down') {
                                tempWeightedNet -= 0.5;
                            }
                            tempWeightedNet = tempWeightedNet.toFixed(2);
                            avgWeightedNet = avgWeightedNet.toFixed(2);
                        } else {
                            tempWeightedNet = 0;
                        }
                        playerObj.tempWeightedNet = parseFloat(tempWeightedNet);
                        playerObj.avgWeightedNet = avgWeightedNet;
                        playerObj.weightedRatio = (tempWeightedNet / avgWeightedNet).toFixed(2);
                        finalData.players.push(playerObj);
                    }

                });
            });
        }
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

    function ftrVsOppFoul(ftr, oppPF) {
        if (ftr > 0.25 && oppPF.stat > 21) {
            return 'up';
        }
        return '';
    };

    function trbVsOppFGA(trb, oppFGA) {
        if (trb > 10 && oppFGA.stat > 84.5) {
            return 'up';
        }
        return '';
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

    function getDefenseVsPositionStatsRank(team, data) {
        var validList = ['3PM', 'AST', 'BLK', 'FG%', 'PTS', 'REB', 'STL'];

        // set categories
        for (var i=0; i<validList.length; i++) {
            // determined the rank based on stat categories
            var category = validList[i];
            finalData.dvpRank['categories'][category] = {};
        }
        // need to remove this extra call
        fetch.getDefenseVsPositionStats(team).then(function (data){

            _.forEach(data, function(stats, position){
                // determine the rank of tonight's matchups for each position
                var dvpPosition = finalData.dvpRank['positions'];
                if (dvpPosition && dvpPosition[position]) {
                    if (dvpPosition[position]['max']['Last 5'] < stats['Last 5']) {
                        dvpPosition[position]['max'] = stats;
                        calcMatchupStrengthByPosition(dvpPosition[position]['max'], stats, position);
                    } else if (dvpPosition[position]['min']['Last 5'] > stats['Last 5']) {
                        dvpPosition[position]['min'] = stats;
                        calcMatchupStrengthByPosition(dvpPosition[position]['min'], stats, position);
                    }
                } else {
                    dvpPosition[position] = {
                        max: stats,
                        min: stats,
                        average: finalData.dvpStats['league']['position'][position].average.toFixed(2)
                    };

                    // set initial matchup strength
                    calcMatchupStrengthByPosition(dvpPosition[position]['max'], stats, position);
                    calcMatchupStrengthByPosition(dvpPosition[position]['min'], stats, position);
                }

                for (var i=0; i<validList.length; i++) {
                    // determined the rank based on stat categories
                    var category = validList[i];
                    var statObj = {
                        team: common.translateTeamNames()[stats['Team']],
                        stat: category,
                        num: stats[category],
                        position: stats['Vs. Pos'],
                        average: finalData.dvpStats['league']['category'][position][category].toFixed(2)
                    };

                    // calc categories for each position
                    var dvpCategory = finalData.dvpRank['categories'][category];
                    if (dvpCategory && dvpCategory[position]) {
                        if (dvpCategory[position]['max']['num'] < stats[category]) {
                            dvpCategory[position]['max'] = statObj;
                            calcMatchupStrengthByCategory(dvpCategory[position]['max'], statObj, position, category);
                        } else if (dvpCategory[position]['min']['num'] > stats[category]) {
                            dvpCategory[position]['min'] = statObj;
                            calcMatchupStrengthByCategory(dvpCategory[position]['min'], statObj, position, category);
                        }
                    } else {
                        dvpCategory[position] = {
                            max: statObj,
                            min: statObj
                        };
                        calcMatchupStrengthByCategory(dvpCategory[position]['max'], statObj, position, category);
                        calcMatchupStrengthByCategory(dvpCategory[position]['min'], statObj, position, category);
                    }

                }
            });
        });

    }

    function calcMatchupStrengthByPosition(dataObj, stats, position) {
        dataObj['matchup'] = parseFloat(stats.Season / finalData.dvpStats['league']['position'][position].average).toFixed(2);
        dataObj['matchup5'] = parseFloat(stats['Last 5'] / finalData.dvpStats['league']['position'][position].average).toFixed(2);
        dataObj['matchup10'] = parseFloat(stats['Last 10'] / finalData.dvpStats['league']['position'][position].average).toFixed(2);
    }

    function calcMatchupStrengthByCategory(dataObj, stats, position, category) {
        dataObj['matchup'] = parseFloat(stats.num / finalData.dvpStats['league']['category'][position][category]).toFixed(2);
    }

    return finalData
}]);