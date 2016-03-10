/// <reference path="../../../typings/vsts-task-lib/vsts-task-lib.d.ts" />

import tl = require("vsts-task-lib/task");
import tr = require("vsts-task-lib/toolrunner");

export class DockerCommand {
    public commandName: string;
    public dockerFile: string;
    public context: string;
    public imageName: string;
    public additionalArguments: string;

    constructor(commandName: string) {
        this.commandName = commandName;
    }

    public execSync() {
        var command = this.getBasicCommand();

        switch (this.commandName) {
            case "run":
                this.appendRunCmdArgs(command);
                break;
            case "build":
                this.appendBuildCmdArgs(command);
                break;
            default:
                command.arg(this.commandName);
        }

        if (this.additionalArguments) {
           command.arg(this.additionalArguments);
        }

        command.execSync();
    }

    private getBasicCommand(): tr.ToolRunner {
        var dockerPath = tl.which("docker", true);
        tl.debug("docker path: " + dockerPath);
        // TODO: what if docker is not found

        var basicDockerCommand = tl.createToolRunner(dockerPath);

        return basicDockerCommand;
    }

    private appendRunCmdArgs(command: tr.ToolRunner) {
        command.arg("run");
        command.arg(this.imageName);
        // TODO: hanle imageName not set
    }

    private appendBuildCmdArgs(command: tr.ToolRunner) {
        command.arg("build");
        command.arg("-t " + this.imageName);
        command.arg("-f " + this.dockerFile);
        command.arg(this.context);
    }
}