/// <reference path="../../../typings/vsts-task-lib/vsts-task-lib.d.ts" />

import tl = require("vsts-task-lib/task");
import * as docker from "./dockerComposeCommand";

export function dockerComposeAnyCommand(): void {
    var dockerConnectionString = tl.getInput("dockerServiceEndpoint", true);
    var registryConnectionString = tl.getInput("dockerRegistryServiceEndpoint", true);
    var dockerComposeFile = tl.getInput("dockerComposeFile", true);
    var cmdToBeExecuted = tl.getInput("dockerComposeCommand", true);

    var cmd = new docker.DockerCommand(cmdToBeExecuted);
    cmd.dockerConnectionString = dockerConnectionString;
    cmd.dockerComposeFile = dockerComposeFile;
    cmd.exec();
}