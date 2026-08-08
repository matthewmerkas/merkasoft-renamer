import os

from PySide6.QtCore import (
    QObject,
    QUrl,
    Slot,
    Signal,
    Property,
    QThreadPool,
)

from backend import generate_previews
from models.file_list import FileListModel
from workers.add_files import AddFilesWorker
from workers.rename import RenameWorker


def format_parent_path(path_str: str) -> str:
    """Formats a full path into 'ParentFolder/filename.ext'."""
    if not path_str:
        return ""
    clean_path = os.path.normpath(path_str)
    parent_dir = os.path.basename(os.path.dirname(clean_path))
    file_name = os.path.basename(clean_path)
    if parent_dir:
        return f"{parent_dir}/{file_name}"
    return file_name


class FileModel(QObject):
    filesChanged = Signal()
    previewFilesChanged = Signal()
    selectedIndicesChanged = Signal()

    isProcessingChanged = Signal()
    progressValueChanged = Signal()
    statusMessageChanged = Signal()

    searchPatternChanged = Signal()
    replacePatternChanged = Signal()
    useRegexChanged = Signal()

    _addFilesCompleted = Signal(dict)

    def __init__(self):
        super().__init__()
        self._raw_input_paths = []
        self._input_model = FileListModel(self)
        self._output_model = FileListModel(self)
        self._selected_indices = set()
        self._anchor_index = -1

        self._thread_pool = QThreadPool.globalInstance()
        self._addFilesCompleted.connect(self._on_add_files_completed)

        self._strategies = [
            {"id": "date", "label": "Date"},
            {"id": "sequential", "label": "Sequential"},
            {"id": "replace_space", "label": "Replace ( )"},
            {"id": "replace_underscore", "label": "Replace (_)"},
        ]
        self._current_strategy = self._strategies[0]["id"]

        self._utc_offset_str = "+10:00"
        self._start_num = 1
        self._jpeg_quality = 90

        self._search_pattern = "\\d{4} \\d{2}$"
        self._replace_pattern = ""
        self._use_regex = True

        self._is_processing = False
        self._progress_value = 0.0
        self._status_message = ""
        self._worker_thread = None

    @Property(QObject, constant=True)
    def inputListModel(self):
        return self._input_model

    @Property(QObject, constant=True)
    def outputListModel(self):
        return self._output_model

    @Property(bool, notify=isProcessingChanged)
    def isProcessing(self):
        return self._is_processing

    @Property(float, notify=progressValueChanged)
    def progressValue(self):
        return self._progress_value

    @Property(str, notify=statusMessageChanged)
    def statusMessage(self):
        return self._status_message

    @Property(str, notify=searchPatternChanged)
    def searchPattern(self):
        return self._search_pattern

    @Property(str, notify=replacePatternChanged)
    def replacePattern(self):
        return self._replace_pattern

    @Property(bool, notify=useRegexChanged)
    def useRegex(self):
        return self._use_regex

    def getFiles(self):
        return self._raw_input_paths

    def getSelectedIndices(self):
        return list(self._selected_indices)

    def getStrategies(self):
        return self._strategies

    files = Property("QVariantList", getFiles, notify=filesChanged)
    selectedIndices = Property("QVariantList", getSelectedIndices, notify=selectedIndicesChanged)
    strategies = Property("QVariantList", getStrategies, constant=True)

    def _update_previews(self):
        """Generates new preview names via backend dispatcher."""
        files = self._raw_input_paths
        if not files:
            self._output_model.clear()
            self.previewFilesChanged.emit()
            return

        previews = generate_previews(
            strategy_key=self._current_strategy,
            files=files,
            utc_offset_str=self._utc_offset_str,
            start_num=self._start_num,
            search_pattern=self._search_pattern,
            replace_pattern=self._replace_pattern,
            use_regex=self._use_regex
        )

        self._output_model.set_items(previews)
        self.previewFilesChanged.emit()

    @Slot(QUrl)
    @Slot(str)
    def addFile(self, url):
        self.addFiles([url])

    @Slot(list)
    @Slot(str)
    def addFiles(self, urls):
        worker = AddFilesWorker(
            raw_input=urls,
            existing_paths=self._raw_input_paths,
            strategy_key=self._current_strategy,
            utc_offset_str=self._utc_offset_str,
            start_num=self._start_num,
            search_pattern=self._search_pattern,
            replace_pattern=self._replace_pattern,
            use_regex=self._use_regex,
            callback_signal=self._addFilesCompleted
        )
        self._thread_pool.start(worker)

    @Slot(dict)
    def _on_add_files_completed(self, result: dict):
        new_unique_paths = result["new_unique_paths"]
        new_previews = result["new_previews"]

        if new_unique_paths:
            self._raw_input_paths.extend(new_unique_paths)
            formatted_inputs = [format_parent_path(p) for p in new_unique_paths]
            self._input_model.add_items(formatted_inputs)
            self._output_model.add_items(new_previews)
            self.filesChanged.emit()

    @Slot()
    def deleteSelected(self):
        if not self._selected_indices:
            return

        indices_to_remove = sorted(self._selected_indices)

        # 1. Update the raw internal path list
        self._raw_input_paths = [
            path for i, path in enumerate(self._raw_input_paths)
            if i not in self._selected_indices
        ]

        # 2. Granularly remove rows from the Qt input model without resetting it
        self._input_model.remove_indices(indices_to_remove)

        # 3. Clear selections
        self._selected_indices.clear()
        self._anchor_index = -1
        self._input_model.set_selected_indices(self._selected_indices)

        # 4. Refresh output preview list
        self._update_previews()

        self.filesChanged.emit()
        self.selectedIndicesChanged.emit()

    @Slot()
    def clearFiles(self):
        self._raw_input_paths.clear()
        self._input_model.clear()
        self._output_model.clear()
        self._selected_indices.clear()
        self._anchor_index = -1
        self._input_model.set_selected_indices(self._selected_indices)
        self.filesChanged.emit()
        self.selectedIndicesChanged.emit()
        self.previewFilesChanged.emit()

    @Slot(str)
    def setStrategyKey(self, key):
        self._current_strategy = key
        self._update_previews()

    @Slot(int)
    def setStartNumber(self, val):
        self._start_num = val
        self._update_previews()

    @Slot(str)
    def setUtcOffset(self, text):
        self._utc_offset_str = text
        self._update_previews()

    @Slot(str)
    def setSearchPattern(self, text):
        if self._search_pattern != text:
            self._search_pattern = text
            self.searchPatternChanged.emit()
            self._update_previews()

    @Slot(str)
    def setReplacePattern(self, text):
        if self._replace_pattern != text:
            self._replace_pattern = text
            self.replacePatternChanged.emit()
            self._update_previews()

    @Slot(bool)
    def setUseRegex(self, enabled):
        if self._use_regex != enabled:
            self._use_regex = enabled
            self.useRegexChanged.emit()
            self._update_previews()

    @Slot(int, bool, bool)
    def handleSelection(self, index, is_ctrl, is_shift):
        total_count = len(self._raw_input_paths)
        if index < 0 or index >= total_count:
            return

        if is_shift and self._anchor_index != -1:
            start = min(self._anchor_index, index)
            end = max(self._anchor_index, index)
            range_set = set(range(start, end + 1))

            if is_ctrl:
                self._selected_indices.update(range_set)
            else:
                self._selected_indices = range_set
        elif is_ctrl:
            if index in self._selected_indices:
                self._selected_indices.remove(index)
            else:
                self._selected_indices.add(index)
            self._anchor_index = index
        else:
            self._selected_indices = {index}
            self._anchor_index = index

        self._input_model.set_selected_indices(self._selected_indices)
        self.selectedIndicesChanged.emit()

    @Slot()
    def selectAll(self):
        total_count = len(self._raw_input_paths)
        if total_count > 0:
            self._selected_indices = set(range(total_count))
            self._input_model.set_selected_indices(self._selected_indices)
            self.selectedIndicesChanged.emit()

    @Property("QStringList", notify=previewFilesChanged)
    def previewFiles(self):
        return self._output_model.items

    @Slot()
    def processFiles(self):
        files = self._raw_input_paths
        if self._is_processing or not files:
            return

        self._is_processing = True
        self._progress_value = 0.0
        self._status_message = "Starting..."
        self.isProcessingChanged.emit()
        self.progressValueChanged.emit()
        self.statusMessageChanged.emit()

        self._worker_thread = RenameWorker(
            files=list(files),
            strategy_key=self._current_strategy,
            utc_offset_str=self._utc_offset_str,
            start_num=self._start_num,
            jpeg_quality=self._jpeg_quality,
            search_pattern=self._search_pattern,
            replace_pattern=self._replace_pattern,
            use_regex=self._use_regex
        )

        self._worker_thread.progress.connect(self._on_worker_progress)
        self._worker_thread.finished.connect(self._on_worker_finished)
        self._worker_thread.cancelled.connect(self._on_worker_cancelled)
        self._worker_thread.error.connect(self._on_worker_error)

        self._worker_thread.start()

    @Slot(int, int, str)
    def _on_worker_progress(self, current, total, msg):
        self._progress_value = current / max(1, total)
        self._status_message = msg
        self.progressValueChanged.emit()
        self.statusMessageChanged.emit()

    @Slot(list)
    def _on_worker_finished(self, final_paths):
        self._raw_input_paths = list(final_paths)
        formatted_inputs = [format_parent_path(p) for p in self._raw_input_paths]
        self._input_model.set_items(formatted_inputs)
        self._selected_indices.clear()
        self._input_model.set_selected_indices(self._selected_indices)
        self._is_processing = False
        self._progress_value = 1.0
        self._status_message = "Done!"

        self._update_previews()

        self.filesChanged.emit()
        self.selectedIndicesChanged.emit()
        self.isProcessingChanged.emit()
        self.progressValueChanged.emit()
        self.statusMessageChanged.emit()

        self._worker_thread = None

    @Slot(str)
    def _on_worker_error(self, err_msg):
        self._is_processing = False
        self._status_message = f"Error: {err_msg}"
        self.isProcessingChanged.emit()
        self.statusMessageChanged.emit()
        self._worker_thread = None

    @Slot()
    def cancelProcessing(self):
        if self._worker_thread and self._worker_thread.isRunning():
            self._status_message = "Cancelling..."
            self.statusMessageChanged.emit()
            self._worker_thread.request_cancel()

    @Slot()
    def _on_worker_cancelled(self):
        self._is_processing = False
        self._progress_value = 0.0
        self._status_message = "Cancelled by user"
        self.isProcessingChanged.emit()
        self.progressValueChanged.emit()
        self.statusMessageChanged.emit()
        self._worker_thread = None
