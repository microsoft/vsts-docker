/// <reference path="../../../typings/vsts-task-lib/vsts-task-lib.d.ts" />

import tl = require("vsts-task-lib/task");
import * as docker from "./dockerComposeCommand";

export function dockerComposeAnyCommand(): void {
    var cwd = tl.getInput("cwd");
    tl.cd(cwd);

    var dockerConnectionString = tl.getInput("dockerHostEndpoint", true);
    var registryConnectionString = tl.getInput("dockerRegistryEndpoint", true);
    var dockerComposeFilePattern = tl.getInput("dockerComposeFile", true);
    var projectName = tl.getInput("projectName", false);
    var cmdToBeExecuted = tl.getInput("dockerComposeCommand", true);

    var dockerComposeFileArgs = tl.getInput("dockerComposeFileArgs", false);
    addArgumentsAsEnvironmentVariables(dockerComposeFileArgs);

    var cmd = new docker.DockerCommand(cmdToBeExecuted);
    cmd.dockerConnectionString = dockerConnectionString;
    cmd.registryConnectionString = registryConnectionString;
    cmd.dockerComposeFile = getDockerComposeFile(dockerComposeFilePattern);
    cmd.projectName = projectName;
    cmd.exec();
}

function getDockerComposeFile(dockerComposeFilePattern: string): string {
    var dockerComposeFile = tl.globFirst(dockerComposeFilePattern);
    return dockerComposeFile;
}

function addArgumentsAsEnvironmentVariables(dockerComposeFileArgs: string): void {
    if (dockerComposeFileArgs) {
        dockerComposeFileArgs = dockerComposeFileArgs.trim();
        var argsArr = dockerComposeFileArgs.split("\n");
        argsArr.forEach(function(argEntry) {
            argEntry = argEntry.trim();
            if (argEntry) {
                var argKvp = argEntry.split("=");
                if (argKvp && argKvp.length == 2) {
                    process.env[argKvp[0].trim()] = argKvp[1].trim();
                }
                else {
                    throw ("Docker compose file arguments are invalid, argument: %s. Please refer the Docker compose file help markdown.", argKvp);
                }
            }
        });
    }
}