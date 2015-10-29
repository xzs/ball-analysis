app.factory('fetch', ['$http', function($http) {
    return {
        getCSV: function() {
            return $http.get('csv/DKSalaries.csv').then(function (response) {
                return response.data;
            });
        },
        getPlayer: function(name) {
            return $http.get('scrape/json_files/'+name+'.json').then(function (response) {
                return response.data;
            });
        }
    }
}]);