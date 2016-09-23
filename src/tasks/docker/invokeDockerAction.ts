"use strict";

import * as tl from "vsts-task-lib/task";
import DockerConnection from "./dockerConnection";

tl.cd(tl.getInput("cwd"));

var connection = new DockerConnection();
connection.open(tl.getInput("dockerHostEndpoint"), tl.getInput("dockerRegistryEndpoint"));

var action = tl.getInput("action", true);
var promise: any;
switch (action) {
    /* tslint:disable:no-var-requires */
    case "Run an image":
        promise = require("./dockerRun").run(connection);
        break;
    case "Build an image":
        promise = require("./dockerBuild").run(connection);
        break;
    case "Push an image":
        promise = require("./dockerPush").run(connection);
        break;
    case "Run a Docker command":
        promise = require("./dockerCommand").run(connection);
        break;
    /* tslint:enable:no-var-requires */
}

promise
.fin(function cleanup() {
    connection.close();
})
.fail(function failure(err) {
    tl.setResult(tl.TaskResult.Failed, err.message);
})
.then(function success() {
    tl.setResult(tl.TaskResult.Succeeded, "");
})
.done();
