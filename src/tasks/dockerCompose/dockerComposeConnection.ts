"use strict";

import * as cp from "child_process";
import * as path from "path";
import * as tl from "vsts-task-lib/task";
import * as tr from "vsts-task-lib/toolrunner";
import * as yaml from "js-yaml";
import DockerConnection from "./dockerConnection";

export default class DockerComposeConnection extends DockerConnection {
    private dockerComposePath: string;
    private dockerComposeFile: string;
    private additionalDockerComposeFiles: string[];
    private projectName: string;

    constructor() {
        super();
        this.dockerComposePath = tl.which("docker-compose", true);
        this.dockerComposeFile = tl.globFirst(tl.getInput("dockerComposeFile", true));
        this.additionalDockerComposeFiles = tl.getDelimitedInput("additionalDockerComposeFiles", "\n");
        this.projectName = tl.getInput("projectName");
    }

    public open(hostEndpoint?: string, registryEndpoint?: string) {
        super.open(hostEndpoint, registryEndpoint);
        var envVars = tl.getDelimitedInput("dockerComposeFileArgs", "\n");
        if (envVars) {
            envVars.forEach(envVar => {
                tl.debug("setting environment variable: " + envVar);
                var tokens = envVar.split("=");
                if (tokens.length < 2) {
                    throw new Error("Environment variable '" + envVar + "' is invalid.");
                }
                process.env[tokens[0].trim()] = tokens.slice(1).join("=").trim();
            });
        }
    }

    public createComposeCommand(): tr.ToolRunner {
        var command = tl.createToolRunner(this.dockerComposePath);
        this.addAuthArgs(command);
        command.arg(["-f", this.dockerComposeFile]);
        if (this.additionalDockerComposeFiles) {
            var basePath = path.dirname(this.dockerComposeFile);
            this.additionalDockerComposeFiles.forEach(file => {
                // If the path is relative, resolve it
                if (file.indexOf("/") !== 0) {
                    file = path.join(basePath, file);
                }
                if (tl.exist(file)) {
                    command.arg(["-f", file]);
                }
            });
        }
        if (this.projectName) {
            command.arg(["-p", this.projectName]);
        }
        return command;
    }

    public getCombinedConfig(): any {
        var command = this.createComposeCommand();
        command.arg("config");
        var result = "";
        command.on("stdout", data => {
            result += data;
        });
        return command.exec({ silent: true } as any).then(() => result);
    }

    public getBuiltImages(): any {
        return this.getCombinedConfig().then(input => {
            var doc = yaml.safeLoad(input);
            var images = [];
            for (var serviceName in doc.services) {
                var service = doc.services[serviceName];
                if (service.build) {
                    var image = service.image;
                    if (!image) {
                        throw new Error("Missing image name for service '" + serviceName + "'.");
                    }
                    images.push(image);
                }
            }
            return images;
        });
    }
}
