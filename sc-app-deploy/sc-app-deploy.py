#!/usr/bin/env python3

'''
This script deploys / updates the docker image tagged with "develop_latest" for the applications "schulcloud-server", "schulcloud-client" 
and "schulcloud-nuxt-client" to the staging server.

The script is prepared to easily switch deployment to another host. The remote user "travis" must be available on the
remote host. The remote host must be prepared with docker swarm.

The remote travis user is granted access to the remote host by a private ssh-key that is registered on that host. This key is provided
in an encypted file travisssh.gpg, which is decypted using a secret provided by the GitHub CI.

If the passphrase is not set in the CI_GITHUB_TRAVISUSER_SWARMVM_KEY environment variable, we fall back to pageant. This
means you can use this script locally for development purposes, if your personal key is registered with the travis remote user.
'''

import sys
import os
import subprocess
import logging
from contextlib import redirect_stdout

from sad_common.run_command import runCommand
from sad_common.sad_logging import initLogging
from sad_infra.application import Application
from sad_infra.host import Host
import sad_secrets.secret_helper

def deploy(application: Application, host: Host, decryptedSshKeyFile: str):
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

if __name__ == '__main__':
    try:
        initLogging()
        logging.info('Call arguments given: %s' % sys.argv[1:])
        exit(0)

        decryptedSshKeyFile = None
        if sad_secrets.secret_helper.isPassphraseSet():
            decryptedSshKeyFile="travisssh"
            sad_secrets.secret_helper.gpgDecrypt(decryptedSshKeyFile)
        else:
            logging.info("Passphrase not set in CI_GITHUB_TRAVISUSER_SWARMVM_KEY. Using ssh identity of the currently logged in user.")

        # Deploy to the hotfix6 host
        deployHost = Host("test", "schul-cloud.org")

        deploy(Application("server", "schulcloud/schulcloud-server", "develop_latest"), deployHost, decryptedSshKeyFile)
        deploy(Application("client", "schulcloud/schulcloud-client", "develop_latest"), deployHost, decryptedSshKeyFile)
        deploy(Application("nuxtclient", "schulcloud/schulcloud-nuxt-client", "develop_latest"), deployHost, decryptedSshKeyFile)
        deploy(Application("calendar", "schulcloud/schulcloud-calendar", "develop_latest"), deployHost, decryptedSshKeyFile)
        
        exit(0)
    except Exception as ex:
        logging.exception(ex)
        logging.info("Deployment failed.")
        exit(1)
