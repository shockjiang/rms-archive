
var rmsApp = angular.module('rmsApp', ['ngRoute','ngResource','ui.bootstrap','angularFileUpload']);

Array.prototype.clear = function() {
  while (this.length > 0) {
    this.pop();
  }
};

String.prototype.toHex = function() {
    var hex = '';
    for(var i=0;i<this.length;i++) {
        hex += this.charCodeAt(i).toString(16);
    }
    return hex;
}

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
    Model.prototype.selectedHosts = function (){
        var ret = []
        for (var i = this.hosts.length - 1; i >= 0; i--) {
            if(this.hosts[i].selected)
                ret.push(this.hosts[i].name);
        }
        return ret;
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
    }
    return new model()
})

rmsApp.factory('ContentResources', function ($resource){
    return $resource('api/content/:hosts/:filter', null, {
        list: {method: 'GET', isArray: true},
        remove: {method: 'DELETE'},
        upload: {method: 'PUT'}
    })
})

rmsApp.controller('HostSelection', function ($http,$scope,HostModel,$rootScope) {
    $scope.hostmodel = HostModel
    $scope.allselected = false
    $scope.onitemchanged = function(){
        $scope.allselected = $scope.hostmodel.allSelected();
        $rootScope.$broadcast('HostSelectionChanged')
    }
    $scope.onallchecked = function(){
        $scope.hostmodel.setAll($scope.allselected);
        $rootScope.$broadcast('HostSelectionChanged')
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
                runCmd.get({host: h.name, cmd: $scope.inputcmd.toHex()},(function(h){return function(content){
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

rmsApp.controller('ContentList', function ($scope, HostModel, ContentResources){
    $scope.files = []
    $scope.bLoading = $scope.bError = false
    $scope.nameFilter = ''
    $scope.doReload = function() {
        var hs = HostModel.selectedHosts().join(',');
        $scope.bLoading=true
        $scope.bError = false
        ContentResources.list({hosts: hs, filter: $scope.nameFilter.toHex()}, function(result){
            $scope.bLoading=false
            $scope.files.clear()
            for (var i = result.length - 1; i >= 0; i--) {
                $scope.files.push({
                    name: result[i]['c'],
                    selected: false
                });
            };
        },function(){
            $scope.bLoading=false
            $scope.files.clear()
            $scope.bError = true
        })
    }
    $scope.refresh = function(){
        $scope.doReload()
    }
    // $scope.upload = function(){

    // }
    $scope.remove = function(){
        var hs = HostModel.selectedHosts().join(',');
        for (var i = $scope.files.length - 1; i >= 0; i--) {
            if($scope.files[i].selected){
                ContentResources.remove({hosts: hs, filter: $scope.files[i].name.toHex()},function(){
                    $scope.doReload();
                });
            }
        };
    }
    $scope.filterChange = function(){
        $scope.doReload()
    }
    $scope.$on('HostSelectionChanged', function(){
        $scope.doReload()
    })
    $scope.$on('ContentUploadFinished', function(){
        $scope.doReload()
    })
})

rmsApp.controller('ContentUpload', function ($scope, HostModel, $rootScope, $upload){
    $scope.content_name = '';
    $scope.drop_filename = null;
    $scope.start_upload = function() {
        var hs = HostModel.selectedHosts().join(',');
        if(!hs || !$scope.content_name || !$scope.pendingFiles){
            console.log('empty input');
            $scope.notify={msg:'Please select hosts!', type:'warning'}
            return;
        }
        $scope.notify = null;
        var files = $scope.pendingFiles;
        // for (var i = 0; i < files.length; i++) {
            var file = files[0];
            $scope.upload = $upload.upload({
                url: 'api/content/'+hs+'/'+$scope.content_name.toHex(),
                method: 'POST',
                // headers: {'header-key': 'header-value'},
                // withCredentials: true,
                // data: {'content_name': $scope.content_name},
                file: file, // or list of files: files for html5 only
                /* set the file formData name ('Content-Desposition'). Default is 'file' */
                fileFormDataName: 'file', //or a list of names for multiple files (html5).
            }).progress(function(evt) {
                $scope.progress_val = Math.min(100, parseInt(100.0 * evt.loaded / evt.total));
                $scope.progress_text = evt.loaded + ' / ' + evt.total;
                $scope.bUploading = ($scope.progress_val < 100);
                console.log('percent: ' + parseInt(100.0 * evt.loaded / evt.total));
            }).then(function(data, status, headers, config) {
                    $scope.bUploading = false;
                    $rootScope.$broadcast('ContentUploadFinished')
                    $scope.notify={msg:'Uploaded successfully!', type:'success'}
                },function(){
                    $scope.bUploading = false;
                    $scope.notify={msg:'Failed to upload!', type:'danger'}
                });
        // }
    }
    $scope.onFileDrop = function($files) {
        console.log($files)
        $scope.pendingFiles = $files;
        $scope.drop_filename = $files[0].name;
    };
    $scope.onFileSelect = function($files) {
        console.log($files)
        $scope.pendingFiles = $files;
    };
})

rmsApp.controller('HostStatus', function ($scope, $http){
    $scope.hosts = []
    $scope.reload_status = function(){
        $http.get('api/sys/*/status').success(function(host_list){
            for (var i in host_list) {
                var item = host_list[i];
                if(item){
                    item.name = i;
                    item.updated = new Date(item.updated*1000)
                    $scope.hosts.push(item);
                }
            }
        });
    }
    $scope.btn_reboot = function(h){
        $http.get('api/sys/'+h+'/reboot').success(function(){

        });
    }
})
