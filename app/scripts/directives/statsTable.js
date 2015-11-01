app.directive('statsTable', function() {
    return {
        restrict: 'E',
        scope: {
          // the key needs to match that within the template
          data: '=data'
        },
        controller: ['$scope', function($scope) {
            $scope.predicate = 'stats.gmsc';
            $scope.reverse = true;
            $scope.order = function(predicate) {
                console.log("here");
                $scope.reverse = ($scope.predicate === predicate) ? !$scope.reverse : false;
                $scope.predicate = predicate;
            }
        }],
        templateUrl: 'views/directives/statsTable.html'
    }
});