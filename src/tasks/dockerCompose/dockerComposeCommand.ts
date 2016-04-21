/// <reference path="../../../typings/vsts-task-lib/vsts-task-lib.d.ts" />

import del = require("del");
import fs = require("fs");
import path = require("path");
import tl = require("vsts-task-lib/task");
import tr = require("vsts-task-lib/toolrunner");
import child = require("child_process");

export class DockerCommand {
    public commandName: string;
    public dockerComposeFile: string;
    public projectName: string;
    public additionalArguments: string;
    public dockerConnectionString: string;
    public registryConnectionString: string;
    public connectToHub: boolean;

    private dockerHostEnvVarValue: string;
    private dockerTlsVerifyEnvVarValue: number;
    private dockerCertPathEnvVarValue: string;
    private serverUrl: string;
    private certsDir: string;
    private caPath: string;
    private certPath: string;
    private keyPath: string;

    constructor(commandName: string) {
        this.commandName = commandName;
        this.connectToHub = true;
    }

    public exec(): any {
        this.writeCerts();
        this.addDockerHostAuth();

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
        var command = this.getBasicCommand(commandName);

        switch (commandName) {
            case "login":
                this.appendLoginCmdArgs(command);
                break;
            case "logout":
                this.appendLogoutCmdArgs(command);
                break;
            default:
                command.arg(commandName);
        }

        return command;
    }

    private getBasicCommand(commandName: string): tr.ToolRunner {
        if (commandName == "login" || commandName == "logout") {
            var cmdPath = tl.which("docker", true);
            tl.debug("command path: " + cmdPath);

            return tl.createToolRunner(cmdPath);
        }
        return this.getBasicDockerComposeCommand();
    }

    private getBasicDockerComposeCommand(): tr.ToolRunner {
        var cmdPath = tl.which("docker-compose", true);
        tl.debug("command path: " + cmdPath);

        var basicDockerComposeCommand = tl.createToolRunner(cmdPath);
        this.appendDockerComposeCmdArgs(basicDockerComposeCommand);

        return basicDockerComposeCommand;
    }

    private writeCerts(): void {
        this.serverUrl = tl.getEndpointUrl(this.dockerConnectionString, false);
        if (this.serverUrl.charAt(this.serverUrl.length - 1) == "/") {
            this.serverUrl = this.serverUrl.substring(0, this.serverUrl.length - 1);
        }

        tl.debug("server url: " + this.serverUrl);

        var authDetails = tl.getEndpointAuthorization(this.dockerConnectionString, false);

        this.certsDir = path.join("", ".dockercerts");
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

    private addDockerHostAuth() {
        this.dockerHostEnvVarValue = process.env["DOCKER_HOST"];
        this.dockerTlsVerifyEnvVarValue = process.env["DOCKER_TLS_VERIFY"];
        this.dockerCertPathEnvVarValue = process.env["DOCKER_CERT_PATH"];

        process.env["DOCKER_HOST"] = this.serverUrl;
        process.env["DOCKER_TLS_VERIFY"] = 1;
        process.env["DOCKER_CERT_PATH"] = this.certsDir;
    }

    private clearDockerHostAuth() {
        process.env["DOCKER_HOST"] = this.dockerHostEnvVarValue;
        process.env["DOCKER_TLS_VERIFY"] = this.dockerTlsVerifyEnvVarValue;
        process.env["DOCKER_CERT_PATH"] = this.dockerCertPathEnvVarValue;
    }

    private clearCerts() {
        if (this.certsDir && this.certsDir.trim() != "" && fs.existsSync(this.certsDir)) {
            del.sync(this.certsDir);
        }
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

    private appendDockerComposeCmdArgs(command: tr.ToolRunner) {
        command.arg("-f " + this.dockerComposeFile);
        if (this.projectName) {
            command.arg("-p " + this.projectName);
        }
    }
}