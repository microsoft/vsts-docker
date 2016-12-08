"use strict";

import * as del from "del";
import * as fs from "fs";
import * as path from "path";
import * as tl from "vsts-task-lib/task";
import DockerComposeConnection from "./dockerComposeConnection";

var srcPath = path.join(path.dirname(module.filename), "acs-dcos");
var imageName = "vsts-task-dd7c9344117944a9891b177fbb98b9a7-acs-dcos";

function normalizeAppId(id: string) {
    // Marathon allows lowercase letters, digits, hyphens, "." and ".."
    // We don't handle the complexity of normalizing to the exact regex
    return id.toLowerCase().replace(/[^/0-9a-z-\.]/g, "");
}

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

        var appGroupName = normalizeAppId(tl.getInput("acsDcosAppGroupName", true)),
            appGroupQualifier = normalizeAppId(tl.getInput("acsDcosAppGroupQualifier", true)),
            appGroupVersion = normalizeAppId(tl.getInput("acsDcosAppGroupVersion", true));

        var minHealthCapacity = parseInt(tl.getInput("acsDcosMinimumHealthCapacity", true));
        if (isNaN(minHealthCapacity)) {
            throw new Error("Minimum Health Capacity is not a number.");
        }

        var verbose = tl.getVariable("System.Debug");

        composeFile = path.join(srcPath, ".docker-compose." + Date.now() + ".yml");
        fs.writeFileSync(composeFile, config);

        return connection.execCommand(connection.createCommand()
            .arg("build")
            .arg(["-f", path.join(srcPath, "Dockerfile.task")])
            .arg(["-t", imageName])
            .arg(srcPath))
        .then(() => connection.createCommand()
            .arg("run")
            .arg("--rm")
            .arg(imageName)
            .arg("createmarathon.py")
            .arg(["--compose-file", path.basename(composeFile)])
            .arg(masterUrl ? ["--dcos-master-url", masterUrl] : [
                "--acs-host", sshHost,
                "--acs-port", sshPort,
                "--acs-username", sshUsername,
                "--acs-private-key", sshPrivateKey,
                "--acs-password", sshPassword
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
            .arg(verbose ? ["--verbose"] : [])
            .exec());
    })
    .fin(function cleanup() {
        if (composeFile && tl.exist(composeFile)) {
            del.sync(composeFile, { force: true });
        }
        connection.close();
    });
}
