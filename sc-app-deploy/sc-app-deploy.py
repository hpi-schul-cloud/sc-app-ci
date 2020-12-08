#!/usr/bin/env python3

'''
This script deploys / updates manually the docker images of branches if started with the ticket-id as first parameter, 
all branches tagged "latest" for the applications "schulcloud-server", "schulcloud-client" 
and "schulcloud-nuxt-client" on the destination environment (i.a. reused hotfix or staging server) identified with the team number as second parameter.

The script is prepared to easily switch deployment to another host. The remote user "travis" must be available on the
remote host. The remote host must be prepared with docker swarm.

The remote travis user is granted access to the remote host by a private ssh-key that is registered on that host. This key is provided
in an encypted file travisssh.gpg, which is decypted using a secret provided by the GitHub CI.

If the passphrase is not set in the CI_GITHUB_TRAVISUSER_SWARMVM_KEY environment variable, we fall back to pageant. This
means you can use this script locally for development purposes, if your personal key is registered with the travis remote user.
'''

import sys
import os
import logging
import argparse

from sad_common.sad_logging import initLogging
from sad_deploy.deploy_commands import deployImages

def parseArguments():
    '''
    Parses the program arguments and returns the data parsed by argparse.
    '''
    parser = argparse.ArgumentParser(description='Deploy branch specific images of Schul-Cloud to a team assigned Docker Swarm machine.'
            , add_help=True
    )
    parser.add_argument('--version', action='version', version='1.1.0', help='Prints the script version')
    parser.add_argument('--branchprefix', type=str, choices=['feature','develop', 'release', 'master', 'hotfix'], required=True, help='Branch prefix to deploy')
    parser.add_argument('--deployhost', type=str, choices=['test', 'team'], required=True, help='Destination host for deployment')
    parser.add_argument('--teamnumber', type=int, help='the number of the team to identify the team machine')
    parser.add_argument('--jiraid', type=str, help='JIRA issue ID to identify the branch')
    parser.add_argument('--imageversion',type=str, help='JIRA issue ID to identify the branch')
    args = parser.parse_args()
    return args

def checkArgs(deployhost, branchprefix, teamnumber, jiraid, imageversion):
    imagequalifier = ''
    if deployhost == 'test':
        # Deploy to the test host, just develop is supported
        if branchprefix != 'develop':
            raise Exception("Branch prefix 'develop' only is supported with deployhost 'test'")    
    else:
        # Deploy to the team host
        if branchprefix == 'release' or branchprefix == 'master':
            if imageversion != None:
                # Version spezification has to be with loer case letters
                imagequalifier = imageversion.lower()
            else:
                raise Exception("No imageversion is specified for branchprefix '{}'".format(branchprefix))
        else:
            if jiraid != None:
                # Ticket ID will be always in uppercase letters
                imagequalifier = jiraid.upper()
            else:
                raise Exception("No jiraid is specified for branchprefix '{}'".format(branchprefix))
    return imagequalifier


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

        initLogging()
        parsedArgs = parseArguments()
        logging.info('Call arguments given: %s' % sys.argv[1:])
        deployhost   = parsedArgs['deployhost']
        branchprefix = parsedArgs['branchprefix']
        jiraid = parsedArgs['jiraid']
        imageversion = parsedArgs['imageversion']
        teamnumber = parsedArgs['teamnumber']
        imagequalifier = checkArgs(deployhost, branchprefix, teamnumber, jiraid, imageversion)
        deployImages(deployhost, branchprefix, teamnumber, imagequalifier)
    except Exception as ex:
        logging.exception(ex)
        logging.info("Deployment failed.")
        exit(1)
