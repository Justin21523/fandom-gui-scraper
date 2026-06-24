"""MediaWiki client exceptions."""


class MediaWikiAPIError(RuntimeError):
    """Raised when the MediaWiki Action API returns an error."""


class InvalidWikiTargetError(ValueError):
    """Raised when a wiki URL or api.php endpoint cannot be normalized."""


class RobotsDeniedError(PermissionError):
    """Raised when robots.txt disallows the API request."""


class AccessRestrictedError(PermissionError):
    """Raised when a response indicates access restrictions."""
