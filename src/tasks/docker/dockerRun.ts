/// <reference path="../../../typings/vsts-task-lib/vsts-task-lib.d.ts" />

import tl = require("vsts-task-lib/task");
import * as docker from "./dockerCommand";

export function dockerRun(): void {
    var cwd = tl.getInput("cwd");
    tl.cd(cwd);

    var dockerConnectionString = tl.getInput("dockerHostEndpoint", true);
    var registryConnectionString = tl.getInput("dockerRegistryEndpoint", true);
    var imageName = tl.getInput("imageName", true);
    var containerName = tl.getInput("containerName", false);
    var envVars = tl.getDelimitedInput("envVars", "\n", false);
    var ports = tl.getDelimitedInput("ports", "\n", false);
    var containerCommand = tl.getInput("containerCommand", false);

    var cmd = new docker.DockerCommand("run");
    cmd.dockerConnectionString = dockerConnectionString;
    cmd.registryConnectionString = registryConnectionString;
    cmd.imageName = imageName;
    cmd.containerName = containerName;
    cmd.ports = ports;
    cmd.envVars = envVars;
    cmd.containerCommand = containerCommand;
    cmd.exec();
}