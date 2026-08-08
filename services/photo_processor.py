import os
from datetime import datetime, timedelta
from dateutil.parser import parse, ParserError
import exifread
from PIL import Image
from pillow_heif import register_heif_opener

from services.base_processor import BaseProcessor

register_heif_opener()


def parse_offset(offset_str: str, inverse: bool = False) -> int:
    if not (isinstance(offset_str, str) and len(offset_str) > 0):
        return 0
    multiplier = 1 if offset_str[0] == "+" else (-1 if offset_str[0] == "-" else 1)
    if inverse:
        multiplier *= -1
    try:
        parts = offset_str.lstrip("+-").split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        return (hour * 60 + minute) * multiplier
    except (ValueError, IndexError):
        return 0


def extract_datetime(file_path: str, utc_offset_str: str = "+10:00") -> datetime:
    _, file_name = os.path.split(file_path)
    offset_input_mins = parse_offset(utc_offset_str)

    try:
        with open(file_path, "rb") as f:
            tags = exifread.process_file(f, stop_tag="EXIF DateTimeOriginal", details=False) or {}
    except Exception:
        tags = {}

    def datetime_from_tags(key):
        raw_dt = str(tags.get(key)).split(".")[0]
        dt = datetime.strptime(raw_dt, "%Y:%m:%d %H:%M:%S")
        offset_time = str(tags.get("EXIF OffsetTimeOriginal") or tags.get("EXIF OffsetTime") or "")
        if isinstance(offset_time, str) and len(offset_time) > 0:
            offset_exif = parse_offset(offset_time, inverse=True)
            return dt + timedelta(minutes=offset_exif) + timedelta(minutes=offset_input_mins)
        return dt

    if "EXIF DateTimeOriginal" in tags:
        try:
            return datetime_from_tags("EXIF DateTimeOriginal")
        except Exception:
            pass
    if "Image DateTime" in tags:
        try:
            return datetime_from_tags("Image DateTime")
        except Exception:
            pass

    try:
        return parse(file_name, ignoretz=True, dayfirst=True, yearfirst=True, fuzzy=True)
    except ParserError:
        try:
            before, _, after = file_name.partition("_")
            datetime_str = (after or before).rpartition(".")[0]
            return datetime.strptime(datetime_str, "%Y%m%d_%H%M%S")
        except (ValueError, TypeError):
            return datetime.fromtimestamp(os.path.getmtime(file_path))


def format_new_basename(dt: datetime, strategy_key: str, counters: dict, global_counter: int, start_num: int) -> tuple[str, int]:
    if strategy_key == "sequential":
        year_str = dt.strftime("%Y")
        pad_width = max(4, len(str(global_counter)))
        new_name = f"{year_str} {global_counter:0{pad_width}d} 01"
        return new_name, global_counter + 1
    else:
        date_formatted = dt.strftime("%Y %m %b %d")
        if date_formatted not in counters:
            counters[date_formatted] = start_num
        day_counter = counters[date_formatted]
        counters[date_formatted] += 1
        pad_width = max(3, len(str(day_counter)))
        new_name = f"{date_formatted} {day_counter:0{pad_width}d} 01"
        return new_name, global_counter


class PhotoProcessor(BaseProcessor):

    def generate_previews(self, files: list[str], strategy_key: str = "date",
                          utc_offset_str: str = "+10:00", start_num: int = 1, **kwargs) -> list[dict]:
        if not files:
            return []

        start_num = kwargs.get("start_number", start_num)
        input_paths_abs = {os.path.abspath(f) for f in files}

        item_metas = []
        for idx, path in enumerate(files):
            dt = extract_datetime(path, utc_offset_str)
            item_metas.append({"original_index": idx, "path": path, "dt": dt})

        item_metas.sort(key=lambda x: (x["dt"], x["path"]))

        counters = {}
        global_counter = start_num
        last_base_lower = ""
        planned_items = []
        dir_seen = {}

        for item in item_metas:
            path = item["path"]
            dt = item["dt"]
            dirname, filename = os.path.split(path)
            base, ext = os.path.splitext(filename)
            base_lower = base.lower()
            ext_lower = ext.lower()

            input_preview = self.format_parent_path(dirname, filename)

            # Case-insensitive Live Photo (.mov) pairing check
            if ext_lower == ".mov" and last_base_lower and base_lower == last_base_lower:
                planned_items.append({
                    "original_index": item["original_index"],
                    "original_path": path,
                    "dirname": dirname,
                    "filename": filename,
                    "input_preview": input_preview,
                    "output_preview": f"[DELETE] {filename} (Live Photo)",
                    "action": "delete",
                    "display_name": f"[DELETE] {input_preview} (Live Photo)"
                })
                continue

            last_base_lower = base_lower
            new_base_name, global_counter = format_new_basename(dt, strategy_key, counters, global_counter, start_num)

            if ext_lower in [".heic", ".heif"]:
                target_ext = ".jpg"
                action = "convert"
            else:
                target_ext = ".jpg" if ext_lower == ".jpeg" else ext
                action = "rename"

            seen = dir_seen.setdefault(dirname, set())
            candidate_base = new_base_name

            # Collision & disk existence resolution
            counter_sub = 1
            while True:
                candidate = f"{candidate_base}{target_ext}"
                cand_abs = os.path.abspath(os.path.join(dirname, candidate))
                disk_collision = os.path.exists(cand_abs) and cand_abs not in input_paths_abs

                if candidate.lower() not in seen and not disk_collision:
                    break

                counter_sub += 1
                if candidate_base.endswith(" 01"):
                    stem_prefix = candidate_base[:-3]
                    candidate_base = f"{stem_prefix} {counter_sub:02d}"
                else:
                    candidate_base = f"{new_base_name}_{counter_sub}"

            target_name = f"{candidate_base}{target_ext}"
            seen.add(target_name.lower())

            output_preview = self.format_parent_path(dirname, target_name)

            planned_items.append({
                "original_index": item["original_index"],
                "original_path": path,
                "dirname": dirname,
                "filename": filename,
                "input_preview": input_preview,
                "target_name": target_name,
                "output_preview": output_preview,
                "action": action,
                "display_name": output_preview
            })

        return planned_items

    def process_item(self, item: dict, jpeg_quality: int = 90, **kwargs) -> str | None:
        temp_path = item["temp_path"]
        dirname = item["dirname"]
        action = item["action"]

        if action == "delete":
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return None

        target_path = os.path.join(dirname, item["target_name"])

        if action == "convert":
            image = Image.open(temp_path)
            image.save(target_path, quality=jpeg_quality, exif=image.getexif())
            os.remove(temp_path)
            return target_path

        elif action == "rename":
            os.rename(temp_path, target_path)
            return target_path

        return None
