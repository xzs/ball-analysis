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

            $scope.getPermutations = function(players) {

                var sets = permutate(players, 8);
                var finalList = [];
                for (var i=0; i<sets.length; i++){
                    var gCount = 0, fCount=0, cCount=0, sgCount=0, pgCount=0, sfCount=0, pfCount=0;
                    var fppPerMinute=0, opportunityScore=0, dkPoints=0, last3=0;
                    _.forEach(sets[i], function(player, set) {
                        if (player.basic_info.position == 'PG') {
                            gCount += 1;
                            pgCount += 1;
                        } else if (player.basic_info.position == 'SG') {
                            gCount += 1;
                            sgCount += 1;
                        } else if (player.basic_info.position == 'SF') {
                            fCount += 1;
                            sfCount += 1;
                        } else if (player.basic_info.position == 'PF') {
                            fCount += 1;
                            pfCount += 1;
                        } else if (player.basic_info.position == 'C'){
                            cCount += 1;
                        }
                        fppPerMinute += parseFloat(player.fppPerMinute)
                        opportunityScore += parseFloat(player.opportunityScore)
                        dkPoints += parseFloat(player.stats.dk_points)
                        last3 += parseFloat(player.last_3_games.dk_points)
                    });
                    // console.log('PG: '+pgCount+', SG: '+sgCount+', SF: '+sfCount+', PF: '+pfCount+', C: '+cCount);
                    // lineup criteria
                    if  (    cCount >= 1
                            && sgCount >= 1
                            && pgCount >= 1
                            && sfCount >= 1
                            && pfCount >= 1
                            && gCount >= 2 && fCount >= 2 && cCount < 3
                        )
                    {
                        // calc the total salary
                        var salary = _.sumBy(sets[i], 'salary');
                        var usage = _.sumBy(sets[i], 'usage');
                        var tempWeightedNet = _.sumBy(sets[i], 'tempWeightedNet');
                        if (salary <= 50000 && salary >= 49300){
                            if (!_.find(finalList, { 'salary': salary, 'fppPerMinute': fppPerMinute, 'opportunityScore':opportunityScore, 'usage':usage, 'tempWeightedNet':tempWeightedNet })) {
                                finalList.push({
                                    'players': sets[i],
                                    'salary': salary,
                                    'fppPerMinute': fppPerMinute,
                                    'opportunityScore': opportunityScore,
                                    'usage': usage,
                                    'dk_points': dkPoints,
                                    'last3': last3,
                                    'tempWeightedNet': tempWeightedNet,
                                });
                            }
                        }
                    }
                }
                finalList = sortKey('last3', finalList);
                console.log(finalList);

            }

            // http://stackoverflow.com/questions/18201617/generate-all-subsets-of-a-set-in-javascript
            // http://stackoverflow.com/a/18201618
            var permutate = function(input, size){
                var results = [], result, mask, total = Math.pow(2, input.length);
                for(mask = 0; mask < total; mask++){
                    result = [];
                    i = input.length - 1;
                    do{
                        if( (mask & (1 << i)) !== 0){
                            result.push(input[i]);
                        }
                    }while(i--);
                    if( result.length == size){
                        results.push(result);
                    }
                }
                return results;
            }
            // http://stackoverflow.com/a/5073866
            var sortKey = function (prop, arr) {
                prop = prop.split('.');
                var len = prop.length;

                arr.sort(function (a, b) {
                    var i = 0;
                    while( i < len ) {
                        a = a[prop[i]];
                        b = b[prop[i]];
                        i++;
                    }
                    if (a < b) {
                        return -1;
                    } else if (a > b) {
                        return 1;
                    } else {
                        return 0;
                    }
                });
                return arr;
            };
        },
        templateUrl: function(elem, attr) {
            return 'views/directives/table-stats-'+attr.type+'.html'
        }
    }
});