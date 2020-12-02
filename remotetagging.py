from logging import INFO
import os
from os import name
import sys
import logging
from dxf import DXF
import argparse

def parseArguments():
    '''
    Parses the program arguments and returns the data parsed by argparse.
    '''
    parser = argparse.ArgumentParser(description='Add or delete tags on Docker Hub.')

    parser.add_argument('--version', action='version', version='1.0.0')
    parser.add_argument('--repo', dest='repo', required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--add', dest='add_tag', action='store_true')
    group.add_argument('--del', dest='del_tag', action='store_true')
    parser.add_argument('--tag', dest='exist_tag', required=True)
    parser.add_argument('--alias', dest='new_tag')
    args = parser.parse_args()
    return args

def query_yes_no(question, default="no"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def auth(dxf, response):
    dxf.authenticate(os.environ.get("DOCKER_USERNAME"), os.environ.get("DOCKER_TOKEN"), response=response)


if __name__ == '__main__':
    try:
        logging.basicConfig(level=logging.INFO)
        parsedArgs = parseArguments()
        logging.info('Call arguments given: %s' % sys.argv[1:])
        dxf = DXF('registry-1.docker.io', 'schulcloud/{}'.format(parsedArgs.repo), auth)
        if hasattr(parsedArgs, 'add_tag') and parsedArgs.add_tag == True:
            logging.info("Adding tag '{}' to '{}' in repository '{}'".format(parsedArgs.new_tag, parsedArgs.exist_tag, parsedArgs.repo))
            manifest = dxf.get_manifest('{}'.format(parsedArgs.exist_tag))
            dxf.set_manifest('{}'.format(parsedArgs.new_tag), manifest)
        else:
            logging.info("Deleting tag '{}' in repository '{}'".format(parsedArgs.exist_tag, parsedArgs.repo))
            suretodel = query_yes_no("Are you sure to delete tag '{}' from '{}'".format(parsedArgs.exist_tag, parsedArgs.repo))
            if suretodel:
                dxf.del_alias(parsedArgs.exist_tag)
        exit(0)

    except Exception as ex:
        logging.exception(ex)
        exit(1)


