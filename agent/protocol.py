from uuid import UUID


class UploadMessage(object):
    firmware_id: UUID

    def __init__(self, firmware_id: UUID):
        self.firmware_id = firmware_id
