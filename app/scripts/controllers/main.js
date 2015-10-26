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
        console.log(processing.setPlayersByPosition(data));
    };

    fetchCSV();

}]);
