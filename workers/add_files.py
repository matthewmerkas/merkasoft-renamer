import time
from urllib.parse import urlparse, unquote

from PySide6.QtCore import QRunnable, QUrl

from backend import generate_previews


class AddFilesWorker(QRunnable):
    """Worker task for processing dropped URLs and generating previews in background."""

    def __init__(self, raw_input, existing_paths, strategy_key, utc_offset_str, start_num, search_pattern,
                 replace_pattern, use_regex, callback_signal):
        super().__init__()
        self.raw_input = raw_input
        self.existing_paths = list(existing_paths)
        self.strategy_key = strategy_key
        self.utc_offset_str = utc_offset_str
        self.start_num = start_num
        self.search_pattern = search_pattern
        self.replace_pattern = replace_pattern
        self.use_regex = use_regex
        self.callback_signal = callback_signal

    def run(self):
        t_start = time.perf_counter()

        if isinstance(self.raw_input, str):
            items = self.raw_input.splitlines()
        elif isinstance(self.raw_input, (list, tuple)):
            items = self.raw_input
        else:
            items = [self.raw_input]

        t0 = time.perf_counter()
        new_unique_paths = []
        existing_set = set(self.existing_paths)
        new_unique_set = set()

        for item in items:
            if not item:
                continue

            path = ""
            if isinstance(item, QUrl):
                path = item.toLocalFile()
            elif isinstance(item, str):
                item_str = item.strip()
                if not item_str or item_str.startswith("#"):
                    continue
                if item_str.startswith("file://"):
                    parsed = urlparse(item_str)
                    path = unquote(parsed.path)
                elif item_str.startswith("file:"):
                    path = unquote(item_str[5:])
                else:
                    path = item_str

            if path and path not in existing_set and path not in new_unique_set:
                new_unique_paths.append(path)
                new_unique_set.add(path)

        t1 = time.perf_counter()

        if not new_unique_paths:
            return

        t4 = time.perf_counter()
        new_previews = generate_previews(
            strategy_key=self.strategy_key,
            files=new_unique_paths,
            utc_offset_str=self.utc_offset_str,
            start_num=self.start_num + len(self.existing_paths),
            search_pattern=self.search_pattern,
            replace_pattern=self.replace_pattern,
            use_regex=self.use_regex
        )
        t5 = time.perf_counter()

        self.callback_signal.emit({
            "new_unique_paths": new_unique_paths,
            "new_previews": new_previews,
            "t_parse": t1 - t0,
            "t_preview": t5 - t4,
            "t_total_bg": time.perf_counter() - t_start
        })
