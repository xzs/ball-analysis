app.directive('statsTable', function() {
    return {
        restrict: 'EA',
        scope: {
          // the key needs to match that within the template
          data: '=data',
          heading: '=heading',
          fantasy: '=fantasy',
          news: '=news'
        },
        controller: function($scope) {
            // set default predicate to the gmsc
            $scope.predicate = 'stats.gmsc';
            $scope.reverse = true;
            $scope.order = function(predicate) {
                $scope.reverse = ($scope.predicate === predicate) ? !$scope.reverse : false;
                $scope.predicate = predicate;
            }
            $scope.showMin = false;
            $scope.showMax = true;
            $scope.toggleCategories = function(category) {
              if (category == 'max') {
                $scope.showMin = false;
                $scope.showMax = true;
              } else {
                $scope.showMin = true;
                $scope.showMax = false;
              }
            }
        },
        templateUrl: function(elem, attr) {
            return 'views/directives/table-stats-'+attr.type+'.html'
        }
    }
});