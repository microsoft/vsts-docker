"use strict";

import * as del from "del";
import * as fs from "fs";
import * as path from "path";
import * as tl from "vsts-task-lib/task";
import * as tr from "vsts-task-lib/toolrunner";

export default class DockerConnection {
    private dockerPath: string;
    private hostUrl: string;
    private certsDir: string;
    private caPath: string;
    private certPath: string;
    private keyPath: string;
    private loggedIn: boolean;

    constructor() {
        this.dockerPath = tl.which("docker", true);
    }

    private createBaseCommand() {
        return tl.createToolRunner(this.dockerPath);
    }

    public open(hostEndpoint?: string, registryEndpoint?: string) {
        if (hostEndpoint) {
            this.hostUrl = tl.getEndpointUrl(hostEndpoint, false);

            this.certsDir = path.join("", ".dockercerts");
            if (!fs.existsSync(this.certsDir)) {
                fs.mkdirSync(this.certsDir);
            }

            var authDetails = tl.getEndpointAuthorization(hostEndpoint, false);

            this.caPath = path.join(this.certsDir, "ca.pem");
            fs.writeFileSync(this.caPath, authDetails.parameters["cacert"]);

            this.certPath = path.join(this.certsDir, "cert.pem");
            fs.writeFileSync(this.certPath, authDetails.parameters["cert"]);

            this.keyPath = path.join(this.certsDir, "key.pem");
            fs.writeFileSync(this.keyPath, authDetails.parameters["key"]);
        }

        if (registryEndpoint) {
            var loginCmd = this.createBaseCommand();
            var registryAuth = tl.getEndpointAuthorization(registryEndpoint, true).parameters;
            if (registryAuth) {
                loginCmd.arg("login");
                loginCmd.arg(["-u", registryAuth["username"]]);
                loginCmd.arg(["-p", registryAuth["password"]]);
                loginCmd.arg(registryAuth["registry"]);
                loginCmd.execSync();
                this.loggedIn = true;
            }
        }
    }

    protected addAuthArgs(command: tr.ToolRunner) {
        if (this.hostUrl) {
            command.arg(["-H", this.hostUrl]);
            command.arg("--tls");
            command.arg("--tlscacert='" + this.caPath + "'");
            command.arg("--tlscert='" + this.certPath + "'");
            command.arg("--tlskey='" + this.keyPath + "'");
        }
    }

    public createCommand(): tr.ToolRunner {
        var command = this.createBaseCommand();
        this.addAuthArgs(command);
        return command;
    }

    public close(): void {
        if (this.loggedIn) {
            var logoutCmd = this.createBaseCommand();
            logoutCmd.arg("logout");
            logoutCmd.execSync();
        }
        if (this.certsDir && this.certsDir.trim() != "" && fs.existsSync(this.certsDir)) {
            del.sync(this.certsDir);
        }
    }
}
