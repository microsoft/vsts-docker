"use strict";

import * as tl from "vsts-task-lib/task";
import DockerComposeConnection from "./dockerComposeConnection";
import * as gitUtils from "./gitUtils";
import * as imageUtils from "./dockerImageUtils";

function dockerPush(connection: DockerComposeConnection, imageName: string, imageDigests: any, serviceName: string) {
    var command = connection.createCommand();
    command.arg("push");
    command.arg(imageName);
    if (!imageDigests) {
        return command.exec();
    } else {
        var output = "";
        command.on("stdout", data => {
            output += data;
        });
        return command.exec().then(() => {
            // Parse the output to find the repository digest
            var imageDigest = output.match(/^[^:]*: digest: ([^ ]*) size: \d*$/m)[1];
            if (imageDigest) {
                var baseImageName = imageUtils.imageNameWithoutTag(imageName);
                imageDigests[serviceName] = baseImageName + "@" + imageDigest;
            }
        });
    }
}

function pushTag(promise: any, connection: DockerComposeConnection, imageName: string, imageDigests?: any, serviceName?: string) {
    if (!promise) {
        return dockerPush(connection, imageName, imageDigests, serviceName);
    } else {
        return promise.then(() => dockerPush(connection, imageName, imageDigests, serviceName));
    }
}

function pushTags(connection: DockerComposeConnection, imageName: string, imageDigests: any, serviceName: string): any {
    var baseImageName = imageUtils.imageNameWithoutTag(imageName);
    var builtImageName = imageName + (baseImageName === imageName ? ":latest" : "");
    dockerPush(connection, builtImageName, imageDigests, serviceName)
    .then(function pushAdditionalTags() {
        var promise: any;
        var additionalImageTags = tl.getDelimitedInput("additionalImageTags", "\n");
        if (additionalImageTags) {
            additionalImageTags.forEach(tag => {
                promise = pushTag(promise, connection, baseImageName + ":" + tag);
            });
        }
        return promise;
    })()
    .then(function pushGitTags() {
        var promise: any;
        var includeGitTags = tl.getBoolInput("includeGitTags");
        if (includeGitTags) {
            var sourceVersion = tl.getVariable("Build.SourceVersion");
            if (!sourceVersion) {
                throw new Error("Cannot retrieve git tags because Build.SourceVersion is not set.");
            }
            var tags = gitUtils.tagsAt(sourceVersion);
            tags.forEach(tag => {
                promise = pushTag(promise, connection, baseImageName + ":" + tag);
            });
        }
        return promise;
    })
    .then(function pushLatestTag() {
        var includeLatestTag = tl.getBoolInput("includeLatestTag");
        if (baseImageName !== imageName && includeLatestTag) {
            return pushTag(null, connection, baseImageName + ":latest");
        }
    });
}

export function run(connection: DockerComposeConnection): any {
    return connection.getBuiltImages().then(images => {
        var promise: any;
        var imageDigests = {};
        Object.keys(images).forEach(serviceName => {
            var imageName = images[serviceName];
            if (!promise) {
                promise = pushTags(connection, imageName, imageDigests, serviceName);
            } else {
                promise = promise.then(() => pushTags(connection, imageName, imageDigests, serviceName));
            }
        });
        return promise;
    });
}
