/// <reference path="../../../typings/vsts-task-lib/vsts-task-lib.d.ts" />

import tl = require("vsts-task-lib/task");
import * as docker from "./dockerCommand";

export function dockerPublish(): void {
    var registryEndpoint = tl.getInput("dockerRegistryServiceEndpoint", true);
    var imageName = tl.getInput("imageName", true);
    var additionalArgs = tl.getInput("additionalArgs", false);

    var registryConnetionDetails = tl.getEndpointAuthorization(registryEndpoint, true);

    var loginCmd = new docker.DockerCommand("login");
    loginCmd.registryConnetionDetails = registryConnetionDetails;
    loginCmd.execSync();

    var publishCmd = new docker.DockerCommand("publish");
    publishCmd.imageName = imageName;
    publishCmd.additionalArguments = additionalArgs;
    publishCmd.execSync();

    var logoutCmd = new docker.DockerCommand("logout");
    logoutCmd.execSync();
}