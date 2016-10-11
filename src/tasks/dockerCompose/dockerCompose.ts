"use strict";

import * as tl from "vsts-task-lib/task";
import DockerComposeConnection from "./dockerComposeConnection";

// Change to any specified working directory
tl.cd(tl.getInput("cwd"));

// Connect to any specified Docker host and/or registry 
var connection = new DockerComposeConnection();
connection.open(tl.getInput("dockerHostEndpoint"), tl.getInput("dockerRegistryEndpoint"))
.then(function runAction() {
    // Run the specified action
    var action = tl.getInput("action", true);
    /* tslint:disable:no-var-requires */
    return require({
        "Build services": "./dockerComposeBuild",
        "Push services": "./dockerComposePush",
        "Run services": "./dockerComposeUp",
        "Write service image digests": "./dockerComposeLock",
        "Combine configuration": "./dockerComposeConfig",
        "Run a Docker Compose command": "./dockerComposeCommand"
    }[action]).run(connection);
    /* tslint:enable:no-var-requires */
})
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
