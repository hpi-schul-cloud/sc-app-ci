#!/usr/bin/env python3

from logging import log
import os
import json
from textwrap import indent
import logging
import requests

base_url = "https://hub.docker.com/v2"
docker_namespace = "schulcloud"

def dockerRegistryLogin():
    login_url = f"{base_url}/users/login"
    logging.info("==> Logging into DockerHub")
    tok_req = requests.post(login_url, json={"username": os.environ.get("DOCKER_USERNAME"), "password": os.environ.get("DOCKER_TOKEN")})
    token = tok_req.json()["token"]
    headers = {"Authorization": f"JWT {token}"}
    return headers

def dockerRegistryCheckTag(headers, repo_name, tag):
    tags_url = f"{base_url}/repositories/{docker_namespace}/{repo_name}/tags/{tag}"
    tags_req = requests.get(tags_url, headers=headers)
    if tags_req.status_code == 200:
        logging.info("Tag exists")
        return True
    else:
        logging.error("Tags does not exists")
        return False

if __name__ == "__main__":
    repo = "schulcloud-server"
    logging.info("==> Logging into DockerHub")
    headers = dockerRegistryLogin()
    tag_exists = dockerRegistryCheckTag(headers, repo, "develop_latest")
