app.factory('fetch', ['$http', function($http) {
    return {
        getStarters: function() {
            return $http.get('scrape/misc/starters.json').then(function (response) {
                return response.data;
            });
        },
        getPlayer: function(year, name) {
            return $http.get('scrape/json_files/'+year+'/'+name+'.json').then(function (response) {
                return response.data;
            });
        },
        getAllPlayers: function(year) {
            return $http.get('scrape/json_files/'+year+'/all_players.json').then(function (response) {
                return response.data;
            });
        }
    }
}]);