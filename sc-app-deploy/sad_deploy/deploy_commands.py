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

team_target_postfix = "schul-cloud.dev"
auto_target_postfix = "schul-cloud.org"
team_host_name_prefix = "hotfix"
auto_host_name = "test"
docker_namespace = "schulcloud"
sc_image_list = [
    {'image_name': "schulcloud-server", 'application_name': "server"},
    {'image_name': "schulcloud-client", 'application_name': "client"},
    {'image_name': "schulcloud-nuxt-client", 'application_name': "nuxtclient"},
    {'image_name': "schulcloud-calendar", 'application_name': "calendar" }
]

def deployImage(application: Application, host: Host, decryptedSshKeyFile: str):
    '''
    Deploys the application to the given host.
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

def deployImages(branch, args):
    logging.info("Image deployment triggered for %s" % args)
    testmode = os.environ.get("TESTMODE")
    tag_middle = ''
    if hasattr(args, "ticket_id"):
        tag_middle = '_' + args.ticket_id
    tag_to_deploy = branch + tag_middle + "_" + "latest"
    if hasattr(args, "scheduled") and args.scheduled == True and (testmode == None):
        # Deploy to the test host
        deployHost = Host(auto_host_name , auto_target_postfix)
    else:
        # Deploy to the team host
        deployHost = Host("%s%d" % (team_host_name_prefix, args.team_number) , team_target_postfix)
    logging.info("Deployment triggered for {} branch on {}".format(branch, args.team_number))
    decryptedSshKeyFile = None
    if sad_secrets.secret_helper.isPassphraseSet():
        decryptedSshKeyFile="travisssh"
        sad_secrets.secret_helper.gpgDecrypt(decryptedSshKeyFile)
    else:
        logging.info("Passphrase not set in CI_GITHUB_TRAVISUSER_SWARMVM_KEY. Using ssh identity of the currently logged in user.")
    drh = DockerRegistry(docker_namespace)
    drh.dockerRegistryLogin()
    for sc_image in sc_image_list:
        if drh.dockerRegistryCheckTag(sc_image['image_name'], tag_to_deploy):
            app = Application(sc_image['application_name'], docker_namespace + '/' + sc_image['image_name'], tag_to_deploy)
            deployImage(app, deployHost, decryptedSshKeyFile)