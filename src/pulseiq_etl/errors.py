class PipelineError(Exception):
    """Base class for failures the pipeline raises on purpose."""


class ExtractError(PipelineError):
    pass


class RejectThresholdExceeded(PipelineError):
    pass


class ValidationFailed(PipelineError):
    pass


class WarehouseError(PipelineError):
    pass
