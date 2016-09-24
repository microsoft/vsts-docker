"use strict";

import * as fs from "fs";
import * as tl from "vsts-task-lib/task";
import DockerConnection from "./dockerConnection";
import * as gitUtils from "./gitUtils";
import * as imageUtils from "./dockerImageUtils";

function dockerPush(connection: DockerConnection, imageName: string, imageDigestFile?: string) {
    var command = connection.createCommand();
    command.arg("push");
    command.arg(imageName);
    if (!imageDigestFile) {
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
                fs.writeFileSync(imageDigestFile, baseImageName + "@" + imageDigest);
            }
        });
    }
}

export function run(connection: DockerConnection): any {
    var images = [];
    var imageName = tl.getInput("imageName", true);
    var baseImageName = imageUtils.imageNameWithoutTag(imageName);
    if (baseImageName === imageName) {
        images.push(imageName + ":latest");
    } else {
        images.push(imageName);
    }
    var additionalImageTags = tl.getDelimitedInput("additionalImageTags", "\n");
    if (additionalImageTags) {
        additionalImageTags.forEach(tag => {
            images.push(baseImageName + ":" + tag);
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
            images.push(baseImageName + ":" + tag);
        });
    }
    var includeLatestTag = tl.getBoolInput("includeLatestTag");
    if (baseImageName !== imageName && includeLatestTag) {
        images.push(baseImageName + ":latest");
    }

    var imageDigestFile = tl.getPathInput("imageDigestFile");

    var promise: any;
    images.forEach(imageName => {
        if (!promise) {
            promise = dockerPush(connection, imageName, imageDigestFile);
        } else {
            promise = promise.then(() => dockerPush(connection, imageName));
        }
    });

    return promise;
}
