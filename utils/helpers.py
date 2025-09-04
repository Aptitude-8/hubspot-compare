"""
Utility functions for the HubSpot comparison tool.
"""

from typing import Any, Dict, List, Optional
import json


def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get a value from a dictionary with a default fallback."""
    return dictionary.get(key, default)


def format_property_value(value: Any) -> str:
    """Format a property value for display."""
    if value is None:
        return "N/A"
    elif isinstance(value, bool):
        return "Yes" if value else "No"
    elif isinstance(value, (list, dict)):
        return json.dumps(value, indent=2)
    else:
        return str(value)


def normalize_property_name(name: str) -> str:
    """Normalize property names for comparison."""
    return name.lower().strip()


def calculate_similarity_score(prop_a: Dict[str, Any], prop_b: Dict[str, Any]) -> float:
    """Calculate a similarity score between two properties (0-1)."""
    if not prop_a or not prop_b:
        return 0.0
    
    score = 0.0
    total_checks = 0
    
    # Compare basic attributes
    comparable_fields = ['type', 'fieldType', 'required', 'hidden']
    
    for field in comparable_fields:
        total_checks += 1
        if prop_a.get(field) == prop_b.get(field):
            score += 1
    
    # Compare labels (case insensitive)
    total_checks += 1
    if prop_a.get('label', '').lower() == prop_b.get('label', '').lower():
        score += 1
    
    # Compare options count for enumeration fields
    if prop_a.get('type') == 'enumeration' and prop_b.get('type') == 'enumeration':
        total_checks += 1
        options_a = len(prop_a.get('options', []))
        options_b = len(prop_b.get('options', []))
        if options_a == options_b:
            score += 1
    
    return score / total_checks if total_checks > 0 else 0.0


def group_properties_by_category(properties: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group properties by their groupName for better organization."""
    grouped = {}
    
    for prop in properties:
        group_name = prop.get('groupName', 'Other')
        if group_name not in grouped:
            grouped[group_name] = []
        grouped[group_name].append(prop)
    
    return grouped


def export_comparison_to_dict(comparison_result: Any) -> Dict[str, Any]:
    """Export comparison results to a dictionary format suitable for JSON export."""
    if hasattr(comparison_result, 'model_dump'):
        return comparison_result.model_dump()
    elif hasattr(comparison_result, 'dict'):
        return comparison_result.dict()
    else:
        return {}


def validate_hubspot_token_format(token: str) -> bool:
    """Basic validation for HubSpot private app token format."""
    if not token or not isinstance(token, str):
        return False
    
    # HubSpot private app tokens typically start with 'pat-' and have a specific format
    # This is a basic check - actual validation happens via API call
    return (
        token.startswith('pat-') and 
        len(token) > 20 and
        '-' in token[4:]  # Has additional hyphens after 'pat-'
    )