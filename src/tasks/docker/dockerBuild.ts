"use strict";

import * as path from "path";
import * as tl from "vsts-task-lib/task";
import DockerConnection from "./dockerConnection";
import * as sourceUtils from "./sourceUtils";
import * as imageUtils from "./dockerImageUtils";

export function run(connection: DockerConnection): any {
    var command = connection.createCommand();
    command.arg("build");

    var dockerFile = tl.globFirst(tl.getInput("dockerFile", true));
    command.arg(["-f", dockerFile]);

    tl.getDelimitedInput("buildArguments", "\n").forEach(buildArgument => {
        command.arg(["--build-arg", buildArgument]);
    });

    var imageName = tl.getInput("imageName", true);
    command.arg(["-t", imageName]);

    var baseImageName = imageUtils.imageNameWithoutTag(imageName);

    tl.getDelimitedInput("additionalImageTags", "\n").forEach(tag => {
        command.arg(["-t", baseImageName + ":" + tag]);
    });

    var includeSourceTags = tl.getBoolInput("includeSourceTags");
    if (includeSourceTags) {
        sourceUtils.getSourceTags().forEach(tag => {
            command.arg(["-t", baseImageName + ":" + tag]);
        });
    }

    var includeLatestTag = tl.getBoolInput("includeLatestTag");
    if (baseImageName !== imageName && includeLatestTag) {
        command.arg(["-t", baseImageName]);
    }

    var context: string;
    if (!tl.filePathSupplied("context")) {
        context = path.dirname(dockerFile);
    } else {
        context = tl.getPathInput("buildContext");
    }
    command.arg(context);

    return command.exec();
}
