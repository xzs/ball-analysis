app.directive('statsTable', function() {
    return {
        restrict: 'A',
        scope: {
          // the key needs to match that within the template
          data: '=data',
          heading: '=heading',
        },
        controller: ['$scope', function($scope) {
            // set default predicate to the gmsc
            $scope.predicate = 'stats.gmsc';
            $scope.reverse = true;
            $scope.order = function(predicate) {
                $scope.reverse = ($scope.predicate === predicate) ? !$scope.reverse : false;
                $scope.predicate = predicate;
            }
        }],
        templateUrl: function(elem, attr) {
            return 'views/directives/table-stats-'+attr.type+'.html'
        }
    }
});