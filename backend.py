from services.base_processor import BaseProcessor
from services.photo_processor import PhotoProcessor
from services.regex_processor import RegexProcessor


class ProcessorFactory:
    """Registry mapping strategy keys directly to processor instances."""

    _photo_processor = PhotoProcessor()
    _regex_processor = RegexProcessor()

    _processors: dict[str, BaseProcessor] = {
        "date": _photo_processor,
        "sequential": _photo_processor,
        "replace_space": _regex_processor,
        "replace_underscore": _regex_processor,
    }

    @classmethod
    def get_processor(cls, strategy_key: str):
        if strategy_key in cls._processors:
            return cls._processors[strategy_key]
        if strategy_key.startswith("replace"):
            return cls._processors["replace"]
        raise ValueError(
            f"Unknown strategy key: '{strategy_key}'. Registered strategies: {list(cls._processors.keys())}"
        )

    @classmethod
    def register_strategy(cls, strategy_key: str, processor: BaseProcessor):
        cls._processors[strategy_key.lower()] = processor


def generate_previews(strategy_key: str, files: list[str], **kwargs) -> list[str]:
    """
    Unified entry point for generating filename previews.
    Delegates to the processor registered for `strategy_key`.
    """
    if not files:
        return []
    processor = ProcessorFactory.get_processor(strategy_key)
    return processor.preview(files, strategy_key=strategy_key, **kwargs)


def execute_renaming(
        strategy_key: str,
        files: list[str],
        progress_callback=None,
        is_cancelled=None,
        **kwargs
) -> list[str]:
    """
    Unified entry point for on-disk batch execution.
    Delegates execution to the processor registered for `strategy_key`.
    """
    if not files:
        return []
    processor = ProcessorFactory.get_processor(strategy_key)
    return processor.process(
        files,
        strategy_key=strategy_key,
        progress_callback=progress_callback,
        is_cancelled=is_cancelled,
        **kwargs
    )
