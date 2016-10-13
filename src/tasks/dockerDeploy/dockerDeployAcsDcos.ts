"use strict";

import * as crypto from "crypto";
import * as tl from "vsts-task-lib/task";
import * as yaml from "js-yaml";
import DockerComposeConnection from "./dockerComposeConnection";

function getApplicationGroupId(): string {
    var name = tl.getInput("acsDcosAppGroupName", true);
    var qualifier = tl.getInput("acsDcosAppGroupQualifier", true);
    var version = tl.getInput("acsDcosAppGroupVersion", true);

    qualifier = crypto.createHash("sha1").update(qualifier).digest("hex").substring(0, 8);

    return "/" + name + "." + qualifier + "." + version;
}

function buildApplicationGroup(compose: any): any {
    var group = {
        id: getApplicationGroupId(),
        apps: []
    };

    for (var serviceName in compose.services || {}) {
        var service = compose.services[serviceName];
        var app = {
            id: serviceName,
            cpus: 0.01,
            mem: 128,
            instances: 1,
            container: {
                type: "DOCKER",
                docker: {
                    image: service.image
                }
            }
        };
        // cap_add, cap_drop: not supported
        // command: not supported
        // cgroup_parent: not supported
        // container_name: not supported
        // cpu_quota: not supported
        // cpu_shares: not supported
        // cpuset: not supported
        // devices: not supported
        // depends_on: not supported
        // domainname: not supported
        // dns: not supported
        // dns_search: not supported
        // hostname: not supported
        // ipc: not supported
        // tmpfs: not supported
        // entrypoint: not supported
        // environment: not supported
        // expose: not supported
        // external_links: not supported
        // extra_hosts: not supported
        // image: not supported
        // labels: not supported
        // links: not supported
        // logging: not supported
        // mac_address: not supported
        // mem_limit: not supported
        // memswap_limit: not supported
        // network_mode: not supported
        // networks: not supported
        // pid: not supported
        // privileged: not supported
        // ports: not supported
        // read_only: not supported
        // restart: not supported
        // security_opt: not supported
        // shm_size: not supported
        // stdin_open: not supported
        // stop_signal: not supported
        // tty: not supported
        // ulimits: not supported
        // user: not supported
        // volumes: not supported
        // volumes_from: not supported
        // working_dir: not supported
        group.apps.push(app);
    }

    for (var volumeName in compose.volumes || {}) {
        // not supported
    }

    for (var networkName in compose.networks || {}) {
        // not supported
    }

    return group;
}

export function run(): any {
    var connection = new DockerComposeConnection();
    return connection.open(null, tl.getInput("dockerRegistryEndpoint"))
    .then(() => connection.getCombinedConfig())
    .then(output => yaml.safeLoad(output))
    .then(buildApplicationGroup)
    .then(group => console.log(JSON.stringify(group, null, 2)))
    .fin(function cleanup() {
        connection.close();
    });
}
