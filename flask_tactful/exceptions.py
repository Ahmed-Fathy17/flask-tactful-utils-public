""" HTTP exceptions fired by Tactful services
each exception contains an HTTP Status code and error message

The exceptions are handled by Flask and are returned to the user with the status code
"""
from http import HTTPStatus

from werkzeug.exceptions import HTTPException


class SchemaValidationException(HTTPException):
    code = 400
    description = "Request is missing required fields"


class ItemAlreadyExistsException(HTTPException):
    code = 409
    description = "Item is already exists"


class ItemNotExistsException(HTTPException):
    code = 404
    description = "Item with given id doesn't exists"


class ItemDuplicateFieldException(HTTPException):
    code = 409
    description = "Item with given field value already exists"


class RoleRequiredException(HTTPException):
    code = 403
    description = "Accessing item by other is forbidden"


class UnauthorizedException(HTTPException):
    code = 401
    description = "Invalid username or password"


class LimitExceededException(HTTPException):
    code = 402
    description = "Payment Plan is Limit Excceeded. for exstra limit payment required."


class ProfileLanguageException(HTTPException):
    code = 400
    description = "Given language is not supported by this Profile."


class FileSizeException(HTTPException):
    code = 400
    description = "File size is greater than allowed limit."


class FileTypeException(HTTPException):
    code = 400
    description = "File type is not supported."


class UnAuthenticatedException(HTTPException):
    code = 401
    description = "User is not authenticated. - Missing x-api-key header"


class InvalidTokenException(HTTPException):
    code = HTTPStatus.UNPROCESSABLE_ENTITY  # 422
    description = "User is not authenticated. - Token invalid"


class UnAuthorizedRoleException(HTTPException):
    code = 401
    description = "User is not authorized. - Role is not allowed"


class SignatureValidationException(HTTPException):
    code = 422
    description = "Signature validation failed"


class UserNotFoundException(HTTPException):
    code = 404
    description = "User does not exist"


class InternalServerErrorException(HTTPException):
    code = 500
    description = "Internal server error"


class PreConditionFailedException(HTTPException):
    code = 412
    description = "Precondition requested data FAILED!"


class ExternalPreconditionFailedException(HTTPException):
    """ This for the precondition requested from the third-party """
    code = 412
    description = PreConditionFailedException.description
