import os
import re
from services.base_processor import BaseProcessor


def natural_sort_key(path: str) -> list:
    basename = os.path.basename(path)
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', basename)]


class RegexProcessor(BaseProcessor):

    def generate_previews(self, files: list[str], search_pattern: str = "",
                          replace_pattern: str = "", use_regex: bool = False,
                          strategy_key: str = "replace_space", start_num: int = 1,
                          **kwargs) -> list[dict]:
        if not files:
            return []

        start_num = kwargs.get("start_number", start_num)

        input_paths_abs = {os.path.abspath(f) for f in files}
        sorted_files = sorted(enumerate(files), key=lambda x: natural_sort_key(x[1]))

        compiled_regex = None
        if use_regex and search_pattern:
            try:
                compiled_regex = re.compile(search_pattern)
            except re.error:
                pass

        def transform_stem(stem: str, file_idx: int) -> str:
            if not search_pattern:
                return stem

            current_num = start_num + file_idx
            actual_replace = replace_pattern.replace("{num}", str(current_num))

            if use_regex and compiled_regex:
                try:
                    return compiled_regex.sub(actual_replace, stem)
                except Exception:
                    return stem
            return stem.replace(search_pattern, actual_replace) if not use_regex else stem

        # Pass 1: Group by directory and STEM (ignoring extension & case)
        targets, stem_counts = [], {}
        for seq_idx, (orig_idx, path) in enumerate(sorted_files):
            dirname, basename = os.path.split(path)
            stem, ext = os.path.splitext(basename)
            new_stem = transform_stem(stem, seq_idx)
            raw_target = f"{new_stem}{ext}"

            # Group key ignores extension and forces lowercase for case-insensitivity
            stem_key = (dirname, new_stem.lower())
            stem_counts[stem_key] = stem_counts.get(stem_key, 0) + 1
            targets.append((orig_idx, path, dirname, new_stem, ext, raw_target, stem_key))

        # Pass 2: Resolve final filenames across the shared stem group
        planned = [None] * len(files)
        dir_seen = {}
        dir_counters = {}

        for orig_idx, path, dirname, stem, ext, raw_target, stem_key in targets:
            seen = dir_seen.setdefault(dirname, set())
            raw_abs = os.path.abspath(os.path.join(dirname, raw_target))

            disk_collision = os.path.exists(raw_abs) and raw_abs not in input_paths_abs

            # Check for stem-level conflict across all extensions
            has_conflict = (
                    strategy_key in ("replace_space", "replace")
                    or stem_counts[stem_key] > 1
                    or disk_collision
                    or raw_target.lower() in seen
            )

            if has_conflict:
                # Retrieve the next counter position for this stem group
                counter = dir_counters.get(stem_key, start_num)
                num_conflicts = stem_counts.get(stem_key, 1)

                max_counter = start_num + num_conflicts - 1
                pad_width = max(1, len(str(max_counter)))

                while True:
                    current_pad = max(pad_width, len(str(counter)))

                    if strategy_key == "replace_underscore":
                        suffix = f"_{counter:0{current_pad}d}"
                    else:
                        suffix = f"{counter:0{max(3, current_pad)}d} 01"

                    candidate = f"{stem}{suffix}{ext}"
                    cand_abs = os.path.abspath(os.path.join(dirname, candidate))

                    if candidate.lower() not in seen and not (
                            os.path.exists(cand_abs) and cand_abs not in input_paths_abs):
                        dir_counters[stem_key] = counter + 1
                        break
                    counter += 1
            else:
                candidate = raw_target

            seen.add(candidate.lower())

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
