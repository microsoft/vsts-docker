"use strict";

export function imageNameWithoutTag(imageName: string): string {
    var endIndex = 0;
    if (imageName.indexOf(":") < imageName.indexOf("/")) {
        // Contains a registry component that includes ":", so omit
        // this part of the name from the main delimiter determination
        endIndex = imageName.indexOf("/");
    }
    endIndex = imageName.indexOf(":", endIndex);

    return endIndex < 0 ? imageName : imageName.substr(0, endIndex);
}
