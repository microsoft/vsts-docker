/// <reference path="../../../typings/vsts-task-lib/vsts-task-lib.d.ts" />

import tl = require("vsts-task-lib/task");
import * as docker from "./dockerCommand";

export function dockerPublish(): void {
    var cwd = tl.getInput("cwd");
    tl.cd(cwd);

    var dockerConnectionString = tl.getInput("dockerHostEndpoint", true);
    var registryConnectionString = tl.getInput("dockerRegistryEndpoint", true);
    var imageName = tl.getInput("imageName", true);
    var removeImageAfterPush = tl.getBoolInput("removeImageAfterPush", true);

    var publishCmd = new docker.DockerCommand("publish");
    publishCmd.dockerConnectionString = dockerConnectionString;
    publishCmd.registryConnectionString = registryConnectionString;
    publishCmd.imageName = imageName;
    publishCmd.exec();

    if (removeImageAfterPush) {
        var rmiCmd = new docker.DockerCommand("removeImage");
        rmiCmd.dockerConnectionString = dockerConnectionString;
        rmiCmd.imageName = imageName;
        rmiCmd.connectToHub = false;
        rmiCmd.execSync();
    }
}