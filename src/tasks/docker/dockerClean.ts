"use strict";

import * as tl from "vsts-task-lib/task";
import DockerConnection from "./dockerConnection";

export function run(connection: DockerConnection): any {
    var command = <any>connection.createCommand();
    var images = "";

    command.line("images -aq");

    command.on("stdout", line => {
        var lineString = line + "";
        images = lineString.replace(/[\r\n]+/g, " ");
        console.log("Images: .." + images + "..");
    });

    var result = connection.execCommand(command).then(function success() {
        console.log("Then...");

        var removeImageCommand = connection.createCommand();
        removeImageCommand.line("rmi " + images);
        var res2 = removeImageCommand.execSync();
        console.log("Output for rmi " + images + ": " + res2.stdout);

        // images.forEach(element => {
            // var thisResult = connection.execCommand(removeImageCommand);
            // console.log("ThisResult: " + thisResult);
        // });

    }, function failure(err) {
        throw err;
    });

    console.log("Result: " + result);
    return result;
}
