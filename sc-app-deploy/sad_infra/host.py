class Host:
    hostname = None
    domain = None

    def __init__(self, hostname, domain):
        '''
        hostname like 'hotfix6'
        domain like 'schul-cloud.dev'
        '''
        self.hostname = hostname
        self.domain = domain

    def getFQDN(self):
        '''
        Returns the fully qualified domain name like 'hotfix6.schul-cloud.dev'
        '''
        fqdn = "%s.%s" % (self.hostname, self.domain)
        return fqdn
