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
        $scope.equalDistributedLineup = processing.getEqualDistributionLineUp(local.salary);
    };

    init();
    fetchCSV();

}]);
