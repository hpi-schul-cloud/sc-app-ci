#!/usr/bin/env python3

from logging import log
import os
import json
from textwrap import indent
import logging
import requests
class DockerRegistry:
    '''
    Docker registry access class that allows checking whether a tag exists for an repo in the initialized namespace.
    '''
    base_url = "https://hub.docker.com/v2"
    docker_namespace = ""
    auth_headers = ""

    def __init__(self, namespace):
        '''
        The namespace like 'schucloud'.
        '''
        self.docker_namespace = namespace

    def dockerRegistryLogin(self):
        login_url = f"{self.base_url}/users/login"
        logging.info("==> Logging into DockerHub")
        tok_req = requests.post(login_url, json={"username": os.environ.get("DOCKER_USERNAME"), "password": os.environ.get("DOCKER_TOKEN")})
        token = tok_req.json()["token"]
        self.auth_headers = {"Authorization": f"JWT {token}"}

    def dockerRegistryCheckTag(self, repo_name, tag):
        tags_url = f"{self.base_url}/repositories/{self.docker_namespace}/{repo_name}/tags/{tag}"
        tags_req = requests.get(tags_url, headers=self.auth_headers)
        if tags_req.status_code == 200:
            logging.info("Tag exists")
            return True
        else:
            logging.error("Tags does not exists")
            return False

if __name__ == "__main__":
    drh = DockerRegistry ("schulcloud")
    repo = "schulcloud-server"
    logging.info("==> Logging into DockerHub")
    headers = drh.dockerRegistryLogin()
    tag_exists = drh.dockerRegistryCheckTag(repo, "develop_latest")
