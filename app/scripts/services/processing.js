app.factory('processing', function() {
    var finalData = {};

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

    // this is more so the constructor
    finalData.setAllPlayersByPosition = function(data) {
        var dataLength = data.length;
        // sub categories
        finalData['G'] = [];
        finalData['F'] = [];
        finalData['All'] = [];

        for (var i=0; i<dataLength; i++) {
            var player = {
                pos: data[i][0],
                name: data[i][1],
                salary: data[i][2],
                appg: data[i][4],
                team: data[i][5],
            };

            player.appgCostRatio = calcPlayerCostToPoints(player);

            // categorize them by position
            if (!finalData[data[i][0]]) {
                finalData[data[i][0]] = [];
                // If G
                if (data[i][0] == 'PG' || data[i][0] == 'SG') {
                    finalData['G'].push(player);
                }
                // If F
                if (data[i][0] == 'SF' || data[i][0] == 'PF') {
                    finalData['F'].push(player);
                }
                finalData[data[i][0]].push(player);
            } else {
                // If G
                if (data[i][0] == 'PG' || data[i][0] == 'SG') {
                    finalData['G'].push(player);
                }
                // If F
                if (data[i][0] == 'SF' || data[i][0] == 'PF') {
                    finalData['F'].push(player);
                }
                finalData[data[i][0]].push(player);
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

    return finalData
});