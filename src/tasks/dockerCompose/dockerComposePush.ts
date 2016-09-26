"use strict";

import * as fs from "fs";
import * as tl from "vsts-task-lib/task";
import * as yaml from "js-yaml";
import DockerComposeConnection from "./dockerComposeConnection";
import * as sourceUtils from "./sourceUtils";
import * as imageUtils from "./dockerImageUtils";

function dockerPush(connection: DockerComposeConnection, imageName: string, imageDigests?: any, serviceName?: string) {
    var command = connection.createCommand();
    command.arg("push");
    command.arg(imageName, true);

    if (!imageDigests) {
        return command.exec();
    }

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

function pushTag(promise: any, connection: DockerComposeConnection, imageName: string) {
    if (!promise) {
        return dockerPush(connection, imageName);
    } else {
        return promise.then(() => dockerPush(connection, imageName));
    }
}

function pushTags(connection: DockerComposeConnection, imageName: string, imageDigests: any, serviceName: string): any {
    var baseImageName = imageUtils.imageNameWithoutTag(imageName);
    var builtImageName = imageName + (baseImageName === imageName ? ":latest" : "");
    return dockerPush(connection, builtImageName, imageDigests, serviceName)
    .then(function pushAdditionalTags() {
        var promise: any;
        var additionalImageTags = tl.getDelimitedInput("additionalImageTags", "\n");
        if (additionalImageTags) {
            additionalImageTags.forEach(tag => {
                promise = pushTag(promise, connection, baseImageName + ":" + tag);
            });
        }
        return promise;
    })
    .then(function pushSourceTags() {
        var promise: any;
        var includeSourceTags = tl.getBoolInput("includeSourceTags");
        if (includeSourceTags) {
            sourceUtils.getSourceTags().forEach(tag => {
                promise = pushTag(promise, connection, baseImageName + ":" + tag);
            });
        }
        return promise;
    })
    .then(function pushLatestTag() {
        var includeLatestTag = tl.getBoolInput("includeLatestTag");
        if (baseImageName !== imageName && includeLatestTag) {
            return dockerPush(connection, baseImageName + ":latest");
        }
    });
}

function writeImageDigestComposeFile(imageDigests: any): void {
    var imageDigestComposeFile = tl.getPathInput("imageDigestComposeFile");
    var services = {};
    Object.keys(imageDigests).forEach(serviceName => {
        services[serviceName] = {
            image: imageDigests[serviceName]
        };
    });
    fs.writeFileSync(imageDigestComposeFile, yaml.safeDump({
        version: 2,
        services: services
    }, { lineWidth: -1 } as any));
}

export function run(connection: DockerComposeConnection): any {
    return connection.getBuiltImages()
    .then(images => {
        var promise: any;
        var imageDigests = tl.filePathSupplied("imageDigestComposeFile") ? {} : null;
        Object.keys(images).forEach(serviceName => {
            (imageName => {
                if (!promise) {
                    promise = pushTags(connection, imageName, imageDigests, serviceName);
                } else {
                    promise = promise.then(() => pushTags(connection, imageName, imageDigests, serviceName));
                }
            })(images[serviceName]);
        });
        if (imageDigests) {
            promise = promise.then(() => writeImageDigestComposeFile(imageDigests));
        }
        return promise;
    });
}
