from PySide6.QtCore import QThread, Signal
from backend import execute_renaming


class RenameWorker(QThread):
    progress = Signal(int, int, str)
    finished = Signal(list)
    cancelled = Signal()
    error = Signal(str)

    def __init__(self, files, strategy_key, **kwargs):
        super().__init__()
        self.files = files
        self.strategy_key = strategy_key
        self.kwargs = kwargs
        self._is_cancelled = False

    def request_cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            results = execute_renaming(
                strategy_key=self.strategy_key,
                files=self.files,
                progress_callback=self.progress.emit,
                is_cancelled=lambda: self._is_cancelled,
                **self.kwargs
            )
            if self._is_cancelled:
                self.cancelled.emit()
            else:
                self.finished.emit(results)
        except Exception as e:
            if self._is_cancelled:
                self.cancelled.emit()
            else:
                self.error.emit(str(e))
