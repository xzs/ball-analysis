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

    function init() {
        fetch.getAllPlayers().then(function (response) {
            local.allPlayers = response;
            $scope.teams = Object.keys(response).sort();
        });
    }

    init();

}]);
