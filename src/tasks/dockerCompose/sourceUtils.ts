"use strict";

import * as tl from "vsts-task-lib/task";
import * as gitUtils from "./gitUtils";

export function getSourceTags(): string[] {
    var tags: string[];

    var sourceProvider = tl.getVariable("Build.Repository.Provider");

    var sourceVersion = tl.getVariable("Build.SourceVersion");
    if (!sourceVersion) {
        throw new Error("Cannot retrieve source tags because Build.SourceVersion is not set.");
    }

    switch (sourceProvider) {
        case "TfsVersionControl":
            // TODO: support TFVC labels
            break;
        case "TfsGit":
        case "GitHub":
        case "Git":
            tags = gitUtils.tagsAt(sourceVersion);
            break;
        case "Subversion":
            // TODO: support subversion tags
            break;
    }

    return tags || [];
}
