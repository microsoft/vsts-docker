"use strict";

import * as tl from "vsts-task-lib/task";
import DockerConnection from "./dockerConnection";

// Change to any specified working directory
tl.cd(tl.getInput("cwd"));

// Connect to any specified Docker host and/or registry 
var connection = new DockerConnection();
connection.open(tl.getInput("dockerHostEndpoint"), tl.getInput("dockerRegistryEndpoint"));

// Run the specified action
var action = tl.getInput("action", true);
var output = "";
/* tslint:disable:no-var-requires */
require({
    "Build an image": "./dockerBuild",
    "Push an image": "./dockerPush",
    "Run an image": "./dockerRun",
    "Run a Docker command": "./dockerCommand",
    "Clean all images": "./dockerClean"
}[action]).run(connection)
.then((result) => {
    tl._writeLine("Result: " + result);
    const outputVariable = tl.getInput("outputVariableName", false);
    tl._writeLine("Output variable: ." + outputVariable + ".");
    if (outputVariable !== null) {
        tl.setVariable(outputVariable, result);
        tl._writeLine(`Set ${outputVariable} to: ${result}`);
    } else {
        tl._writeLine("Skipping writing of output because no output variable was set. This is normal.");
    }
})
.fin(function cleanup() {
    connection.close();
})
.then(function success() {
    tl.setResult(tl.TaskResult.Succeeded, "");
}, function failure(err) {
    tl.setResult(tl.TaskResult.Failed, err.message);
})
.done();
