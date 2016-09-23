"use strict";

import * as tl from "vsts-task-lib/task";
import DockerConnection from "./dockerConnection";

export function run(connection: DockerConnection): any {
    var command = connection.createCommand();
    command.arg(tl.getInput("customCommand", true));
    return command.exec();
}
