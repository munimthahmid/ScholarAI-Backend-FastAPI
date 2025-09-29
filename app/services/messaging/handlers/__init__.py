"""
Compatibility package for message handlers.

This package re-exports handler modules from `handlers_dir` to
preserve historical import paths used by tests:

    app.services.messaging.handlers.extraction_handler
    app.services.messaging.handlers.summarization_handler
    app.services.messaging.handlers.structuring_handler
"""

from .extraction_handler import ExtractionMessageHandler  # noqa: F401
from .summarization_handler import SummarizationMessageHandler  # noqa: F401
from .structuring_handler import StructuringMessageHandler  # noqa: F401

