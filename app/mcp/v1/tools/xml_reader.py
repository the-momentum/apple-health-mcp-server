import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from app.schemas.record import RecordType

xml_reader_router = FastMCP(name="XML Reader MCP")
_current_xml_file: str = ""


@xml_reader_router.tool
def set_xml_file(filename: str) -> str:
    """
    Set the current XML file path for all XML tools. This avoids passing the filename to every function.
    Checks if the file exists before setting.

    Parameters:
    - filename: Path to the XML file to use for all subsequent XML tool calls.

    Returns:
    - Confirmation message with the set file path.

    Notes for LLMs:
    - Call this tool before using other XML tools if you want to avoid passing the filename each time.
    - All other XML tools will use this file by default if filename is not provided.
    """
    global _current_xml_file
    path = Path(filename)
    if not path.exists():
        raise FileNotFoundError("Health export file not found. Please provide a valid filename.")
    _current_xml_file = filename
    return f"XML file set to: {filename}"


@xml_reader_router.tool
def get_xml_structure(filename: str = "") -> dict[str, Any]:
    """
    Analyze the structure and metadata of an Apple Health XML export file without loading the entire content.

    Parameters:
    - filename: Path to the XML file to analyze. If not provided, uses the file set by set_xml_file.

    Returns:
    - file_size_mb: Size of the file in megabytes
    - root_elements: List of unique root-level XML tags
    - record_types: List of unique health record types (see RecordType for most frequent types, but may include others)
    - workout_types: List of unique workout types
    - sources: List of unique data sources (device/app names)

    Notes for LLMs:
    - Use this to quickly understand the contents and structure of a health XML file
    - RecordType contains only the most frequent types; other types may appear as strings
    """
    try:
        xml_path = Path(filename) if filename else Path(_current_xml_file)
        structure = {
            "file_size_mb": round(xml_path.stat().st_size / (1024 * 1024), 2),
            "root_elements": [],
            "record_types": set(),
            "workout_types": set(),
            "sources": set(),
        }
        context = ET.iterparse(xml_path, events=("start", "end"))
        for event, elem in context:
            if event == "start":
                if elem.tag not in structure["root_elements"]:
                    structure["root_elements"].append(elem.tag)
                if elem.tag == "Record":
                    record_type = elem.get("type")
                    if record_type:
                        structure["record_types"].add(record_type)
                    source = elem.get("sourceName")
                    if source:
                        structure["sources"].add(source)
                elif elem.tag == "Workout":
                    workout_type = elem.get("workoutActivityType")
                    if workout_type:
                        structure["workout_types"].add(workout_type)
            elem.clear()
        structure["record_types"] = list(structure["record_types"])
        structure["workout_types"] = list(structure["workout_types"])
        structure["sources"] = list(structure["sources"])
        return structure
    except Exception as e:
        return {"error": f"Failed to analyze XML structure: {str(e)}"}


@xml_reader_router.tool
def search_xml_content(filename: str = "", query: str = "", max_results: int = 50) -> str:
    """
    Search for specific content in the Apple Health XML file and return matching records as XML text.

    Parameters:
    - filename: Path to the XML file to search. If not provided, uses the file set by set_xml_file.
    - query: Text to search for in any attribute value (case-insensitive)
    - max_results: Maximum number of matching records to return (default: 50)

    Returns:
    - A string containing up to max_results XML elements that match the query, or a message if no matches are found.

    Notes for LLMs:
    - Searches both Record and Workout elements
    - Useful for finding all records containing a specific value, device, or type
    - This function streams the file for memory efficiency and does not load the entire file into memory.
    - If filename is not provided, the file set by set_xml_file will be used.
    """
    try:
        xml_path = Path(filename) if filename else Path(_current_xml_file)
        results = []
        query_lower = query.lower()
        context = ET.iterparse(xml_path, events=("start",))
        for event, elem in context:
            if elem.tag in ["Record", "Workout"]:
                matches = any(
                    value and query_lower in value.lower() for value in elem.attrib.values()
                )
                if matches:
                    elem_str = ET.tostring(elem, encoding="unicode", method="xml")
                    results.append(elem_str)
                    if len(results) >= max_results:
                        break
            elem.clear()
        if not results:
            return f"No matches found for query: '{query}'"
        return f"""Search Results for '{query}' (showing up to {max_results} results):\n\n{chr(10).join(results)}\n\nTotal matches found: {len(results)}"""
    except Exception as e:
        return f"Error searching XML content: {str(e)}"


@xml_reader_router.tool
def get_xml_by_type(filename: str = "", record_type: RecordType | str = "", limit: int = 20) -> str:
    """
    Get all records of a specific health record type from the Apple Health XML file.

    Parameters:
    - filename: Path to the XML file to search. If not provided, uses the file set by set_xml_file.
    - record_type: The type of health record to retrieve (use RecordType for most frequent types, or any string for custom/rare types)
    - limit: Maximum number of records to return (default: 20)

    Returns:
    - A string containing up to limit XML elements of the specified type, or a message if no records are found.

    Notes for LLMs:
    - Use this to extract all records of a given type for further analysis or conversion
    - RecordType contains only the most frequent types; other types may appear as strings
    - Example types: "HKQuantityTypeIdentifierStepCount", "HKQuantityTypeIdentifierBodyMassIndex", etc.
    - This function streams the file for memory efficiency and does not load the entire file into memory.
    - If filename is not provided, the file set by set_xml_file will be used.
    """
    try:
        xml_path = Path(filename) if filename else Path(_current_xml_file)
        results = []
        context = ET.iterparse(xml_path, events=("start",))
        for event, elem in context:
            if elem.tag == "Record" and elem.get("type") == record_type:
                elem_str = ET.tostring(elem, encoding="unicode", method="xml")
                results.append(elem_str)
                if len(results) >= limit:
                    break
            elem.clear()
        if not results:
            return f"No records found of type: '{record_type}'"
        return f"""Records of type '{record_type}' (showing up to {limit} results):\n\n{chr(10).join(results)}\n\nTotal records found: {len(results)}"""
    except Exception as e:
        return f"Error getting XML by type: {str(e)}"
