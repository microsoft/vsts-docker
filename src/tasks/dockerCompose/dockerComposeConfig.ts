"use strict";

import * as fs from "fs";
import * as tl from "vsts-task-lib/task";
import DockerComposeConnection from "./dockerComposeConnection";

export function run(connection: DockerComposeConnection): any {
    var command = connection.createComposeCommand();
    command.arg("config");

    var output = "";
    command.on("stdout", data => {
        output += data;
    });

    return command.exec().then(() => {
        var baseResolveDir = tl.getPathInput("baseResolveDirectory");
        if (baseResolveDir) {
            // This just searches the output string and replaces all
            // occurrences of the base resolve directory. This isn't
            // precisely accurate but is a good enough solution.
            var replaced = output;
            do {
                output = replaced;
                replaced = output.replace(baseResolveDir, ".");
            } while (replaced !== output);
        }

        var outputDockerComposeFile = tl.getPathInput("outputDockerComposeFile", true);

        fs.writeFileSync(outputDockerComposeFile, output);
    });
}
