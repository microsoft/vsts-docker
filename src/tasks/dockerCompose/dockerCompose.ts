/// <reference path="../../../typings/vsts-task-lib/vsts-task-lib.d.ts" />

import tl = require("vsts-task-lib/task");

export function compose(): void {
    var greeting = tl.getInput("greeting");
    console.log(greeting);
}