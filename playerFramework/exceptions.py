class frameworkError(Exception):
    pass


class PlayerPathNotValid(frameworkError):
    def __init__(self, *args, **kwargs):
        pass


class UnableToWriteToIOFile(frameworkError):
    def __init__(self, *args, **kwargs):
        pass


class UndefinedKey(frameworkError):
    def __init__(self, *args, **kwargs):
        pass


class ProcessTerminatedExternally(frameworkError):
    def __init__(self, *args, **kwargs):
        pass


class InvalidTrackPath(frameworkError):
    def __init__(self, *args, **kwargs):
        pass

class songObjectNotInitialized(frameworkError):
    def __init__(self, *args, **kwargs):
        pass

class unableToReadBytes(frameworkError):
    def __init__(self, *args, **kwargs):
        pass

class invalidInternalType(frameworkError):
    def __init__(self, *args, **kwargs):
        pass