from tempfile import SpooledTemporaryFile


max_size = 1024 * 1024 * 2 # 2MB


class UploadedFile(object):
    def __init__(self, name, filename, mime_type, *args, **kwargs):
        self.name = name
        self.filename = filename
        self.file = SpooledTemporaryFile(max_size=max_size)
        self.mime_type = mime_type
