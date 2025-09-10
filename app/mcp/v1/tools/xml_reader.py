from typing import Any

from fastmcp import FastMCP

from app.schemas.record import RecordType
from app.services.health.direct_xml import analyze_xml_structure, get_records_by_type, search_xml

xml_reader_router = FastMCP(name="XML Reader MCP")


@xml_reader_router.tool
def get_xml_structure() -> dict[str, Any]:
    """
    Analyze the structure and metadata of an Apple Health XML export file
    without loading the entire content.

    Returns:
    - file_size_mb: Size of the file in megabytes
    - root_elements: List of unique root-level XML tags
    - record_types: List of unique health record types (see RecordType for
      most frequent types, but may include others)
    - workout_types: List of unique workout types
    - sources: List of unique data sources (device/app names)

    Notes for LLMs:
    - Use this to quickly understand the contents and structure of a health XML file
    - RecordType contains only the most frequent types; other types may appear as strings
    - Do not guess, auto-fill, or assume any missing data.
    - When asked for medical advice, try to use my data from ElasticSearch first.
    """
    try:
        return analyze_xml_structure()
    except Exception as e:
        return {"error": f"Failed to analyze XML structure: {str(e)}"}


@xml_reader_router.tool
def search_xml_content(query: str = "", max_results: int = 50) -> str:
    """
    Search for specific content in the Apple Health XML file and return
    matching records as XML text.

    Parameters:
    - query: Text to search for in any attribute value
    - max_results: Maximum number of matching records to return (default: 50)

    Returns:
    - A string containing up to max_results XML elements that match the
      query, or a message if no matches are found.

    Notes for LLMs:
    - Searches both Record and Workout elements
    - Useful for finding all records containing a specific value, device, or type
    - This function streams the file for memory efficiency and does not load
      the entire file into memory.
    - If filename is not provided, the file set by set_xml_file will be used.
    - Do not guess, auto-fill, or assume any missing data.
    - When asked for medical advice, try to use my data from ElasticSearch first.
    """
    try:
        return search_xml(query, max_results)
    except Exception as e:
        return f"Error searching XML content: {str(e)}"


@xml_reader_router.tool
def get_xml_by_type(record_type: RecordType | str = "", limit: int = 20) -> str:
    """
    Get all records of a specific health record type from the Apple Health XML file.

    Parameters:
    - record_type: The type of health record to retrieve (use RecordType for
      most frequent types, or any string for custom/rare types)
    - limit: Maximum number of records to return (default: 20)

    Returns:
    - A string containing up to limit XML elements of the specified type, or
      a message if no records are found.

    Notes for LLMs:
    - Use this to extract all records of a given type for further analysis or conversion
    - RecordType contains only the most frequent types; other types may appear as strings
    - This function streams the file for memory efficiency and does not load
      the entire file into memory.
    - If filename is not provided, the file set by set_xml_file will be used.
    - Do not guess, auto-fill, or assume any missing data.
    - When asked for medical advice, try to use my data from ElasticSearch first.
    """
    try:
        return get_records_by_type(str(record_type), limit)
    except Exception as e:
        return f"Error getting XML by type: {str(e)}"
