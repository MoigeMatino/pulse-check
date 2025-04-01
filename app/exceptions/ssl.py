class InvalidURLException(Exception):
    """Custom exception raised when an invalid URL is provided"""

    def __init__(self, message: str):
        super().__init__(message)
