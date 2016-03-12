/// <reference path="../../../typings/vsts-task-lib/vsts-task-lib.d.ts" />

import fs = require("fs");
import path = require("path");
import tl = require("vsts-task-lib/task");
import tr = require("vsts-task-lib/toolrunner");

export class DockerCommand {
    public commandName: string;
    public dockerFile: string;
    public context: string;
    public imageName: string;
    public additionalArguments: string;
    public dockerConnectionString: string;
    public registryConnetionDetails: tl.EndpointAuthorization;

    constructor(commandName: string) {
        this.commandName = commandName;
    }

    public execSync() {
        var command = this.getBasicCommand();

        this.appendAuth(command);

        switch (this.commandName) {
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

    private appendAuth(command: tr.ToolRunner) {
        var serverUrl = tl.getEndpointUrl(this.dockerConnectionString, false);
        var authDetails = tl.getEndpointAuthorization(this.dockerConnectionString, false);

        var dir = path.join("", "certs");
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir);
        }

        var caPath = path.join(dir, "ca.pem");
        fs.writeFileSync(caPath, authDetails.parameters["username"]);

        var certPath = path.join(dir, "cert.pem");
        fs.writeFileSync(certPath, authDetails.parameters["password"]);

        var keyPath = path.join(dir, "key.pem");
        fs.writeFileSync(keyPath, authDetails.parameters["key"]);

        command.arg("--tls");
        command.arg("--tlscacert='" + caPath + "'");
        command.arg("--tlscert='" + certPath + "'");
        command.arg("--tlskey='" + keyPath + "'");
        command.arg("-H");
        command.arg(serverUrl);
    }

    private appendRunCmdArgs(command: tr.ToolRunner) {
        command.arg("run");
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
        command.arg("login");
        command.arg("-e " + this.registryConnetionDetails.parameters["email"]);
        command.arg("-u " + this.registryConnetionDetails.parameters["username"]);
        command.arg("-p " + this.registryConnetionDetails.parameters["password"]);
    }

    private appendLogoutCmdArgs(command: tr.ToolRunner) {
        command.arg("logout");
    }
}