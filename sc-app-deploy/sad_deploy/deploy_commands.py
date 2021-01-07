""" Deploy module
This module handles the deployment of tags identified by the branch, 
a Ticket-ID or version number to the destination team machine.
The application which will be deployed are specified in the dictionary sc_image_list. 
Adding more applications just need to be added in that dictionary.
"""
from logging import exception
import sys
import os
import subprocess
import logging
from contextlib import redirect_stdout
import sad_common
from sad_common.docker_helper import DockerRegistry

from sad_common.run_command import runCommand
from sad_infra.application import Application
from sad_infra.host import Host
import sad_secrets.secret_helper

# DNS parts for team machines
team_target_postfix = "schul-cloud.dev"
team_host_name_prefix = "hotfix"
# DNS parts for scheduled deployment
auto_target_postfix = "schul-cloud.org"
auto_host_name = "test"
# Works currently for images of the specified namespace only
docker_namespace = "schulcloud"
# Dictionary of the applications which will be tried to deploy
sc_image_list = [
    {'image_name': "schulcloud-server", 'application_name': "server"},
    {'image_name': "schulcloud-client", 'application_name': "client"},
    {'image_name': "schulcloud-nuxt-client", 'application_name': "nuxtclient"},
    {'image_name': "schulcloud-nuxt-storybook", 'application_name': "storybook"},
    {'image_name': "schulcloud-nuxt-vuepress", 'application_name': "vuepress"},
    {'image_name': "schulcloud-calendar", 'application_name': "calendar" },
    {'image_name': "antivirus_check_service.scanfile", 'application_name': "scanfile"},
    {'image_name': "antivirus_check_service.webserver", 'application_name': "webserver"}
]

def deployImage(application: Application, host: Host, decryptedSshKeyFile: str):
    '''
    Deploys a single application to the given host.
    '''
    logging.info("Deploying '%s'..." % application.getSwarmServicename(host))

    remoteUser = "travis"

    sshCommand=['ssh']

    # Disable known hosts checking.
    sshOptions=['-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null']

    if decryptedSshKeyFile != None:
        # Use provided ssh key
        sshIdentity=['-i', decryptedSshKeyFile]
    else:
        # Try pageant
        sshIdentity=[]

    # remote = <build user>@<hostname>.schul-cloud.dev
    sshRemote=['%s@%s' % (remoteUser, host.getFQDN())]

    # The remote command parameters.
    # image = <imagename>:<imagetag> = <repository name>:<tag>
    # service name = <hostname>_<applicationname short>. See 'docker service ls'
    sshRemoteCommandParameters=[application.getImage(), application.getSwarmServicename(host)]

    command = sshCommand + sshOptions + sshIdentity + sshRemote + sshRemoteCommandParameters
    logging.info("Running command: '%s'" % ' '.join(command))

    # Run docker service update
    # Example call: ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i travisssh travis@hotfix6.schul-cloud.dev schulcloud/schulcloud-server:develop_latest hotfix6_server
    # Example execution: /usr/bin/docker service update --force --image schulcloud/schulcloud-server:develop_latest hotfix6_server
    runCommand(command)
    #runCommand(['ls'])
    logging.info("Deployment '%s' complete." % application.getSwarmServicename(host))

    # TODO: Inform RocketChat

def deployImages(deployhost, branch, teamnumber, imagequalifier):
    """ deployImages
    The function loops of the sc_image_list dictionary 
    and call deployImage if the tag for the application images exist on the docker registry
    """
    logging.info("Image deployment triggered on {} for {} of team {}".format(branch, imagequalifier, teamnumber))
    testmode = os.environ.get("TESTMODE")
    tag_middle = ''
    # Branch prefix and "latest" qualifier must be lowercase
    tag_qualifier = "latest".lower()

    if deployhost == 'test' and (testmode == None):
        # Deploy to the test host
        deployHost = Host(auto_host_name , auto_target_postfix)
    else:
        if imagequalifier != '':
            tag_middle = '_' + imagequalifier
        deployHost = Host("%s%d" % (team_host_name_prefix, teamnumber) , team_target_postfix)
    tag_to_deploy = branch + tag_middle + "_" + tag_qualifier
    decryptedSshKeyFile = None
    if sad_secrets.secret_helper.isPassphraseSet():
        decryptedSshKeyFile="travisssh"
        sad_secrets.secret_helper.gpgDecrypt(decryptedSshKeyFile)
    else:
        logging.info("Passphrase not set in CI_GITHUB_TRAVISUSER_SWARMVM_KEY. Using ssh identity of the currently logged in user.")
    drh = DockerRegistry(docker_namespace)
    drh.dockerRegistryLogin()
    no_images_deployed = 0
    for sc_image in sc_image_list:
        if drh.dockerRegistryCheckTag(sc_image['image_name'], tag_to_deploy):
            app = Application(sc_image['application_name'], docker_namespace + '/' + sc_image['image_name'], tag_to_deploy)
            deployImage(app, deployHost, decryptedSshKeyFile)
            no_images_deployed += 1
    if no_images_deployed == 0:
        # Without checking that at least on tag has been deploy the abort of the calling job would not be possible
        raise Exception("No images deployed, tag '{}' may not exist for any image on the branch prefix '{}'".format(tag_to_deploy, branch))