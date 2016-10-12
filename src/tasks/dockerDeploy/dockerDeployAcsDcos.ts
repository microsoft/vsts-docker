"use strict";

import * as tl from "vsts-task-lib/task";
import DockerComposeConnection from "./dockerComposeConnection";

export function run(): any {
    var connection = new DockerComposeConnection();
    return connection.open(null, tl.getInput("dockerRegistryEndpoint"))
    .then(function deploy() {
        return connection.getCombinedConfig().then(output => {
            console.log(output);
        });
    })
    .fin(function cleanup() {
        connection.close();
    });
}
