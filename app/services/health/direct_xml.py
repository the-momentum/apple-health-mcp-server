import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterator
from xml.etree.ElementTree import Element

from app.config import settings


def get_xml_path() -> Path:
    return Path(settings.RAW_XML_PATH)


def stream_xml_elements(tag: str | list[str] | None = None) -> Iterator[Element]:
    xml_path = get_xml_path()
    context = ET.iterparse(xml_path, events=("start",))
    for _, elem in context:
        if (
            tag is None
            or (isinstance(tag, str) and elem.tag == tag)
            or (isinstance(tag, (list, tuple)) and elem.tag in tag)
        ):
            yield elem
        elem.clear()


def extract_record_type(elem: Element) -> str | None:
    return elem.get("type") if elem.tag == "Record" else None


def extract_workout_type(elem: Element) -> str | None:
    return elem.get("workoutActivityType") if elem.tag == "Workout" else None


def extract_source(elem: Element) -> str | None:
    return elem.get("sourceName") if elem.tag == "Record" else None


def analyze_xml_structure() -> dict[str, Any]:
    xml_path = get_xml_path()
    structure = {
        "file_size_mb": round(xml_path.stat().st_size / (1024 * 1024), 2),
        "root_elements": set(),
        "record_types": set(),
        "workout_types": set(),
        "sources": set(),
    }
    for elem in stream_xml_elements():
        structure["root_elements"].add(elem.tag)
        if rt := extract_record_type(elem):
            structure["record_types"].add(rt)
        if wt := extract_workout_type(elem):
            structure["workout_types"].add(wt)
        if src := extract_source(elem):
            structure["sources"].add(src)
    # Convert sets to lists
    for k in ["root_elements", "record_types", "workout_types", "sources"]:
        structure[k] = list(structure[k])
    return structure


def search_xml(query: str = "", max_results: int = 50) -> str:
    results = []
    query_lower = query.lower()
    for elem in stream_xml_elements(["Record", "Workout"]):
        matches = any(value and query_lower in value.lower() for value in elem.attrib.values())
        if matches:
            elem_str = ET.tostring(elem, encoding="unicode", method="xml")
            results.append(elem_str)
            if len(results) >= max_results:
                break
    if not results:
        return f"No matches found for query: '{query}'"
    return f"""Search Results for '{query}' (showing up to {max_results} results):\n\n{chr(10).join(results)}\n\nTotal matches found: {len(results)}"""


def get_records_by_type(record_type: str = "", limit: int = 20) -> str:
    results = []
    for elem in stream_xml_elements("Record"):
        if extract_record_type(elem) == record_type:
            elem_str = ET.tostring(elem, encoding="unicode", method="xml")
            results.append(elem_str)
            if len(results) >= limit:
                break
    if not results:
        return f"No records found of type: '{record_type}'"
    return f"""Records of type '{record_type}' (showing up to {limit} results):\n\n{chr(10).join(results)}\n\nTotal records found: {len(results)}"""
