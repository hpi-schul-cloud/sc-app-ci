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
import argparse
from contextlib import redirect_stdout

from sad_common.run_command import runCommand
from sad_common.sad_logging import initLogging
from sad_infra.application import Application
from sad_infra.host import Host
import sad_secrets.secret_helper

def parseArguments():
    '''
    Parses the program arguments and returns the data parsed by argparse.
    '''
    parser = argparse.ArgumentParser(description='Deploy branch specific images of Schul-Cloud to a team assigned Docker Swarm machine.')

    parser.add_argument('--version', action='version', version='1.0.0')
    def add_standard_args(parser, args_to_add):
        # each command has a slightly different use of these arguments,
        # therefore just add the ones specified in `args_to_add`.
        if 'team-number' in args_to_add:
            parser.add_argument('team-number',
                                type=int,
                                help='the number of the team to identify the team machine')
        if 'ticket-id' in args_to_add:
            parser.add_argument('ticket-id',
                            type=str,
                            help='JIRA issue ID to identify the branch')

    branch_base_names = ('develop', 'master', 'hotfix', 'feature')
    subp = parser.add_subparsers(title='Branches', metavar='\n  '.join(branch_base_names))

    # develop PARSER
    develop_parser = subp.add_parser('develop',
                                      usage=(' develop '),
                                      description='Deploy latest images from develop branch')
    develop_parser.set_defaults(func=deployDevelop)

    # master PARSER
    master_parser = subp.add_parser('master',
                                      usage=(' master '),
                                      description='Deploy latest images from master branch')
    add_standard_args(master_parser,
                      ('team-number'))
    master_parser.set_defaults(func=deployMaster)

    # hotfix PARSER
    hotfix_parser = subp.add_parser('hotfix',
                                      usage=(' hotfix '),
                                      description='Deploy latest images from hotfix branch of team')
    add_standard_args(hotfix_parser,
                      ('team-number', 'ticket-id'))
    hotfix_parser.set_defaults(func=deployHotFix)

    # feature PARSER
    feature_parser = subp.add_parser('feature',
                                      usage=(' feature '),
                                      description='Deploy latest images from feature branch of team')
    add_standard_args(feature_parser,
                      ('team-number', 'ticket-id'))
    feature_parser.set_defaults(func=deployFeature)
    parser.add_argument('--debug', '-d', dest='debug', action='store_true', default=False),
    parser.add_argument("-w", "--whatif", action='store_true', help = "If set no deploy operations are executed.")

    args = parser.parse_args()
    return args
    
def logWhatIfHeader():
    logging.info("====================================================")
    logging.info("====================================================")
    logging.info("====================================================")
    logging.info("====== Simulation only! No backup performed. =======")
    logging.info("====================================================")
    logging.info("====================================================")
    logging.info("====================================================")

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

def deployMaster():
    pass

def deployHotFix():
    pass

def deployFeature():
    pass


def deployDevelop(application: Application, host: Host, decrytedSshKeyFile: str):
        decryptedSshKeyFile = None
        if sad_secrets.secret_helper.isPassphraseSet():
            decryptedSshKeyFile="travisssh"
            sad_secrets.secret_helper.gpgDecrypt(decryptedSshKeyFile)
        else:
            logging.info("Passphrase not set in CI_GITHUB_TRAVISUSER_SWARMVM_KEY. Using ssh identity of the currently logged in user.")

        # Deploy to the test host
        deployHost = Host("hotfix6", "schul-cloud.dev")

        deploy(Application("server", "schulcloud/schulcloud-server", "develop_latest"), deployHost, decryptedSshKeyFile)
        deploy(Application("client", "schulcloud/schulcloud-client", "develop_latest"), deployHost, decryptedSshKeyFile)
        deploy(Application("nuxtclient", "schulcloud/schulcloud-nuxt-client", "develop_latest"), deployHost, decryptedSshKeyFile)
        deploy(Application("calendar", "schulcloud/schulcloud-calendar", "develop_latest"), deployHost, decryptedSshKeyFile)

if __name__ == '__main__':
    try:
        if sys.version_info[0] < 3 or sys.version_info[1] < 6:
            print("This script requires Python version 3.6")
            print("Python version")
            print (sys.version)
            print("Version info.")
            print (sys.version_info)          
            print(os.environ['PATH'])
            sys.exit(1)

        parsedArgs = parseArguments()
        initLogging()
        if hasattr(parsedArgs, 'debug') and parsedArgs.debug:
            rootLogger = logging.getLogger()
            rootLogger.setLevel(logging.DEBUG)
        logging.debug('Call arguments given: %s' % sys.argv[1:])
        exit(0)
        if hasattr(args, 'func'):
            args.func(args)
        else:
            logger.info("No command given, exiting ...")
        exit(0)
    except Exception as ex:
        logging.exception(ex)
        logging.info("Deployment failed.")
        exit(1)
