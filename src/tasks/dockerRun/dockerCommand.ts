/// <reference path="../../../typings/vsts-task-lib/vsts-task-lib.d.ts" />

import tl = require("vsts-task-lib/task");
import tr = require("vsts-task-lib/toolrunner");

export class DockerCommand {
    public commandName: string;
    public imageName: string;

    constructor(commandName: string) {
        this.commandName = commandName;
    }

    public execSync() {
        var cmd = this.getCommand();
        cmd.execSync(<tr.IExecOptions> { failOnStdErr: true });
    }

    private getCommand(): tr.ToolRunner {
        var dockerPath = tl.which("docker", true);
        tl.debug("docker path: " + dockerPath);
        // TODO: what if docker is not found

        var dockerToolRunner = tl.createToolRunner(dockerPath);

        // TODO: throw if commandName is not set

        if (this.commandName == "run") {
            dockerToolRunner.arg("run");

            // TODO: throw if imageName is not set
            dockerToolRunner.arg(this.imageName);
        }
        else {
            dockerToolRunner.arg(this.commandName);
        }

        return dockerToolRunner;
    }
}