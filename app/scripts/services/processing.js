app.factory('processing', function() {
    var finalData = {};
    // this is more so the constructor
    finalData.setPlayersByPosition = function(data) {
        var dataLength = data.length;
        for (var i=0; i<dataLength; i++) {
            var player = {
                pos: data[i][0],
                name: data[i][1],
                salary: data[i][2],
                appg: data[i][4],
                team: data[i][5]
            };
            // categorize them by position
            if (!finalData[data[i][0]]) {
                finalData[data[i][0]] = [];
                finalData[data[i][0]].push(player);
            } else {
                finalData[data[i][0]].push(player);
            }
        }
        return finalData;
    }
    return finalData
});