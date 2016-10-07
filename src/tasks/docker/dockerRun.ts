"use strict";

import * as path from "path";
import * as tl from "vsts-task-lib/task";
import DockerConnection from "./dockerConnection";

export function run(connection: DockerConnection): any {
    var command = connection.createCommand();
    command.arg("run");

    var detached = tl.getBoolInput("detached");
    if (detached) {
        command.arg("-d");
    }

    var entrypoint = tl.getInput("entrypoint");
    if (entrypoint) {
        command.arg(["--entrypoint", entrypoint]);
    }

    tl.getDelimitedInput("envVars", "\n").forEach(envVar => {
        command.arg(["-e", envVar]);
    });

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

    command.arg("-t");

    tl.getDelimitedInput("volumes", "\n").forEach(volume => {
        command.arg(["-v", volume]);
    });

    var workDir = tl.getInput("workDir");
    if (workDir) {
        command.arg(["-w", workDir]);
    }

    var imageName = tl.getInput("imageName", true);
    command.arg(imageName);

    var containerCommand = tl.getInput("containerCommand");
    if (containerCommand) {
        command.arg(containerCommand);
    }

    return command.exec();
}
