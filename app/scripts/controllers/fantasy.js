'use strict';

app.controller('FantasyCtrl',
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
    local.year = '2016';
    $scope.file = {};
    $scope.file.csv = "";
    $scope.lineups = {};


    function init(year) {
        fetch.getAllPlayers(year).then(function (response) {
            local.allPlayers = response;
            $scope.teams = Object.keys(response).sort();
        });
    }

    $scope.getCSV = function(csv){
        Papa.parse(csv, {
            complete: function(results) {
                // remove the first element from the list
                processCSV(_.drop(results.data));
            }
        });
    }

    function processCSV(data) {
        // process the data into readable JSON format
        processing.setAllPlayersByPosition(data);
        $scope.lineups.equalDistributedLineup = processing.getEqualDistributionLineUp(local.salary);
        // Check for starters
        _.forEach($scope.lineups.equalDistributedLineup, function(player, position){
            player.isStarter = _.includes(Object.keys(local.starters), player.name);
        });
        // force apply as the file reader API will work asynchronously, outside of the angularjs "flow".
        // Therefore, you have to make apply int he end of the onload function
        // http://stackoverflow.com/a/33038028
        $scope.$apply();

    };

    function processDepthChart() {
        fetch.getStarters().then(function (data){
            local.starters = data;
        });
    }

    init(local.year);
    processDepthChart();

}]);
