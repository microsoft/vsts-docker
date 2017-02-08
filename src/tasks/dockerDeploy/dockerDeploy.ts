"use strict";

import * as tl from "vsts-task-lib/task";

// Change to any specified working directory
tl.cd(tl.getInput("cwd"));

// Run the deployment based on target type
var targetType = tl.getInput("targetType", true);
/* tslint:disable:no-var-requires */
require({
    "ACS DCOS": "./dockerDeployAcsDcos",
    "Kubernetes": "./dockerDeployAcsKube"
}[targetType]).run()
/* tslint:enable:no-var-requires */
.fail(function failure(err) {
    tl.setResult(tl.TaskResult.Failed, err.message);
})
.then(function success() {
    tl.setResult(tl.TaskResult.Succeeded, "");
})
.done();
