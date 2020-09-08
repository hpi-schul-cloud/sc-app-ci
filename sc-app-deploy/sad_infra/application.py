from sad_infra.host import Host

class Application:
    '''
    Dataclass that stores the Docker info and the short application name of an application.
    '''

    imagename = None
    # 'schulcloud/schulcloud-server'

    imagetag = None
    # 'develop_latest'

    applicationname_short = None
    # 'server'

    def __init__(self, applicationname_short, imagename, imagetag):
        '''
        The applicationname_short like 'server'.
        The imagename like 'schulcloud/schulcloud-server'.
        The imagetag like 'develop_latest'.
        '''
        self.applicationname_short = applicationname_short
        self.imagename = imagename
        self.imagetag = imagetag

    def getSwarmServicename(self, host: Host):
        '''
        The servicename is constructed from two parts: <hostname>_<applicationname_short>
        E.g.: "hotfix6_server".
        '''
        servicename = "%s_%s" % (host.hostname, self.applicationname_short)
        return  servicename

    def getImage(self):
        '''
        Returns the full image name with tag like 'schulcloud/schulcloud-server:develop_latest'.
        '''
        image = "%s:%s" % (self.imagename, self.imagetag)
        return image

