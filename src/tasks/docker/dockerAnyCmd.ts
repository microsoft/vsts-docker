/// <reference path="../../../typings/vsts-task-lib/vsts-task-lib.d.ts" />

import tl = require("vsts-task-lib/task");
import * as docker from "./dockerCommand";

export function runCommand(): void {
    var cwd = tl.getInput("cwd");
    tl.cd(cwd);

    var dockerConnectionString = tl.getInput("dockerServiceEndpoint", true);
    var registryConnectionString = tl.getInput("dockerRegistryServiceEndpoint", true);
    var commandLine = tl.getInput("customCommand", true);

    var cmd = new docker.DockerCommand(commandLine);
    cmd.dockerConnectionString = dockerConnectionString;
    cmd.registryConnectionString = registryConnectionString;
    cmd.exec();
}