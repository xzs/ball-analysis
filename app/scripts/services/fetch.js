app.factory('fetch', ['$http', function($http) {
    return {
        getStarters: function() {
            return $http.get('scrape/misc/starters.json').then(function (response) {
                return response.data;
            });
        },
        getPlayer: function(name) {
            return $http.get('scrape/json_files/'+name+'.json').then(function (response) {
                return response.data;
            });
        },
        getAllPlayers: function() {
            return $http.get('scrape/json_files/all_players.json').then(function (response) {
                return response.data;
            });
        }
    }
}]);