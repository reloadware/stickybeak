from collections import OrderedDict
from stickybeak.vendored.pip._vendor.toml import TomlEncoder
from stickybeak.vendored.pip._vendor.toml import TomlDecoder


class TomlOrderedDecoder(TomlDecoder):

    def __init__(self):
        super(self.__class__, self).__init__(_dict=OrderedDict)


class TomlOrderedEncoder(TomlEncoder):

    def __init__(self):
        super(self.__class__, self).__init__(_dict=OrderedDict)
