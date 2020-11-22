from dxf import DXF

def auth(dxf, response):
    dxf.authenticate('schulclouddevops', 'jimeeCh3ei', response=response)

dxf = DXF('registry-1.docker.io', 'schulcloud/schulcloud-server', auth)

tag_exist = dxf.get_manifest('develop_latest')
print ("%b" % tag_exist)
