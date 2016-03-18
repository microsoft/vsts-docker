/// <reference path="../../../typings/vsts-task-lib/vsts-task-lib.d.ts" />

import tl = require("vsts-task-lib/task");
import * as docker from "./dockerCommand";

export function dockerPublish(): void {
    var cwd = tl.getInput("cwd");
    tl.cd(cwd);

    var dockerConnectionString = tl.getInput("dockerServiceEndpoint", true);
    var registryConnectionString = tl.getInput("dockerRegistryServiceEndpoint", true);
    var imageName = tl.getInput("imageName", true);
    var removeImageAfterPublish = tl.getBoolInput("removeImageAfterPublish", true);
    var additionalArgs = tl.getInput("additionalArgs", false);

    var publishCmd = new docker.DockerCommand("publish");
    publishCmd.dockerConnectionString = dockerConnectionString;
    publishCmd.registryConnectionString = registryConnectionString;
    publishCmd.imageName = imageName;
    publishCmd.additionalArguments = additionalArgs;
    publishCmd.exec();

    if (removeImageAfterPublish) {
        var rmiCmd = new docker.DockerCommand("removeImage");
        rmiCmd.dockerConnectionString = dockerConnectionString;
        rmiCmd.imageName = imageName;
        rmiCmd.connectToHub = false;
        rmiCmd.execSync();
    }
}