"use strict";

import * as tl from "vsts-task-lib/task";
import DockerComposeConnection from "./dockerComposeConnection";
import * as sourceUtils from "./sourceUtils";
import * as imageUtils from "./dockerImageUtils";

function dockerTag(connection: DockerComposeConnection, source: string, target: string) {
    var command = connection.createCommand();
    command.arg("tag");
    command.arg(source, true);
    command.arg(target, true);
    return command.exec();
}

function addTag(promise: any, connection: DockerComposeConnection, source: string, target: string) {
    if (!promise) {
        return dockerTag(connection, source, target);
    } else {
        return promise.then(() => dockerTag(connection, source, target));
    }
}

function addOtherTags(connection: DockerComposeConnection, imageName: string): any {
    var baseImageName = imageUtils.imageNameWithoutTag(imageName);
    return (function addAdditionalTags() {
        var promise: any;
        var additionalImageTags = tl.getDelimitedInput("additionalImageTags", "\n");
        if (additionalImageTags) {
            additionalImageTags.forEach(tag => {
                promise = addTag(promise, connection, imageName, baseImageName + ":" + tag);
            });
        }
        return promise;
    })()
    .then(function addSourceTags() {
        var promise: any;
        var includeSourceTags = tl.getBoolInput("includeSourceTags");
        if (includeSourceTags) {
            sourceUtils.getSourceTags().forEach(tag => {
                promise = addTag(promise, connection, imageName, baseImageName + ":" + tag);
            });
        }
        return promise;
    })
    .then(function addLatestTag() {
        var includeLatestTag = tl.getBoolInput("includeLatestTag");
        if (baseImageName !== imageName && includeLatestTag) {
            return dockerTag(connection, imageName, baseImageName);
        }
    });
}

export function run(connection: DockerComposeConnection): any {
    var command = connection.createComposeCommand();
    command.arg("build");
    return command.exec()
    .then(() => connection.getBuiltImages())
    .then(images => {
        var promise: any;
        Object.keys(images).map(serviceName => images[serviceName]).forEach(imageName => {
            if (!promise) {
                promise = addOtherTags(connection, imageName);
            } else {
                promise = promise.then(() => addOtherTags(connection, imageName));
            }
        });
        return promise;
    });
}
