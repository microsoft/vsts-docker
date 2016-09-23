"use strict";

import * as tl from "vsts-task-lib/task";
import DockerComposeConnection from "./dockerComposeConnection";
import * as gitUtils from "./gitUtils";
import * as imageUtils from "./dockerImageUtils";

function addTag(previousPromise: any, connection: DockerComposeConnection, source: string, target: string) {
    var command = connection.createCommand();
    command.arg("tag");
    command.arg(source, true);
    command.arg(target, true);
    if (!previousPromise) {
        return command.exec();
    } else {
        return previousPromise.then(() => command.exec());
    }
}

function addOtherTags(connection: DockerComposeConnection, imageName: string): any {
    var baseImageName = imageUtils.imageNameWithoutTag(imageName);
    var additionalImageTags = tl.getDelimitedInput("additionalImageTags", "\n");
    var promise: any;

    if (additionalImageTags) {
        additionalImageTags.forEach(tag => {
            promise = addTag(promise, connection, imageName, baseImageName + ":" + tag);
        });
    }

    var includeGitTags = tl.getBoolInput("includeGitTags");
    if (includeGitTags) {
        var sourceVersion = tl.getVariable("Build.SourceVersion");
        if (!sourceVersion) {
            throw new Error("Cannot retrieve git tags because Build.SourceVersion is not set.");
        }
        var tags = gitUtils.tagsAt(sourceVersion);
        tags.forEach(tag => {
            promise = addTag(promise, connection, imageName, baseImageName + ":" + tag);
        });
    }

    var includeLatestTag = tl.getBoolInput("includeLatestTag");
    if (baseImageName !== imageName && includeLatestTag) {
        promise = addTag(promise, connection, imageName, baseImageName);
    }

    return promise;
}

export function run(connection: DockerComposeConnection): any {
    var command = connection.createComposeCommand();
    command.arg("build");
    return command.exec()
    .then(() => connection.getBuiltImages())
    .then(images => {
        var promise: any;
        images.forEach(image => {
            if (!promise) {
                promise = addOtherTags(connection, image);
            } else {
                promise = promise.then(() => addOtherTags(connection, image));
            }
        });
        return promise;
    });
}
