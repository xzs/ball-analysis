app.factory('fetch', ['$http', function($http) {
    return {
        getCSV: function() {
            return $http.get('/csv/DKSalaries.csv').then(function (response) {
                return response.data;
            });
        }
    }
}]);