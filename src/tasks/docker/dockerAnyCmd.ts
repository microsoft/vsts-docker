"use strict";

import * as tl from "vsts-task-lib/task";
import DockerConnection from "./dockerConnection";

export function run(connection: DockerConnection): any {
    var cmd = connection.createCommand();
    cmd.arg(tl.getInput("customCommand", true));
    return cmd.exec();
}
