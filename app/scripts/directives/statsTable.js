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

            $scope.playerStatus = function(player){
              var classes = '';
              if (player.status == 'Sidelined') {
                  classes += ' injured-player';
              }

              if (player.last_3_games.dk_points > 20 && player.last_1_games.dk_points > 20 && player.val > 4.5 && player.opportunityScore > 1) {
                classes += ' potential'
              }
              // if there havent been any increase in performance and value
              if (
                  player.minuteIncrease.last_1_games == 'none' && player.minuteIncrease.last_3_games == 'none'
                  && player.lastGameBetterThanAverage.last_1_games == 'none' && player.lastGameBetterThanAverage.last_3_games == 'none'
                  && player.val < 4.0
                ) {
                classes += ' warning'
              }
              if (player.last_3_games.dk_points < 20 && player.last_1_games.dk_points < 20 && player.val < 4.0 && player.dvp['last_5_ratio'] < 1) {
                classes += ' endangered'
              }
              return classes;
            }


        },
        templateUrl: function(elem, attr) {
            return 'views/directives/table-stats-'+attr.type+'.html'
        }
    }
});