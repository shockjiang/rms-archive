
var rmsApp = angular.module('rmsApp', ['ngRoute','ngResource','ui.bootstrap']);

Array.prototype.clear = function() {
  while (this.length > 0) {
    this.pop();
  }
};

rmsApp.config(['$routeProvider',
  function($routeProvider) {
    $routeProvider.
      when('/dashboard', {
        templateUrl: 'partials/dashboard.html',
        // controller: 'PhoneListCtrl'
      }).
      when('/ndnroute', {
        templateUrl: 'partials/ndnroute.html',
        // controller: 'PhoneListCtrl'
      }).
      when('/content', {
        templateUrl: 'partials/content.html',
        // controller: 'PhoneDetailCtrl'
      }).
      when('/cmd', {
        templateUrl: 'partials/command.html',
        // controller: 'PhoneDetailCtrl'
      }).
      otherwise({
        redirectTo: '/dashboard'
      });
  }
]);

rmsApp.filter('status2icon', function() {
    return function(input) {
        switch(input){
            case 'ok':
                return ['fa-check','text-success'];
            case 'err':
                return ['fa-times','text-danger'];
            case 'run':
                return ['fa-spinner','text-primary','fa-spin'];
            case 'warn':
                return ['fa-exclamation-circle','text-warning'];
        }
        return '';
    };
});

rmsApp.factory('HostModel', function($http){
    var Model = function(){
        this.hosts = [];
    }
    Model.prototype.reload_hosts = function(){
        var self = this;
        $http.get('api/hostlist').success(function(host_list){
            self.hosts.clear();
            for (var i = host_list.length - 1; i >= 0; i--) {
                self.hosts.push({
                    name: host_list[i]['name'],
                    selected: false,
                    status: ''
                });
            }
        });
    }
    Model.prototype.setAll = function(selected){
        for (var i = this.hosts.length - 1; i >= 0; i--) {
            this.hosts[i].selected = selected;
        }
    }
    Model.prototype.allSelected = function (){
        if(!this.hosts.length)
            return false;
        var all = true;
        for (var i = this.hosts.length - 1; i >= 0; i--) {
            all = all && this.hosts[i].selected;
        }
        return all
    }
    return new Model();
})

rmsApp.factory('CmdResultModel', function(){
    var model = function(){
        this.results = []
    }
    model.prototype.clear = function(){
        this.results.clear()
    }
    model.prototype.add = function(host, result){
        this.results.push({
            title: 'Result of '+host,
            content: result
        })
        console.log(this.results)
    }
    return new model()
})

rmsApp.controller('HostSelection', function ($http,$scope,HostModel) {
    $scope.hostmodel = HostModel
    $scope.allselected = false
    $scope.onitemchanged = function(){
        $scope.allselected = $scope.hostmodel.allSelected();
    }
    $scope.onallchecked = function(){
        $scope.hostmodel.setAll($scope.allselected);
    }
});

rmsApp.controller('CmdLine', function ($scope,HostModel,$resource,CmdResultModel) {
    var runCmd = $resource('api/execute/:host/:cmd');
    $scope.hostmodel = HostModel
    $scope.onexecute = function(){
        CmdResultModel.clear();
        var hs = $scope.hostmodel.hosts;
        for (var i = hs.length - 1; i >= 0; i--) {
            var h = hs[i];
            if(h.selected){
                h.status = 'run';
                runCmd.get({host: h.name, cmd: $scope.inputcmd},(function(h){return function(content){
                    h.status = 'ok';
                    CmdResultModel.add(h.name, content.text)
                }})(h),(function(h){return function(){
                    h.status = 'err';
                }})(h));
            }
        }
    }
});

rmsApp.controller('CmdResult', function (CmdResultModel, $scope){
    $scope.cmdresults = CmdResultModel.results
})