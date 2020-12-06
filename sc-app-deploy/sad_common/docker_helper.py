#!/usr/bin/env python3

from logging import log
import os
import json
from textwrap import indent
import logging
import requests
class DockerRegistry:
    ''' Docker Registry Access Helper class
    Docker registry access class allows checking whether a tag exists for an repo in the initialized namespace.
    Attributes:
        - base_url: the docker registry main URL
        - docker_namespace: the organization or owner of the repositories in the registry
    Methodes:
        - dockerRegistryLogin: authenticate towards the registry
        - docker RegistryCheckTag: checks whether a tags exist for the specified repository in the initialized namespace
                 returns true if tag exists, otherwise false
    '''
    base_url = "https://hub.docker.com/v2"
    auth_headers = ""

    def __init__(self, namespace):
        """
        The namespace like 'schucloud'.
        """
        self.docker_namespace = namespace

    def dockerRegistryLogin(self):
        """
        Login in the registry specified in the base_url for the namepace used in the initialization
        Credentials are read from the environment (DOCKER_USERNAME, DOCKER_TOKEN)
        """
        login_url = f"{self.base_url}/users/login"
        logging.info("==> Logging into DockerHub")
        tok_req = requests.post(login_url, json={"username": os.environ.get("DOCKER_USERNAME"), "password": os.environ.get("DOCKER_TOKEN")})
        token = tok_req.json()["token"]
        self.auth_headers = {"Authorization": f"JWT {token}"}

    def dockerRegistryCheckTag(self, repo_name, alias):
        """
        Checks whether a tag (alias) exist for the specified repository (repo_name) in the initialized namespace
                 returns true if tag exists, otherwise false
        """
        tags_url = f"{self.base_url}/repositories/{self.docker_namespace}/{repo_name}/tags/{alias}"
        tags_req = requests.get(tags_url, headers=self.auth_headers)
        if tags_req.status_code == 200:
            logging.info("Tag '{}' exists in repository: '{}'".format(alias, repo_name))
            return True
        else:
            logging.warning("Tags '{}' does not exists in repository: '{}'".format(alias, repo_name))
            return False

if __name__ == "__main__":
    """
    Main function can be invoked to test the class
    """
    drh = DockerRegistry ("schulcloud")
    repo = "schulcloud-server"
    logging.info("==> Logging into DockerHub")
    drh.dockerRegistryLogin()
    tag_exists = drh.dockerRegistryCheckTag(repo, "develop_latest")
