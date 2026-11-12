from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.user_profile import UserProfile


class User:
    """A person using the site, signed in or guest.

    Data only, with no methods (professor's rule). Passwords are handled
    by Supabase Auth, so there is no password field. Guests get a
    temporary User that is never saved.
    """

    def __init__(
        self,
        user_id: str,
        username: str,
        email: str,
        profile: UserProfile,
    ) -> None:
        self._user_id: str = user_id
        self._username: str = username
        self._email: str = email
        self._profile: UserProfile = profile

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @property
    def email(self) -> str:
        return self._email

    @property
    def profile(self) -> UserProfile:
        return self._profile
