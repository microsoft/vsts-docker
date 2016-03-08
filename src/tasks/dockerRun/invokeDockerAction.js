/// <reference path="../../../typings/vsts-task-lib/vsts-task-lib.d.ts" />
"use strict";
var tl = require("vsts-task-lib/task");

var action = tl.getInput("action", true);

switch (action) {
    case "run a container":
        var dockerRun = require("./dockerRun");
        dockerRun.dockerRun();
        break;
    case "build an image":
        var dockerBuild = require("./dockerBuild");
        dockerBuild.dockerBuild();
        break;
}