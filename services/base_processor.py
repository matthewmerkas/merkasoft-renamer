import os
import uuid
from abc import ABC, abstractmethod


class ProcessingCancelledException(Exception):
    """Exception raised when batch processing is cancelled by the user."""
    pass


class BaseProcessor(ABC):
    """
    Abstract Base Class using the Template Method pattern for batch file processors.

    Provides standard two-pass execution:
    - Pass 1: Stage original files into isolated temporary UUID paths (with automatic rollback).
    - Pass 2: Execute final transformations/renames from temporary paths.
    """

    @staticmethod
    def format_parent_path(dirname_or_path: str, filename: str = None) -> str:
        """Formats a path to 'ParentDir/filename.ext' using only the direct parent folder."""
        if filename is None:
            dirname, filename = os.path.split(dirname_or_path)
        else:
            dirname = dirname_or_path
        parent_dir = os.path.basename(dirname)
        return os.path.join(parent_dir, filename) if parent_dir else filename

    @abstractmethod
    def generate_previews(self, files: list[str], **kwargs) -> list[dict]:
        """
        Analyzes files and generates execution specs for each item.

        Each returned dictionary must contain:
          - "original_path": str
          - "input_preview": str (ParentDir/OriginalFile)
          - "output_preview": str (ParentDir/TargetFile)
          - "display_name": str (target string for UI preview)
          - "action": "rename" | "convert" | "delete" | "skip"
        """
        pass

    def preview(self, files: list[str], **kwargs) -> list[str]:
        """Unified UI preview generator. Returns target display names matching input order."""
        items = self.generate_previews(files, **kwargs)
        sorted_items = sorted(items, key=lambda x: x.get("original_index", 0))
        return [item["display_name"] for item in sorted_items]

    def process(
            self,
            files: list[str],
            progress_callback=None,
            is_cancelled=None,
            **kwargs
    ) -> list[str]:
        """Executes safe two-pass file operations with progress callbacks and rollback on cancel."""
        if not files:
            return []

        def check_cancel():
            if is_cancelled and is_cancelled():
                raise ProcessingCancelledException("Operation cancelled by user.")

        total_files = len(files)
        total_steps = total_files * 2

        def report(step: int, message: str):
            if progress_callback:
                progress_callback(step, total_steps, message)

        check_cancel()
        report(0, "Analyzing files...")

        items = self.generate_previews(files, **kwargs)

        temp_renames_done = []
        staged_items = []

        try:
            # Pass 1: Move files to unique temporary paths
            for idx, item in enumerate(items):
                check_cancel()
                orig_path = item["original_path"]

                if not os.path.exists(orig_path):
                    continue

                dir_name = os.path.dirname(orig_path)
                temp_path = os.path.join(dir_name, f".tmp_{uuid.uuid4().hex}")

                os.rename(orig_path, temp_path)
                temp_renames_done.append((orig_path, temp_path))

                staged_item = dict(item)
                staged_item["temp_path"] = temp_path
                staged_items.append(staged_item)

                report(idx + 1, f"Preparing files ({idx + 1}/{total_files})")

            # Pass 2: Execute transformation / final renaming
            final_file_paths = []
            for idx, item in enumerate(staged_items):
                check_cancel()
                step_num = total_files + idx + 1

                final_path = self.process_item(item, **kwargs)
                if final_path:
                    final_file_paths.append(final_path)

                msg = item.get("display_name", os.path.basename(final_path or ""))
                report(step_num, f"Processing {msg}")

            report(total_steps, "Processing complete")
            return final_file_paths

        except ProcessingCancelledException:
            report(0, "Cancelling & rolling back changes...")
            self._rollback(temp_renames_done)
            raise
        except Exception:
            self._rollback(temp_renames_done)
            raise

    def _rollback(self, temp_renames_done: list[tuple[str, str]]):
        """Restores temporary files back to their original paths in reverse order."""
        for orig_path, temp_path in reversed(temp_renames_done):
            if os.path.exists(temp_path) and not os.path.exists(orig_path):
                try:
                    os.rename(temp_path, orig_path)
                except Exception:
                    pass

    @abstractmethod
    def process_item(self, item: dict, **kwargs) -> str | None:
        """Executes transformation for a single staged item in Pass 2."""
        pass
