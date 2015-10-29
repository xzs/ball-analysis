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
    var salary = 50000;

    function fetchCSV() {
        fetch.getCSV().then(function (response) {
            // use papa to parse the csv to json
            Papa.parse(response, {
                complete: function(results) {
                    // remove the first element from the list
                    processCSV(_.drop(results.data));
                }
            });
        })
    };

    function fetchPlayer(name) {
        $scope.playerName = name;
        fetch.getPlayer(name).then(function (response) {
            // console.log();
            var playerTeamData = response.teams_against;
            $scope.teamDataHeader = Object.keys(playerTeamData);
            $scope.teamData = playerTeamData;
            // against teams
        })
    }

    function processCSV(data) {
        // process the data into readable JSON format
        processing.setAllPlayersByPosition(data);
        console.log(processing.getEqualDistributionLineUp(salary));

    };

    fetchCSV();
    fetchPlayer('Aaron Gordon');

}]);
