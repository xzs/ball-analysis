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
        fetch.getPlayer(name).then(function (response) {
            // Player info
            $scope.playerInfo = response.basic_info;
            // Base stats
            $scope.playerStats = response.stats;
            $scope.playerCov = response.cov;
            $scope.playerLast5 = response.last_5_games;

            $scope.playerPlayerTimeAway = response.away_playtime;
            $scope.playerPlayerTimeHome = response.home_playtime;

            $scope.playerGmscAway = response.average_away_gmsc;
            $scope.playerGmscHome = response.average_home_gmsc;

            // Data for against opponents
            var playerTeamData = response.teams_against;
            $scope.teamDataHeader = Object.keys(playerTeamData);
            // add an array of your data objects to enable sorting
            // http://stackoverflow.com/a/27779633
            $scope.teamData = Object.keys(playerTeamData)
             .map(function (key) {
               return playerTeamData[key];
             });
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
            $scope.teams = Object.keys(response).sort();
        });
    }
    function processCSV(data) {
        // process the data into readable JSON format
        processing.setAllPlayersByPosition(data);
        console.log(processing.getEqualDistributionLineUp(local.salary));
    };

    init();
    fetchCSV();

}]);
