import os
import sys
from dxf import DXF

def auth(dxf, response):
    dxf.authenticate(os.environ.get("DOCKER_USERNAME"), os.environ.get("DOCKER_TOKEN"), response=response)

dxf = DXF('registry-1.docker.io', 'schulcloud/{}'.format(sys.argv[1]), auth)

#tag_exist = dxf.list_aliases('schulcloud/schulcloud-server')
manifest = dxf.get_manifest('{}'.format(sys.argv[2]))
dxf.set_manifest('{}'.format(sys.argv[3]), manifest)
#digest = dxf.get_manifest('{}'.format(sys.argv[2]))
#dxf.set_alias('feature_ops-1559_latest', digest)
print ("%b" % tag_exist)