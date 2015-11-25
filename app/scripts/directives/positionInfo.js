app.directive('positionInfo', function(){
	return{
		restrict: 'E',
		scope: {
			player: '=player',
			position: '=position'
		},
		templateUrl: 'views/directives/depth_chart/position-info.html',
		link: function(scope, element, attrs){
			scope.getPlayerStatus = function(){
				if (scope.player == scope.position[0] && scope.player.status == 'Available') {
					return 'status-green';
				} else if (scope.player == scope.position[0] && scope.player.status == 'Sidelined') {
					return 'status-red';
				}
			}
		}
	}
})