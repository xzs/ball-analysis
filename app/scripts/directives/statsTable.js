app.directive('statsTable', function() {
  return {
    restrict: 'E',
    scope: {
      // the key needs to match that within the template
      data: '=data'
    },
    templateUrl: 'views/directives/statsTable.html'
  };
});