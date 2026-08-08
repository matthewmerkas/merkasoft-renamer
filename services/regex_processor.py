import os
import re
from services.base_processor import BaseProcessor


def natural_sort_key(path: str) -> list:
    basename = os.path.basename(path)
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', basename)]


class RegexProcessor(BaseProcessor):

    def generate_previews(self, files: list[str], search_pattern: str = "",
                          replace_pattern: str = "", use_regex: bool = False,
                          strategy_key: str = "replace_space", **kwargs) -> list[dict]:
        if not files:
            return []

        input_paths_abs = {os.path.abspath(f) for f in files}
        sorted_files = sorted(enumerate(files), key=lambda x: natural_sort_key(x[1]))

        compiled_regex = None
        if use_regex and search_pattern:
            try:
                compiled_regex = re.compile(search_pattern)
            except re.error:
                pass

        def transform_stem(stem: str) -> str:
            if not search_pattern:
                return stem
            if use_regex and compiled_regex:
                try:
                    return compiled_regex.sub(replace_pattern, stem)
                except Exception:
                    return stem
            return stem.replace(search_pattern, replace_pattern) if not use_regex else stem

        # Pass 1: Compute target names and count occurrences per directory
        targets, target_counts = [], {}
        for orig_idx, path in sorted_files:
            dirname, basename = os.path.split(path)
            stem, ext = os.path.splitext(basename)
            new_stem = transform_stem(stem)
            raw_target = f"{new_stem}{ext}"

            key = (dirname, raw_target)
            target_counts[key] = target_counts.get(key, 0) + 1
            targets.append((orig_idx, path, dirname, new_stem, ext, raw_target))

        # Pass 2: Resolve final filenames
        planned = [None] * len(files)
        dir_seen = {}

        for orig_idx, path, dirname, stem, ext, raw_target in targets:
            seen = dir_seen.setdefault(dirname, set())
            raw_abs = os.path.abspath(os.path.join(dirname, raw_target))

            disk_collision = os.path.exists(raw_abs) and raw_abs not in input_paths_abs

            # Always force suffix resolution for "replace_space" / "replace"
            has_conflict = (
                    strategy_key in ("replace_space", "replace")
                    or target_counts[(dirname, raw_target)] > 1
                    or disk_collision
                    or raw_target in seen
            )

            if has_conflict:
                counter = 1
                num_conflicts = target_counts.get((dirname, raw_target), 1)

                # Pad width directly matches the digit count of total conflicts in this group
                pad_width = max(1, len(str(num_conflicts)))

                while True:
                    # Dynamically scale width if counter exceeds initial pad_width
                    current_pad = max(pad_width, len(str(counter)))

                    if strategy_key == "replace_underscore":
                        suffix = f"_{counter:0{current_pad}d}"
                    else:
                        # Default ("replace_space" / "replace"): Always appends "001 01" format
                        suffix = f" {counter:03d} 01"

                    candidate = f"{stem}{suffix}{ext}"
                    cand_abs = os.path.abspath(os.path.join(dirname, candidate))
                    if candidate not in seen and not (os.path.exists(cand_abs) and cand_abs not in input_paths_abs):
                        break
                    counter += 1
            else:
                candidate = raw_target

            seen.add(candidate)

            input_preview = self.format_parent_path(path)
            output_preview = self.format_parent_path(dirname, candidate)

            planned[orig_idx] = {
                "original_index": orig_idx,
                "original_path": path,
                "dirname": dirname,
                "input_preview": input_preview,
                "target_name": candidate,
                "output_preview": output_preview,
                "action": "rename",
                "display_name": output_preview
            }

        return planned

    def process_item(self, item: dict, **kwargs) -> str | None:
        temp_path = item["temp_path"]
        target_path = os.path.join(item["dirname"], item["target_name"])

        os.rename(temp_path, target_path)
        return target_path
