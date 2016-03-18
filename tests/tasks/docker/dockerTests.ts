/// <reference path="../../../typings/tsd.d.ts" />
/// <reference path="../../../typings/vsts-task-lib/vsts-task-lib.d.ts" />

import * as dockerRun from "../../../src/tasks/docker/dockerRun";

import chai = require("chai");
import sinon = require("sinon");
import sinonChai = require("sinon-chai");
import tl = require("vsts-task-lib/task");

chai.should();
chai.use(sinonChai);

describe("dockerRun.dockerRun", (): void => {
    var sandbox;
    var getInputStub;

    beforeEach((): void => {
        sandbox = sinon.sandbox.create();
        getInputStub = sandbox.stub(tl, "getInput");
    });

    afterEach((): void => {
        sandbox.restore();
    });

    it("should pass", (): void => {
        dockerRun.dockerRun();
    });
});