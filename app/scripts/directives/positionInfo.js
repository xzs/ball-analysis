app.directive('positionInfo', function(){
	return{
		restrict: 'E',
		scope: {
			player: '=player',
			playertype: '=playertype',
			position: '@position'
		},
		templateUrl: 'views/directives/depth_chart/position-info.html',
		link: function(scope, element, attrs){
			scope.getPlayerStatus = function(){
				var classes = '';
				if (scope.player == scope.playertype[0] && scope.player.status == 'Available') {
					classes += ' status-green bold';
				} else if (scope.player == scope.playertype[0] && scope.player.status == 'Sidelined') {
					classes += ' status-red bold';
				}

				if (scope.player.base_stats && scope.player.base_stats['playtime'] > 20 && scope.player.USG > 20) {
					classes += ' highlight text-blue bold';
				} else if (scope.player.base_stats && scope.player.base_stats['playtime'] > 20 && scope.player.USG > 15) {
					classes += ' text-pink';
				}
				return classes;
			}
			scope.twentytwenty = function(m1, m2){
				if (m1 > 20 && m2 > 20 && scope.player.base_stats['playtime'] > 30) {
					return 'twentytwenty';
				}
			}
		}
	}
})