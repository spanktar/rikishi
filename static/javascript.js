// Angular stuff
var nikishiApp = angular.module('nikishiApp', []);

nikishiApp.controller('nikishiCtrl', function ($scope, $http) {

    $scope.formData = {
        apiid: "suq9OWVasvajw2",
        apikey: "0dH80SvcwhRQ6HLvV5GJAKOoxH1NZdy85iMMhVhmgArxv99i2ClD3na7AxpelpSP"
    };

    $scope.collectors = [];
    $scope.selectedCollectors = {};
    $scope.filteredCollectors = {};
    $scope.counter = Object.keys($scope.selectedCollectors).length;
    $scope.editableFields = ['timeZone', 'ephemeral'];
    $scope.uneditableSourceFields = ['alive', 'id', 'selected'];
    $scope.addFields = ['automaticDateParsing', 'blacklist', 'category', 'description', 'encoding', 'forceTimeZone', 'multilineProcessingEnabled', 'name', 'pathExpression', 'sourceType', 'useAutolineMatching'];

    $scope.APICredentialForm = function() {
        $('#gatherModal').modal('show');
        $http.post('getCollectors', $scope.apiFormData).success(function(data) {
            $scope.collectors = data.results;
            $('#gatherModal').modal('hide');
        });
        // TODO: Add spinner
    };

    $scope.sourceinfo = {};
    $scope.getSources = function() {
        var collectors = { 'collectors': $scope.selectedCollectors};
        var payload = angular.extend({}, $scope.apiFormData, collectors);
        $http.post('getSources', payload).success(function(data) {
            $scope.sourceinfo = data.results;
        });
    };

    $scope.commitChanges = function() {
        var payload = angular.extend({}, $scope.apiFormData, $scope.sourceinfo);
        var method = 'putCollectors';

        if (typeof $scope.addcollector !== 'undefined' && $scope.addcollector.selected === true) {
            var collectors = { 'collectors': $scope.selectedCollectors};
            payload = angular.extend({}, $scope.apiFormData, $scope.addcollector, collectors);
            method = 'addCollector';
        }

        $http.post(method, payload).success(function(data) {
            $scope.commitResponse = data.results;
        });
    };

    $scope.allSelected = false;
    $scope.toggleSelected = function(selection) {
        $scope.allSelected = !$scope.allSelected;
        angular.forEach(selection, function(item){
            item.selected = $scope.allSelected;
        });
    };

});

$('.collapse').on('show.bs.collapse', function(){
    $(this).parent().find(".glyphicon-chevron-down").removeClass("glyphicon-chevron-down").addClass("glyphicon-chevron-up");
}).on('hide.bs.collapse', function(){
    $(this).parent().find(".glyphicon-chevron-up").removeClass("glyphicon-chevron-up").addClass("glyphicon-chevron-down");
});

// Spinner
var opts = {
  lines: 12, // The number of lines to draw
  length: 21, // The length of each line
  width: 9, // The line thickness
  radius: 0, // The radius of the inner circle
  corners: 1, // Corner roundness (0..1)
  rotate: 0, // The rotation offset
  direction: 1, // 1: clockwise, -1: counterclockwise
  color: '#000', // #rgb or #rrggbb or array of colors
  speed: 1, // Rounds per second
  trail: 60, // Afterglow percentage
  shadow: false, // Whether to render a shadow
  hwaccel: false, // Whether to use hardware acceleration
  className: 'spinner', // The CSS class to assign to the spinner
  zIndex: 2e9, // The z-index (defaults to 2000000000)
  top: 'auto', // Top position relative to parent in px
  left:'auto' // Left position relative to parent in px
};

var target = document.getElementById('spinner_center');
var spinner = new Spinner(opts).spin(target);
