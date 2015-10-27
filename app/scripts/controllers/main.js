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
        // get the csv
        fetch.getCSV().then(function (response) {
            Papa.parse(response, {
                complete: function(results) {
                    // remove the first element from the list
                    processCSV(_.drop(results.data));
                }
            });
        })
    };

    function processCSV(data) {
        // process the data into readable JSON format
        processing.setAllPlayersByPosition(data);
        // console.log(processing.getCostEffectivePlayersByPosition('C', 5));
        // console.log(processing.getPlayersByPosition('SF'));
        // console.log(processing.getExpensivePlayersByPosition('SF', 2));
        console.log(processing.getLineUp(salary));
        // Go though each and minus the salary
        // Sample only from the top 20% of the dataset
        // Find who is the most cost effective from each of the ranks

    };

    fetchCSV();

}]);
