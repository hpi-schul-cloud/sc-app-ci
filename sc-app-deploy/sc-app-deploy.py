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

from sad_common.sad_logging import initLogging
from sad_deploy.deploy_commands import deployImages
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
        if 'scheduled' in args_to_add:
            group.add_argument('--scheduled',
                                action='store_true', default=False,
                                help='script is called by automatic scheduler')

    branch_base_names = ('develop', 'master', 'release', 'hotfix', 'feature')
    subp = parser.add_subparsers(title='Branches', metavar='\n  '.join(branch_base_names))

    # develop PARSER
    develop_parser = subp.add_parser('develop',
                                      usage=(' develop '),
                                      description='Deploy latest images from develop branch')
    add_standard_args(develop_parser,
                      ('scheduled', 'team-number'))
    develop_parser.set_defaults(func=deployImages)

    # master PARSER
    master_parser = subp.add_parser('master',
                                      usage=(' master '),
                                      description='Deploy latest images from master branch')
    add_standard_args(master_parser,
                      ('team-number'))
    master_parser.set_defaults(func=deployImages)

    # release PARSER
    release_parser = subp.add_parser('release',
                                      usage=(' release '),
                                      description='Deploy latest images from release branch')
    add_standard_args(release_parser,
                      ('team-number'))
    master_parser.set_defaults(func=deployImages)
    # hotfix PARSER
    hotfix_parser = subp.add_parser('hotfix',
                                      usage=(' hotfix '),
                                      description='Deploy latest images from hotfix branch of team')
    add_standard_args(hotfix_parser,
                      ('team-number', 'ticket-id'))
    hotfix_parser.set_defaults(func=deployImages)

    # feature PARSER
    feature_parser = subp.add_parser('feature',
                                      usage=(' feature '),
                                      description='Deploy latest images from feature branch of team')
    add_standard_args(feature_parser,
                      ('team-number', 'ticket-id'))
    feature_parser.set_defaults(func=deployImages)

    args = parser.parse_args()
    return args
    

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
        exit(0)
        if hasattr(parsedArgs, 'func'):
            parsedArgs.func(parsedArgs)
        else:
            logging.info("No command given, exiting ...")
    except Exception as ex:
        logging.exception(ex)
        logging.info("Deployment failed.")
        exit(1)
