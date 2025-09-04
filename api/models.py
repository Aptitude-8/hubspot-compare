from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class PropertyType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    DATE = "date"
    DATETIME = "datetime"
    ENUMERATION = "enumeration"
    BOOL = "bool"
    PHONE_NUMBER = "phone_number"
    JSON = "json"

class FieldType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    DATE = "date"
    DATETIME = "datetime"
    SELECT = "select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    BOOLEAN_CHECKBOX = "booleancheckbox"
    FILE = "file"

class PropertyOption(BaseModel):
    label: str
    value: str
    description: Optional[str] = None
    hidden: bool = False
    displayOrder: Optional[int] = None

class PropertyValidationRule(BaseModel):
    name: str
    enabled: bool = True
    blocker: bool = False
    message: Optional[str] = None
    # Text length validations
    minLength: Optional[int] = None
    maxLength: Optional[int] = None
    # Number validations
    min: Optional[float] = None
    max: Optional[float] = None
    # Regex validation
    pattern: Optional[str] = None
    # Other validation types
    useDefaultBlockList: Optional[bool] = None
    domainBlockList: Optional[List[str]] = None

class HubSpotProperty(BaseModel):
    name: str
    label: str
    description: Optional[str] = None
    groupName: Optional[str] = None
    type: PropertyType
    fieldType: FieldType
    options: List[PropertyOption] = []
    required: bool = False
    searchableInGlobalSearch: bool = False
    hasUniqueValue: bool = False
    hidden: bool = False
    displayOrder: Optional[int] = None
    calculated: bool = False
    externalOptions: bool = False
    hubspotDefined: bool = False
    showCurrencySymbol: Optional[bool] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    archived: bool = False
    validationRules: List[PropertyValidationRule] = []

class TokenPair(BaseModel):
    portal_a_token: str = Field(..., min_length=1)
    portal_b_token: str = Field(..., min_length=1)

class ObjectInfo(BaseModel):
    name: str
    objectTypeId: Optional[str] = None
    portalId: Optional[int] = None
    labels: Dict[str, str] = {}
    requiredProperties: List[str] = []
    searchableProperties: List[str] = []
    primaryDisplayProperty: Optional[str] = None

class ComparisonStatus(str, Enum):
    IDENTICAL = "identical"
    DIFFERENT = "different"
    ONLY_IN_A = "only_in_a"
    ONLY_IN_B = "only_in_b"
    MODIFIED = "modified"

class PropertyDiff(BaseModel):
    field_name: str
    portal_a_value: Any
    portal_b_value: Any
    status: ComparisonStatus

class PropertyComparison(BaseModel):
    property_name: str
    status: ComparisonStatus
    property_a: Optional[HubSpotProperty] = None
    property_b: Optional[HubSpotProperty] = None
    differences: List[PropertyDiff] = []

class ComparisonResult(BaseModel):
    object_type: str
    total_properties_a: int
    total_properties_b: int
    identical_count: int
    different_count: int
    only_in_a_count: int
    only_in_b_count: int
    comparisons: List[PropertyComparison] = []