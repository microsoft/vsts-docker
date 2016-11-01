"use strict";

import * as tl from "vsts-task-lib/task";
import DockerComposeConnection from "./dockerComposeConnection";

export function run(connection: DockerComposeConnection): any {
    var command = connection.createComposeCommand();
    command.arg("run");

    var detached = tl.getBoolInput("detached");
    if (detached) {
        command.arg("-d");
    }

    var entrypoint = tl.getInput("entrypoint");
    if (entrypoint) {
        command.arg(["--entrypoint", entrypoint]);
    }

    var containerName = tl.getInput("containerName");
    if (containerName) {
        command.arg(["--name", containerName]);
    }

    tl.getDelimitedInput("ports", "\n").forEach(port => {
        command.arg(["-p", port]);
    });

    if (!detached) {
        command.arg("--rm");
    }

    var workDir = tl.getInput("workDir");
    if (workDir) {
        command.arg(["-w", workDir]);
    }

    var serviceName = tl.getInput("serviceName", true);
    command.arg(serviceName);

    var containerCommand = tl.getInput("containerCommand");
    if (containerCommand) {
        command.line(containerCommand);
    }

    var promise = command.exec();

    if (!detached) {
        promise = promise.then(() => {
            var downCommand = connection.createComposeCommand();
            downCommand.arg("down");
            return downCommand.exec();
        });
    }

    return promise;
}
