class BackendError(Exception):
    """Base backend integration error."""


class ModelLoadError(BackendError):
    """A saved model or preprocessing object could not be loaded."""


class ValidationError(BackendError):
    """User or model input failed validation."""


class UnknownCustomerError(BackendError):
    """The customer ID is not present in approved lookup data."""


class UnsupportedCutoffError(BackendError):
    """The requested snapshot cutoff is not approved."""
