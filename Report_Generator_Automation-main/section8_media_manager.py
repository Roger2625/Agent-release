import os
import shutil
import uuid


def _unique_name(prefix: str, original_filename: str) -> str:
    unique_id = str(uuid.uuid4())[:8]
    safe_basename = os.path.basename(original_filename or "file")
    if prefix:
        return f"{prefix}_uploaded_{unique_id}_{safe_basename}"
    return f"uploaded_{unique_id}_{safe_basename}"


def _resolve_absolute(import_project_dir: str, relative_path: str) -> str:
    if not relative_path:
        return ""
    # Join with import project's directory; keep relative JSON path intact
    return os.path.join(import_project_dir or "", relative_path)


def _copy_file_if_exists(src_abs: str, dst_dir: str, new_filename: str) -> str:
    try:
        os.makedirs(dst_dir, exist_ok=True)
        dst_path = os.path.join(dst_dir, new_filename)
        shutil.copy2(src_abs, dst_path)
        return dst_path
    except Exception:
        return ""


def _strip_original_path(media_dict: dict) -> dict:
    # Return a shallow copy without original_path if present
    cleaned = dict(media_dict or {})
    if "original_path" in cleaned:
        cleaned.pop("original_path", None)
    return cleaned


def process_section8_media(template_config: dict, import_project_dir: str, code_folder: str, raw_logs_folder: str) -> dict:
    """
    Copy Section 8 media (scripts/images) into export folders and update template_config
    to use relative paths only, mirroring Section 11 behavior. This mutates and returns
    the provided template_config.
    """
    if not template_config:
        return template_config

    configuration = template_config.get("configuration", {})

    # Helper to process an array of media dicts
    def handle_media_list(media_list: list, kind: str, prefix: str):
        updated_list = []
        for item in media_list or []:
            if isinstance(item, dict):
                item = _strip_original_path(item)
                rel_path = item.get("path", "")
                filename = item.get("filename", os.path.basename(rel_path))
                # Decide target folder based on kind
                if kind == "script":
                    target_dir = code_folder
                else:
                    target_dir = raw_logs_folder
                abs_path = _resolve_absolute(import_project_dir, rel_path)
                if abs_path and os.path.exists(abs_path):
                    new_name = _unique_name(prefix, filename)
                    copied = _copy_file_if_exists(abs_path, target_dir, new_name)
                    if copied:
                        # Update JSON to relative target path
                        new_rel = f"code/{new_name}" if kind == "script" else f"raw_logs/{new_name}"
                        updated_list.append({
                            "path": new_rel,
                            "filename": new_name,
                            "original_filename": item.get("original_filename", filename),
                            "description": item.get("description", ""),
                            "is_pasted": bool(item.get("is_pasted", False)),
                        })
                        continue
                # If not copied, keep item but without original_path
                updated_list.append(item)
            else:
                # Non-dict placeholders or strings are preserved as-is
                updated_list.append(item)
        return updated_list

    # 8.1 Test Scenarios
    scenarios = configuration.get("test_scenarios", [])
    for scenario in scenarios:
        if isinstance(scenario, dict):
            scenario["images"] = handle_media_list(scenario.get("images", []), kind="image", prefix="scenario")
            scenario["scripts"] = handle_media_list(scenario.get("scripts", []), kind="script", prefix="scenario")

    # 8.2 Test Bed Diagram
    tbd = configuration.get("test_bed_diagram", {})
    if isinstance(tbd, dict):
        tbd["images"] = handle_media_list(tbd.get("images", []), kind="image", prefix="test_bed_diagram")
        tbd["scripts"] = handle_media_list(tbd.get("scripts", []), kind="script", prefix="test_bed_diagram")

    # 8.3 Tools Required
    tools = configuration.get("tools_required", [])
    for tool in tools:
        if isinstance(tool, dict):
            tool["images"] = handle_media_list(tool.get("images", []), kind="image", prefix="tool")
            tool["scripts"] = handle_media_list(tool.get("scripts", []), kind="script", prefix="tool")

    # 8.4 Execution Steps (base steps from Section 8)
    exec_steps = configuration.get("execution_steps", [])
    for item in exec_steps:
        if isinstance(item, dict):
            item["images"] = handle_media_list(item.get("images", []), kind="image", prefix="exec_step")
            item["scripts"] = handle_media_list(item.get("scripts", []), kind="script", prefix="exec_step")

    return template_config


