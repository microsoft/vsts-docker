"use strict";

import * as del from "del";
import * as fs from "fs";
import * as path from "path";
import * as tl from "vsts-task-lib/task";
import DockerComposeConnection from "./dockerComposeConnection";

var srcPath = path.join(path.dirname(module.filename), "acs-dcos");
console.log("SRC PATH: " + srcPath);
var imageName = "vsts-task-dd7c9344117944a9891b177fbb98b9a7-acs-dcos";

export function run(): any {
    var connection = new DockerComposeConnection(),
        composeFile: string;
    return connection.open(tl.getInput("dockerHostEndpoint"), tl.getInput("dockerRegistryEndpoint"))
    .then(() => connection.getCombinedConfig())
    .then(config => {
        var registryEndpoint = tl.getInput("dockerRegistryEndpoint"),
            registryHost: string,
            registryUsername: string,
            registryPassword: string;
        if (registryEndpoint) {
            var registryAuth = tl.getEndpointAuthorization(registryEndpoint, true).parameters;
            registryHost = registryAuth["registry"];
            registryUsername = registryAuth["username"];
            registryPassword = registryAuth["password"];
        }

        var endpointType = tl.getInput("acsDcosEndpointType", true),
            masterUrl = tl.getInput("acsDcosMasterUrl", endpointType === "Direct"),
            sshEndpoint = tl.getInput("acsDcosSshEndpoint", endpointType === "SSH"),
            sshHost: string,
            sshPort: string,
            sshUsername: string,
            sshPrivateKey: string,
            sshPassword: string;
        if (endpointType === "Direct") {
            sshEndpoint = null;
        } else {
            masterUrl = null;
            sshHost = tl.getEndpointDataParameter(sshEndpoint, "host", false);
            sshPort = tl.getEndpointDataParameter(sshEndpoint, "port", true) || "22";
            sshUsername = tl.getEndpointAuthorizationParameter(sshEndpoint, "username", false);
            sshPrivateKey = tl.getEndpointDataParameter(sshEndpoint, "privateKey", true);
            sshPassword = tl.getEndpointAuthorizationParameter(sshEndpoint, "password", !!sshPrivateKey);
        }

        var appGroupName = tl.getInput("acsDcosAppGroupName", true),
            appGroupQualifier = tl.getInput("acsDcosAppGroupQualifier", true),
            appGroupVersion = tl.getInput("acsDcosAppGroupVersion", true);

        var minHealthCapacity = parseInt(tl.getInput("acsDcosMinimumHealthCapacity", true));
        if (isNaN(minHealthCapacity)) {
            throw new Error("Minimum Health Capacity is not a number.");
        }

        composeFile = path.join(srcPath, ".docker-compose." + Date.now() + ".yml");
        fs.writeFileSync(composeFile, config);

        return connection.createCommand()
            .arg("build")
            .arg(["-t", imageName])
            .arg(path.join(srcPath))
            .exec()
        .then(() => {
            return connection.createCommand()
                .arg("run")
                .arg("--rm")
                .arg("-t")
                .arg(imageName)
                .arg("myscript.py")
                .arg(["--compose-file", path.basename(composeFile)])
                .arg(masterUrl ? ["--dcos-master-url", masterUrl] : [
                    "--ssh-host", sshHost,
                    "--ssh-port", sshPort,
                    "--ssh-username", sshUsername,
                    "--ssh-private-key", sshPrivateKey,
                    "--ssh-password", sshPassword
                ])
                .arg(registryHost ? [
                    "--registry-host", registryHost,
                    "--registry-username", registryUsername,
                    "--registry-password", registryPassword
                ] : [])
                .arg(["--group-name", appGroupName])
                .arg(["--group-qualifier", appGroupQualifier])
                .arg(["--group-version", appGroupVersion])
                .arg(["--minimum-health-capacity", minHealthCapacity.toString()])
                .exec();
        });
    })
    .fin(function cleanup() {
        if (composeFile && tl.exist(composeFile)) {
            del.sync(composeFile, { force: true });
        }
        connection.close();
    });
}