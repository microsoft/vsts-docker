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

    var envVars = tl.getDelimitedInput("envVars", "\n");
    if (envVars) {
        envVars.forEach(envVar => {
            command.arg(["-e", envVar]);
        });
    }

    var containerName = tl.getInput("containerName");
    if (containerName) {
        command.arg(["--name", containerName]);
    }

    var ports = tl.getDelimitedInput("ports", "\n");
    if (ports) {
        ports.forEach(port => {
            command.arg(["-p", port]);
        });
    }

    if (!detached) {
        command.arg("--rm");
    }

    var volumes = tl.getDelimitedInput("volumes", "\n");
    if (volumes) {
        volumes.forEach(volume => {
            // If the host directory is relative, resolve it
            if (volume.indexOf("/") !== 0) {
                volume = path.join(process.cwd(), volume);
            }
            command.arg(["-v", volume]);
        });
    }

    var workDir = tl.getInput("workDir");
    if (workDir) {
        command.arg(["-w", workDir]);
    }

    var imageName = tl.getInput("imageName", true);
    command.arg(imageName, true);

    var containerCommand = tl.getInput("containerCommand");
    if (containerCommand) {
        command.arg(containerCommand);
    }

    return command.exec();
}
