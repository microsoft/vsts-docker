"use strict";

import * as tl from "vsts-task-lib/task";
import DockerConnection from "./dockerConnection";

export function run(connection: DockerConnection): any {
    var command = connection.createCommand();
    var images = [];
    command.on("stdline", line => {
        images.push(line);
    });

    command.line("images -aq");
    var result = connection.execCommand(command);

    images.forEach(element => {
        var removeImageCommand = connection.createCommand();
        removeImageCommand.line("rmi " + element);
        var thisResult = connection.execCommand(removeImageCommand);
        console.log("ThisResult: " + thisResult);
    });
    console.log("Result: " + result);
    return result;
}
