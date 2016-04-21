/// <reference path="../../../typings/vsts-task-lib/vsts-task-lib.d.ts" />
"use strict";
var tl = require("vsts-task-lib/task");

var action = tl.getInput("action", true);

switch (action) {
    case "Run an image":
        var dockerRun = require("./dockerRun");
        dockerRun.dockerRun();
        break;
    case "Build an image":
        var dockerBuild = require("./dockerBuild");
        dockerBuild.dockerBuild();
        break;
    case "Push an image":
        var dockerPublish = require("./dockerPublish");
        dockerPublish.dockerPublish();
        break;
    case "Run a Docker command":
        var dockerAnyCmd = require("./dockerAnyCmd");
        dockerAnyCmd.runCommand();
        break;
}