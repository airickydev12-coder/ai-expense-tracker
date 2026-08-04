from enum import Enum


class PlatformRole(str, Enum):
    """Platform-operator authority level -- who can operate the application.

    Deliberately a separate axis from household/learning-group relationships
    (e.g. a future guardian/child-learner dimension) and from age/consent
    status -- those describe *what a user is*, this describes *what a user
    can operate*. Keeping them separate avoids awkward combined roles.
    """

    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
