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

            $scope.selectedPlayers = [];
            $scope.toggleSelectedPlayer = function(player) {
              var playerIndex = _.indexOf($scope.selectedPlayers, player);
              if (playerIndex == -1){
                $scope.selectedPlayers.push(player);
              } else {
                $scope.selectedPlayers.splice(playerIndex, 1);
              }
            }

            $scope.removeSelectedPlayers = function(players) {
              $scope.removedPlayers = players;
              $scope.data = _.difference($scope.data, players)
              $scope.selectedPlayers = [];
            }

            $scope.sortByPosition = function(players) {
              var playersLength = players.length;
              var playersByPosition = {
                'G': [],
                'F': [],
                'All': [],
              };
              for (var i=0; i<playersLength; i++) {
                player = players[i];
                position = player.basic_info.position;
                // categorize them by position
                if (!playersByPosition[position]) {
                    playersByPosition[position] = [];
                    // If G
                    if (position == 'PG' || position == 'SG') {
                        playersByPosition['G'].push(player);
                    }
                    // If F
                    if (position == 'SF' || position == 'PF') {
                        playersByPosition['F'].push(player);
                    }
                    playersByPosition[position].push(player);
                } else {
                    // If G
                    if (position == 'PG' || position == 'SG') {
                        playersByPosition['G'].push(player);
                    }
                    // If F
                    if (position == 'SF' || position == 'PF') {
                        playersByPosition['F'].push(player);
                    }
                    playersByPosition[position].push(player);
                }
                playersByPosition['All'].push(player);
              }
              console.log(playersByPosition)
            }

        },
        templateUrl: function(elem, attr) {
            return 'views/directives/table-stats-'+attr.type+'.html'
        }
    }
});