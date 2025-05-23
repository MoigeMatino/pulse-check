from fastapi import HTTPException, status


class InvalidCredentialsException(HTTPException):
    def __init__(self, message: str = "Invalid credentials provided"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        )
