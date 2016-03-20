var child = require("child_process");
var tl = require("vsts-task-lib/task");
var fs = require("fs");
var path = require("path");

///var cp = child.spawn("docker-compose", ["-f", "E:\\temp\\temp\\agent\\_work\\1\\s\\HelloWorld\\Docker\\docker-compose.release.yml", "-p", "Docker", "down", "--rmi",  "all"], {shell: true});
///var cp = child.spawn("docker-compose", ["-f", "E:\\temp\\temp\\agent\\_work\\1\\s\\HelloWorld\\Docker\\docker-compose.release.yml", "-p", "Docker", "up",  "-d"], {shell: true});


function exec(serverUrl, authDetails, dockerComposeCommand)
{
    ///Configure
    this.certsDir = path.join("", "certs");
    if (!fs.existsSync(this.certsDir)) {
        fs.mkdirSync(this.certsDir);
    }

    this.caPath = path.join(this.certsDir, "ca.pem");
    fs.writeFileSync(this.caPath, authDetails.parameters["username"]);

    this.certPath = path.join(this.certsDir, "cert.pem");
    fs.writeFileSync(this.certPath, authDetails.parameters["password"]);

    this.keyPath = path.join(this.certsDir, "key.pem");
    fs.writeFileSync(this.keyPath, authDetails.parameters["key"]);

    process.env["DOCKER_HOST"] = this.serverUrl;
    process.env["DOCKER_TLS_VERIFY"] = 1;
    process.env["DOCKER_CERT_PATH"] = this.certsDir;

    
    ///Execute
    var cp = child.spawn("docker-compose", ["-f", "E:\\temp\\temp\\agent\\_work\\1\\s\\HelloWorld\\Docker\\docker-compose.release.yml", "-p", "Docker", "up",  "-d"], {shell: true});
    cp.stdout.on("data", function (data) {
        tl.debug("%s", data)
    });
    cp.stderr.on("data", function (data) {
        tl.debug("%s", data);
    });
    cp.on("exit", function (code, signal) {
        tl.debug("rc:" + code);
    });
}

var serverUrl = process.argv[2];
var authDetails = process.argv[3];
var dockerComposeCommand = process.argv[4];

tl.debug("Server Url is: " + serverUrl)
tl.debug("dockerComposeCommand is: " + dockerComposeCommand)
tl.debug("authDetails is: " + authDetails)


exec(serverUrl, authDetails, dockerComposeCommand)

/*
var dockerComposePath = tl.which("docker-compose", true);
var cmd = tl.createToolRunner(dockerComposePath);
cmd.toolPath = "docker-compose.exe"
cmd.args = new Array<string>[];


var dockerComposeCmd = process.argv[1];
cmd.toolPath = dockerComposeCmd.

process.argv.forEach(function (val, index, array) {
    if(index != 0) {
        cmd.toolPath = 
        console.log(index + ': ' + val);
    }
});
*/