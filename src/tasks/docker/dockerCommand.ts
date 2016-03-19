/// <reference path="../../../typings/vsts-task-lib/vsts-task-lib.d.ts" />

import del = require("del");
import fs = require("fs");
import path = require("path");
import tl = require("vsts-task-lib/task");
import tr = require("vsts-task-lib/toolrunner");

export class DockerCommand {
    public commandName: string;
    public dockerFile: string;
    public context: string;
    public imageName: string;
    public containerName: string;
    public ports: string[];
    public envVars: string[];
    public additionalArguments: string;
    public dockerConnectionString: string;
    public registryConnectionString: string;
    public connectToHub: boolean;

    constructor(commandName: string) {
        this.commandName = commandName;
        this.connectToHub = true;
    }

    public execSync(): tr.IExecResult {
        this.writeCerts();

        if (this.connectToHub) {
            var loginCmd = this.getCommand("login");
            loginCmd.execSync();
        }

        var command = this.getCommand(this.commandName);
        var result = command.execSync();

        if (this.connectToHub) {
            var logoutCmd = this.getCommand("logout");
            logoutCmd.execSync();
        }

        this.clearCerts();

        return result;
    }

    public exec(): any {
        this.writeCerts();

        if (this.connectToHub) {
            var loginCmd = this.getCommand("login");
            loginCmd.execSync();
        }

        var command = this.getCommand(this.commandName);
        return command.exec()
        .then(function(code) {
            tl.setResult(tl.TaskResult.Succeeded, "");
        })
        .fail(function(err: string) {
            tl.setResult(tl.TaskResult.Failed, err);
        })
        .fin(function() {
            if (this.connectToHub) {
                var logoutCmd = this.getCommand("logout");
                logoutCmd.execSync();
            }
            this.clearCerts();
        });
    }

    private getCommand(commandName: string): tr.ToolRunner {
        var command = this.getBasicCommand();

        this.appendAuthArgs(command);
        switch (commandName) {
            case "run":
                this.appendRunCmdArgs(command);
                break;
            case "build":
                this.appendBuildCmdArgs(command);
                break;
            case "publish":
                this.appendPublishCmdArgs(command);
                break;
            case "login":
                this.appendLoginCmdArgs(command);
                break;
            case "logout":
                this.appendLogoutCmdArgs(command);
                break;
            case "removeImage":
                this.appendRemoveImageCmdArgs(command);
                break;
            case "removeContainerByName":
                this.appendRemoveContainerByNameCmdArgs(command);
                break;
            default:
                command.arg(commandName);
        }

        if (this.additionalArguments) {
           command.arg(this.additionalArguments);
        }

        return command;
    }

    private getBasicCommand(): tr.ToolRunner {
        var dockerPath = tl.which("docker", true);
        tl.debug("docker path: " + dockerPath);

        var basicDockerCommand = tl.createToolRunner(dockerPath);

        return basicDockerCommand;
    }

    private serverUrl: string;
    private certsDir: string;
    private caPath: string;
    private certPath: string;
    private keyPath: string;

    private writeCerts(): void {
        this.serverUrl = tl.getEndpointUrl(this.dockerConnectionString, false);
        var authDetails = tl.getEndpointAuthorization(this.dockerConnectionString, false);

        this.certsDir = path.join("", "certs");
        if (!fs.existsSync(this.certsDir)) {
            fs.mkdirSync(this.certsDir);
        }

        this.caPath = path.join(this.certsDir, "ca.pem");
        fs.writeFileSync(this.caPath, authDetails.parameters["cacert"]);

        this.certPath = path.join(this.certsDir, "cert.pem");
        fs.writeFileSync(this.certPath, authDetails.parameters["cert"]);

        this.keyPath = path.join(this.certsDir, "key.pem");
        fs.writeFileSync(this.keyPath, authDetails.parameters["key"]);
    }

    private appendAuthArgs(command: tr.ToolRunner) {
        command.arg("--tls");
        command.arg("--tlscacert='" + this.caPath + "'");
        command.arg("--tlscert='" + this.certPath + "'");
        command.arg("--tlskey='" + this.keyPath + "'");
        command.arg("-H " + this.serverUrl);
    }

    private clearCerts() {
        if (this.certsDir && this.certsDir.trim() != "" && fs.existsSync(this.certsDir)) {
            del.sync(this.certsDir);
        }
    }

    private appendRunCmdArgs(command: tr.ToolRunner) {
        command.arg("run");
        if (this.ports) {
            this.ports.forEach(function (v, i) {
                command.arg("-p " + v);
            });
        }
        if (this.envVars) {
            this.envVars.forEach(function (v, i) {
                command.arg("-e " + v);
            });
        }
        if (this.containerName) {
            command.arg("--name " + this.containerName);
        }
        command.arg(this.imageName);
    }

    private appendBuildCmdArgs(command: tr.ToolRunner) {
        command.arg("build");
        command.arg("-t " + this.imageName);
        command.arg("-f " + this.dockerFile);
        command.arg(this.context);
    }

    private appendPublishCmdArgs(command: tr.ToolRunner) {
        command.arg("push");
        command.arg(this.imageName);
    }

    private appendLoginCmdArgs(command: tr.ToolRunner) {
        var registryConnetionDetails = tl.getEndpointAuthorization(this.registryConnectionString, true);
        command.arg("login");
        command.arg("-e " + registryConnetionDetails.parameters["email"]);
        command.arg("-u " + registryConnetionDetails.parameters["username"]);
        command.arg("-p " + registryConnetionDetails.parameters["password"]);
    }

    private appendLogoutCmdArgs(command: tr.ToolRunner) {
        command.arg("logout");
    }

    private appendRemoveImageCmdArgs(command: tr.ToolRunner) {
        command.arg("rmi --force " + this.imageName);
    }

    private appendRemoveContainerByNameCmdArgs(command: tr.ToolRunner) {
        command.arg("rm --force " + this.containerName);
    }
}