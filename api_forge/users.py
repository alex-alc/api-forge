"""Service client for the user endpoints."""

from http import HTTPStatus

from pydantic import BaseModel

from api_forge.response import ApiResponse
from api_forge.service import BaseService
from api_forge.urls import UserUrl


class UserDto(BaseModel):
    """A user as returned by the API.

    Attributes:
        id: Server-assigned identifier.
        email: The user's email address.
        name: The user's display name.

    """

    id: str
    email: str
    name: str


class UsersService(BaseService):
    """Calls the user endpoints.

    Every operation takes the status code the caller expects, defaulting to the
    happy path, and returns the parsed response envelope. Positive and negative
    cases therefore share one code path.
    """

    def create_user(self, payload: object, expected_status: HTTPStatus = HTTPStatus.OK) -> ApiResponse[UserDto]:
        """Create a user from any payload.

        Returns:
            The parsed response envelope.

        """
        response = self._client.post(UserUrl.users(), json=payload)
        return self._envelope(response, UserDto, expected_status)

    def get_user(self, user_id: str, expected_status: HTTPStatus = HTTPStatus.OK) -> ApiResponse[UserDto]:
        """Fetch a single user by id.

        Returns:
            The parsed response envelope.

        """
        response = self._client.get(UserUrl.user(user_id))
        return self._envelope(response, UserDto, expected_status)

    def delete_user(self, user_id: str, expected_status: HTTPStatus = HTTPStatus.OK) -> ApiResponse[UserDto]:
        """Delete a user by id.

        Returns:
            The parsed response envelope.

        """
        response = self._client.delete(UserUrl.user(user_id))
        return self._envelope(response, UserDto, expected_status)
