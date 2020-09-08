import logging
import os
from sad_common.run_command import runCommand

def gpgDecrypt(decryptToFile: str):
    '''
    Decrypts the private key file using the passphrase from the CI_GITHUB_TRAVISUSER_SWARMVM_KEY environment variable.
    By convention an input file that matches the output file with the ".gpg" extension must exist.
    '''
    encryptedFile='%s.gpg' % decryptToFile
    logging.info("Decrypting  '%s' to '%s'." % (encryptedFile, decryptToFile))
    passphrase= os.environ['CI_GITHUB_TRAVISUSER_SWARMVM_KEY']
    decryptCommand=['gpg', '--quiet', '--batch', '--yes', '--decrypt', '--passphrase=%s' % passphrase, '--output', decryptToFile, encryptedFile]
    runCommand(decryptCommand)
    runCommand(['chmod', '600', decryptToFile])

def isPassphraseSet():
    '''
    Returns, if the passphrase is set in the CI_GITHUB_TRAVISUSER_SWARMVM_KEY environment variable. If
    this is not the case, the decryption will not succeed.
    '''
    if os.environ.get('CI_GITHUB_TRAVISUSER_SWARMVM_KEY') == None:
        return False
    else:
        return True
