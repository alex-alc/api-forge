"""Endpoint paths, one class per resource."""


class UserUrl:
    """Paths for the user resource."""

    _USERS = "/users"
    _USER = "/users/{user_id}"

    @staticmethod
    def users() -> str:
        """Build the path for the user collection.

        Returns:
            The collection path.

        """
        return UserUrl._USERS

    @staticmethod
    def user(user_id: str) -> str:
        """Build the path for a single user.

        Returns:
            The path addressing the given user.

        """
        return UserUrl._USER.format(user_id=user_id)
