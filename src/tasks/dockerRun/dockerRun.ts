/// <reference path="../../../typings/vsts-task-lib/vsts-task-lib.d.ts" />

import tl = require("vsts-task-lib/task");
import * as docker from "./dockerCommand";

export function dockerRun(): void {
    var dockerConnectionString = tl.getInput("dockerServiceEndpoint", true);
    var registryEndpoint = tl.getInput("dockerRegistryServiceEndpoint", true);
    var imageName = tl.getInput("imageName", true);
    var containerName = tl.getInput("containerName", false);
    var envVars = tl.getDelimitedInput("envVars", "\n", false);
    var ports = tl.getDelimitedInput("ports", "\n", false);
    var additionalArgs = tl.getInput("additionalArgs", false);

    var registryConnetionDetails = tl.getEndpointAuthorization(registryEndpoint, true);

    var loginCmd = new docker.DockerCommand("login");
    loginCmd.dockerConnectionString = dockerConnectionString;
    loginCmd.registryConnetionDetails = registryConnetionDetails;
    loginCmd.execSync();

    if (containerName) {
        removeConflictingContainers(containerName, dockerConnectionString);
    }

    var cmd = new docker.DockerCommand("run");
    cmd.dockerConnectionString = dockerConnectionString;
    cmd.imageName = imageName;
    cmd.containerName = containerName;
    cmd.ports = ports;
    cmd.envVars = envVars;
    cmd.additionalArguments = additionalArgs;
    cmd.execSync();

    var logoutCmd = new docker.DockerCommand("logout");
    logoutCmd.dockerConnectionString = dockerConnectionString;
    logoutCmd.execSync();
}

function removeConflictingContainers(containerName: string, dockerConnectionString: string): void {
    var cmd = new docker.DockerCommand("removeContainerByName");
    cmd.dockerConnectionString = dockerConnectionString;
    cmd.containerName = containerName;
    cmd.execSync();
}