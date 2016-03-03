# vsts-docker
This is the source code repository of Docker extension for Visual Studio Team Services. This extension contains VSTS build tasks to work with Docker.

## Working with this repo

### Implementation details
* Task and corresponding tests are in TypeScript.
* Lint is the static analysis tool.
* Istanbul is the code coverage tool.
* Mocha is the testing framework.
* Chai, Sinon and Sinon-Chai are used for assertions.

### Commands
(assuming node is installed)

Once:
```bash
$ npm install
$ npm install gulp -g
$ npm install tfx-cli -g
```

Build:
```bash
$ gulp build
```

Test:
```bash
$ gulp test
```

Package (vsix will be generated at _build/package):
```bash
$ gulp package
```