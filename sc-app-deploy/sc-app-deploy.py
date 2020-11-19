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
    parser = argparse.ArgumentParser(description='Run S3 instance backups for the HPI Schul-Cloud application.')

    parser.add_argument('--version', action='version', version='1.0.0')
    parser.add_argument("-sc", "--showconfig", action='store_true', help = "Prints out the configuration that will be used, before any other action.")
    parser.add_argument("-d", "--dailyincrement", action='store_true', help = "Creates a backup of the files that were uploaded during the last day.")
    parser.add_argument("-s", "--syncfull", action='store_true', help = "Synchronizes the full backup of the configured instances, if scheduled for today.")
    parser.add_argument("-va", "--validate", action='store_true', help = "Validates the existing syncfull backup. The validation checks the number of objects and the size of the buckets.")
    parser.add_argument("-i", "--instance", action='append', dest = 'instances_to_backup', help = "Limits the scope to the specified instance. Add the name of an instance to backup as argument.")
    parser.add_argument("-c", "--configuration", help = "Name of a yaml configuration file to use for the backup. The configuration file contains the definition of the available instances and other static configuration data.", default="s3b_test.yaml")
    parser.add_argument("-f", "--force", action='store_true', help = "Force. If -s is specified forces a syncfull backup, even if it is not scheduled for today.")
    parser.add_argument("-w", "--whatif", action='store_true', help = "If set no write operations are executed. rclone operations are executed with --dryrun.")
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

        initLogging()
        logging.info('Call arguments given: %s' % sys.argv[1:])
        parsedArgs = parseArguments()
        exit(0)
        if parsedArgs.whatif:
            logWhatIfHeader()
        if parsedArgs.showconfig:
            logging.info("Configuration: %s" % s3_backup_config)
        elif parsedArgs.dailyincrement or parsedArgs.syncfull or parsedArgs.validate:
            # Evaluate which instances shall be backed up.
            instances_to_backup = []
            if parsedArgs.instances_to_backup:
                # Check that all instances the user has specified are in the current configuration.
                logging.debug('Run for specific instances: %s' % parsedArgs.instances_to_backup)
                for instance_name_to_check in parsedArgs.instances_to_backup:
                    instance_found = False
                    for current_instance_name, current_instance in s3_backup_config.instances.items():
                        if current_instance.instancename == instance_name_to_check:
                            instance_found = True
                            break
                    if not instance_found:
                        raise S3bException('Instance "%s" not found in configuration.' % instance_name_to_check)
                # All instance names given by the command line are valid
                instances_to_backup = parsedArgs.instances_to_backup
            else:
                # Use all instances in the current configuration.
                logging.debug('Run for all instances.')
                for current_instance_name, current_instance in s3_backup_config.instances.items():
                    instances_to_backup.append(current_instance.instancename)
            logging.info('The following instances are in scope: %s' % instances_to_backup)
            # Validate the s3-backup config.
            rclone.validate_configuration(s3_backup_config)
            # Run the backup or validation.
            rclone.run_backup(s3_backup_config, instances_to_backup, parsedArgs.dailyincrement, parsedArgs.syncfull, parsedArgs.validate, parsedArgs.force, parsedArgs.whatif)
        else:
            logging.info("No action specified. Use a parameter like -d, -s or -sc to define an action.")
        
        exit(0)
    except Exception as ex:
        logging.exception(ex)
        logging.info("Deployment failed.")
        exit(1)
