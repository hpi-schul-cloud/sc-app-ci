#!/usr/bin/env python3
# At least Python 3.5 for subprocess.run
import sys
import os
import subprocess
import logging
import time
from pathlib import Path
from contextlib import redirect_stdout

from sad_common.run_command import runCommand
from sad_infra.application import Application
from sad_infra.host import Host

def initLogging():
    '''
    Initializes the logger.
    '''
    logdir = './log'
    Path(logdir).mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    applicationName = 'sc-app-deploy'
    logFilename = '%s/%s_%s.log' % (logdir, timestamp, applicationName)
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s", "%Y-%m-%d %H:%M:%S")

    # The logger
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)
    
    # File handler
    fileHandler = logging.FileHandler(logFilename)
    fileHandler.setFormatter(logFormatter)
    fileHandler.setLevel(logging.DEBUG)
    rootLogger.addHandler(fileHandler)

    # Console handler
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    consoleHandler.setLevel(logging.INFO)
    rootLogger.addHandler(consoleHandler)
    
    logging.info('Logging initialized')

def deploy(application: Application, host: Host):
    '''
    Deploys the application to the given host.
    '''
    logging.info("Deploying '%s'..." % application.getSwarmServicename(host))

    remoteUser = "travis"

    sshCommand=['ssh']

    # Disable known hosts checking.
    sshOptions=['-o', 'StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null']

    # TODO: Get ssh access to the deployment target system
    #openssl aes-256-cbc -K $encrypted_bce910623bb2_key -iv $encrypted_bce910623bb2_iv -in travis_rsa.enc -out .build/travis_rsa -d
    #chmod 600 .build/travis_rsa
    sshIdentity=['-i', '.build/%s_rsa' % remoteUser]

    # remote = <build user>@<hostname>.schul-cloud.dev
    sshRemote=['%s@%s' % (remoteUser, host.getFQDN())]

    # The remote command parameters.
    # image = <imagename>:<imagetag> = <repository name>:<tag>
    # service name = <hostname>_<applicationname short>. See 'docker service ls'
    sshRemoteCommandParameters=[application.getImage(), application.getSwarmServicename(host)]

    command = sshCommand + sshOptions + sshIdentity + sshRemote + sshRemoteCommandParameters
    logging.info("Running command: '%s'" % ' '.join(command))

    # /usr/bin/docker service update --force --image schulcloud/schulcloud-server:develop_latest hotfix6_server
    # Deploy develop_latest of client, nuxt and server to "test.schul-cloud.org"
    #	ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i .build/travis_rsa travis@staging.schul-cloud.org schulcloud/schulcloud-server:$DOCKERTAG staging_server
    #	ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i .build/travis_rsa travis@hotfix$1.schul-cloud.dev schulcloud/schulcloud-server:$DOCKERTAG hotfix$1_server
    #subprocess.run(command, check=True)
    #subprocess.run('ls', check=True)
    # TODO: use 'command' instead of 'ls' dummy.
    #runCommand(command)
    runCommand(['ls'])
    logging.info("Deployment '%s' complete." % application.getSwarmServicename(host))

    # TODO: Inform RocketChat

if __name__ == '__main__':
    try:
        initLogging()
        logging.info('Call arguments given: %s' % sys.argv[1:])

        # Deploy to the hotfix6 host
        hotfix6Host = Host("hotfix6", "schul-cloud.dev")
        deploy(Application("server", "schulcloud/schulcloud-server", "develop_latest"), hotfix6Host)
        deploy(Application("client", "schulcloud/schulcloud-client", "develop_latest"), hotfix6Host)
        deploy(Application("nuxtclient", "schulcloud/schulcloud-nuxt-client", "develop_latest"), hotfix6Host)
        
        #deploy(Application("server", "schulcloud/schulcloud-server", "develop_latest"), Host("test", "schul-cloud.org"))
        
        exit(0)
    except Exception as ex:
        logging.exception(ex)
        logging.info("Deployment failed.")
        exit(1)
