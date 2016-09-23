"use strict";

import * as fs from "fs";
import * as tl from "vsts-task-lib/task";
import DockerConnection from "./dockerConnection";
import * as imageUtils from "./dockerImageUtils";

function dockerPush(connection: DockerConnection, image: string, imageDigestFile?: string) {
    var command = connection.createCommand();
    command.arg("push");
    command.arg(image);
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
                fs.writeFileSync(imageDigestFile, imageUtils.imageNameWithoutTag(image) + "@" + imageDigest);
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
    // TODO: include Git tags
    var includeLatestTag = tl.getBoolInput("includeLatestTag");
    if (baseImageName !== imageName && includeLatestTag) {
        images.push(baseImageName + ":latest");
    }

    var imageDigestFile = tl.getPathInput("imageDigestFile");

    var promise: any;
    images.forEach(image => {
        if (!promise) {
            promise = dockerPush(connection, image, imageDigestFile);
        } else {
            promise = promise.then(() => dockerPush(connection, image));
        }
    });

    return promise;
}
