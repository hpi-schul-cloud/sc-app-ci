'''
Provides the standard exception class.
'''
class SadException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
