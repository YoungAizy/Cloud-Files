

# --- Custom Exception Classes ---
class FileTooLargeError(Exception):
    def __init__(self, message: str = "File size is too large"):
        self.message = message
        super().__init__(self.message)

class UnsafeURLError(Exception):
    def __init__(self, message: str = "Unsafe Url detected"):
        self.message = message
        super().__init__(self.message)

class GoogleUploadError(Exception):
    def __init__(self, message: str = "Google Drive upload failed"):
        self.message = message
        super().__init__(self.message)