/// <reference path="../../../typings/vsts-task-lib/vsts-task-lib.d.ts" />

import tl = require("vsts-task-lib/task");
import * as docker from "./dockerComposeCommand";

export function dockerComposeAnyCommand(): void {
    var dockerConnectionString = tl.getInput("dockerHostEndpoint", true);
    var registryConnectionString = tl.getInput("dockerRegistryEndpoint", true);
    var dockerComposeFilePattern = tl.getInput("dockerComposeFile", true);
    var projectName = tl.getInput("projectName", false);
    var cmdToBeExecuted = tl.getInput("dockerComposeCommand", true);

    var cmd = new docker.DockerCommand(cmdToBeExecuted);
    cmd.dockerConnectionString = dockerConnectionString;
    cmd.dockerComposeFile = getDockerComposeFile(dockerComposeFilePattern);
    cmd.projectName = projectName;
    cmd.exec();
}

function getDockerComposeFile(dockerComposeFilePattern: string): string {
    var dockerComposeFile = tl.globFirst(dockerComposeFilePattern);
    return dockerComposeFile;
}