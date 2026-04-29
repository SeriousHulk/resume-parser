class ResumeParserError(Exception):
    """Base class for expected resume parser failures."""


class FileValidationError(ResumeParserError):
    """Raised when an uploaded file is missing, too large, or unsupported."""


class DocumentConversionError(ResumeParserError):
    """Raised when MarkItDown cannot produce usable Markdown."""


class OcrConfigurationError(ResumeParserError):
    """Raised when OCR is required but Tesseract is not configured."""


class OcrProcessingError(ResumeParserError):
    """Raised when OCR runs but produces no usable text."""


class ModelConfigurationError(ResumeParserError):
    """Raised when a requested provider or model is unavailable."""


class ResumeExtractionError(ResumeParserError):
    """Raised when the model response cannot be converted to ResumeData."""
