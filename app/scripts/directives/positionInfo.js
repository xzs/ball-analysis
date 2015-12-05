app.directive('positionInfo', function(){
    return{
        restrict: 'E',
        scope: {
            player: '=player',
            playertype: '=playertype',
            position: '@position',
            news: '=news',
        },
        templateUrl: 'views/directives/depth_chart/position-info.html',
        link: function(scope){

            scope.getPlayerStatus = function(){
                var classes = '';
                if (scope.player == scope.playertype[0] && scope.player.status == 'Available') {
                    classes += ' status-green bold';
                } else if (scope.player.status == 'Sidelined') {
                    classes += ' injured-player';
                }

                if (scope.player.base_stats.stats && scope.player.base_stats.stats['playtime'] > 20 && scope.player.USG > 20) {
                    classes += ' highlight text-blue bold';
                } else if (scope.player.base_stats.stats && scope.player.base_stats.stats['playtime'] > 20 && scope.player.USG > 15) {
                    classes += ' text-pink';
                }
                return classes;
            }
            scope.twentytwenty = function(m1, m2){
                if (m1 > 20 && m2 > 20 && scope.player.base_stats['playtime'] > 30) {
                    return 'twentytwenty';
                }
            }

            scope.tooltip = function() {
                var news = _.findLast(scope.news[scope.player.team], {'player': scope.player.name});
                if (news) {
                    return news.report;
                }
                return null;
            }
        }
    }
})