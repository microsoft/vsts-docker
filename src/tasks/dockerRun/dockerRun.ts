/// <reference path="../../../typings/vsts-task-lib/vsts-task-lib.d.ts" />

import tl = require("vsts-task-lib/task");
import * as docker from "./dockerCommand";

export function dockerRun(): void {
    var imageName = tl.getInput("imageName", true);
    var additionalArgs = tl.getInput("additionalArgs", false);

    var cmd = new docker.DockerCommand("run");
    cmd.imageName = imageName;
    cmd.additionalArguments = additionalArgs;
    cmd.execSync();
}