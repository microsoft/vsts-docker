"use strict";

import * as tl from "vsts-task-lib/task";
import DockerComposeConnection from "./dockerComposeConnection";

export function run(connection: DockerComposeConnection): any {
    var command = connection.createComposeCommand();
    command.arg(tl.getInput("dockerComposeCommand", true));
    return command.exec();
}
