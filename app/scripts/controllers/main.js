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
    local.salary = 50000;
    local.allPlayers = {};

    $scope.getPlayers = function(team) {
        $scope.teamPlayers = local.allPlayers[team]
        return $scope.teamPlayers
    }

    $scope.getPlayerData = function(name) {
        $scope.playerName = name;
        fetch.getPlayer(name).then(function (response) {
            var playerTeamData = response.teams_against;
            $scope.teamDataHeader = Object.keys(playerTeamData);
            $scope.teamData = playerTeamData;
        });
    }

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

    function init() {
        fetch.getAllPlayers().then(function (response) {
            local.allPlayers = response;
            $scope.teams = Object.keys(response);
        });
    }
    function processCSV(data) {
        // process the data into readable JSON format
        processing.setAllPlayersByPosition(data);
        // console.log(processing.getEqualDistributionLineUp(salary));

    };

    init();

}]);
