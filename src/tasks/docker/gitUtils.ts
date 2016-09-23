"use strict";

import * as cp from "child_process";
import * as tl from "vsts-task-lib/task";

export function tagsAt(commit: string) {
    var git = tl.which("git", true);
    var args = ["tag", "--points-at", commit];
    var cwd = tl.getVariable("Build.Repository.LocalPath");
    console.log("[command]" + git + " " + args.join(" "));
    var result = (cp.execFileSync(git, args, {
        encoding: "utf8",
        cwd: cwd
    }) as string).trim();
    console.log(result);
    return result.split("\n");
}