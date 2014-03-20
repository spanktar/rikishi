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

    $scope.APICredentialForm = function() {
        $http.post('getCollectors', $scope.apiFormData).success(function(data) {

            $scope.collectors = data.results;
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
        $http.post('putCollectors', payload).success(function(data) {
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
