import httpx
from typing import List, Dict, Any, Optional
from api.models import HubSpotProperty, PropertyOption, ObjectInfo, PropertyType, FieldType, PropertyValidationRule
import logging

logger = logging.getLogger(__name__)

class HubSpotClient:
    BASE_URL = "https://api.hubapi.com"
    
    # Object type ID mapping
    OBJECT_TYPE_IDS = {
        "contacts": "0-1",
        "companies": "0-2", 
        "deals": "0-3",
        "tickets": "0-5",
        "appointments": "0-421",
        "calls": "0-48",
        "communications": "0-18",
        "courses": "0-410",
        "emails": "0-49",
        "feedback_submissions": "0-19",
        "invoices": "0-53",
        "leads": "0-136",
        "line_items": "0-8",
        "listings": "0-420",
        "marketing_events": "0-54",
        "meetings": "0-47",
        "notes": "0-46",
        "orders": "0-123",
        "payments": "0-101",
        "postal_mail": "0-116",
        "products": "0-7",
        "quotes": "0-14",
        "services": "0-162",
        "subscriptions": "0-69",
        "tasks": "0-27",
        "users": "0-115"
    }
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def validate_token(self) -> bool:
        """Validate the HubSpot token by making a test API call"""
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/crm/v3/properties/contacts",
                headers=self.headers,
                params={"limit": 1}
            )
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            logger.error(f"Token validation failed: {e}")
            raise Exception(f"Invalid HubSpot token: {str(e)}")
    
    async def get_available_objects(self) -> Dict[str, List[ObjectInfo]]:
        """Get both standard and custom objects available in the portal"""
        standard_objects = [
            "contacts", "companies", "deals", "tickets", 
            "products", "line_items", "quotes", "calls", 
            "emails", "meetings", "notes", "tasks"
        ]
        
        # Get custom objects
        custom_objects = []
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/crm/v3/schemas",
                headers=self.headers
            )
            response.raise_for_status()
            schemas_data = response.json()
            
            if "results" in schemas_data:
                logger.info(f"Found {len(schemas_data['results'])} schemas total")
                for schema in schemas_data["results"]:
                    logger.info(f"Schema: {schema.get('name')} - fullyQualifiedName: {schema.get('fullyQualifiedName')} - objectTypeId: {schema.get('objectTypeId')}")
                    
                    fqn = schema.get("fullyQualifiedName", "")
                    object_type_id = schema.get("objectTypeId", "")
                    
                    # Custom objects have objectTypeId starting with "2-" and fullyQualifiedName starting with "p"
                    is_custom = object_type_id.startswith("2-") and fqn.startswith("p")
                    logger.info(f"Checking schema: objectTypeId='{object_type_id}', fullyQualifiedName='{fqn}', is_custom={is_custom}")
                    
                    if not is_custom:
                        logger.info(f"Skipping schema {schema.get('name')} - not a custom object")
                        continue
                    
                    logger.info(f"Adding custom object: {schema['name']} (ID: {schema['objectTypeId']})")
                    custom_objects.append(ObjectInfo(
                        name=schema["name"],
                        objectTypeId=schema["objectTypeId"],
                        labels=schema.get("labels", {}),
                        requiredProperties=schema.get("requiredProperties", []),
                        searchableProperties=schema.get("searchableProperties", []),
                        primaryDisplayProperty=schema.get("primaryDisplayProperty")
                    ))
        
        except Exception as e:
            logger.warning(f"Failed to fetch custom objects: {e}")
        
        return {
            "standard": [ObjectInfo(name=obj) for obj in standard_objects],
            "custom": custom_objects
        }
    
    async def get_properties(self, object_type: str) -> List[HubSpotProperty]:
        """Fetch all properties for a given object type"""
        all_properties = []
        after = None
        
        # Fetch all validation rules for this object type in bulk
        validation_rules_by_property = await self.get_all_property_validations(object_type)
        
        while True:
            params = {"limit": 100}
            if after:
                params["after"] = after
            
            try:
                response = await self.client.get(
                    f"{self.BASE_URL}/crm/v3/properties/{object_type}",
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                
                if "results" not in data:
                    break
                
                for prop_data in data["results"]:
                    property_obj = self._parse_property(prop_data)
                    if property_obj:
                        # Apply validation rules from bulk fetch
                        property_obj.validationRules = validation_rules_by_property.get(property_obj.name, [])
                        all_properties.append(property_obj)
                
                # Check for pagination
                paging = data.get("paging", {})
                if "next" in paging and "after" in paging["next"]:
                    after = paging["next"]["after"]
                else:
                    break
                    
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch properties for {object_type}: {e}")
                raise Exception(f"Failed to fetch properties: {str(e)}")
        
        return all_properties
    
    async def get_all_property_validations(self, object_type: str) -> Dict[str, List[PropertyValidationRule]]:
        """Fetch all validation rules for an object type"""
        try:
            object_type_id = self.OBJECT_TYPE_IDS.get(object_type)
            
            # For custom objects, use the object_type as the ID directly (it will be something like "2-123456")
            if not object_type_id and object_type.startswith("2-"):
                object_type_id = object_type
                
            if not object_type_id:
                logger.warning(f"No object type ID mapping found for {object_type}")
                return {}
            
            response = await self.client.get(
                f"{self.BASE_URL}/crm/v3/property-validations/{object_type_id}",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            validations_by_property = {}
            if "results" in data:
                for property_validations in data["results"]:
                    property_name = property_validations.get("propertyName")
                    if property_name:
                        rules = []
                        for rule_data in property_validations.get("propertyValidationRules", []):
                            rule = self._parse_validation_rule_v2(rule_data)
                            if rule:
                                rules.append(rule)
                        if rules:
                            validations_by_property[property_name] = rules
            
            return validations_by_property
            
        except httpx.HTTPError as e:
            logger.debug(f"No validation rules found for {object_type}: {e}")
            return {}
    
    def _parse_validation_rule(self, validation_data: Dict[str, Any]) -> Optional[PropertyValidationRule]:
        """Parse raw validation rule data into PropertyValidationRule model"""
        try:
            rule = PropertyValidationRule(
                name=validation_data.get("name", ""),
                enabled=validation_data.get("enabled", True),
                blocker=validation_data.get("blocker", False),
                message=validation_data.get("message")
            )
            
            # Parse different validation types based on the rule name/type
            rule_name = validation_data.get("name", "").lower()
            
            # Text length validations
            if "minlength" in rule_name or "min_length" in rule_name:
                rule.minLength = validation_data.get("minLength") or validation_data.get("min_length")
            if "maxlength" in rule_name or "max_length" in rule_name:
                rule.maxLength = validation_data.get("maxLength") or validation_data.get("max_length")
            
            # Number range validations
            if "min" in validation_data:
                rule.min = validation_data.get("min")
            if "max" in validation_data:
                rule.max = validation_data.get("max")
                
            # Regex pattern validation
            if "pattern" in validation_data:
                rule.pattern = validation_data.get("pattern")
            
            # Email/domain validations
            if "useDefaultBlockList" in validation_data:
                rule.useDefaultBlockList = validation_data.get("useDefaultBlockList")
            if "domainBlockList" in validation_data:
                rule.domainBlockList = validation_data.get("domainBlockList", [])
            
            return rule
            
        except Exception as e:
            logger.warning(f"Failed to parse validation rule: {e}")
            return None
    
    def _parse_validation_rule_v2(self, rule_data: Dict[str, Any]) -> Optional[PropertyValidationRule]:
        """Parse validation rule data from bulk validation endpoint"""
        try:
            rule_type = rule_data.get("ruleType", "")
            rule_arguments = rule_data.get("ruleArguments", [])
            
            rule = PropertyValidationRule(
                name=rule_type,
                enabled=True,  # Assume enabled if returned by API
                blocker=True,  # Validation rules are generally blockers
                message=None   # Not provided in bulk endpoint
            )
            
            # Parse different rule types based on ruleType
            if rule_type == "MIN_NUMBER" and rule_arguments:
                try:
                    rule.min = float(rule_arguments[0])
                except (ValueError, IndexError):
                    pass
                    
            elif rule_type == "MAX_NUMBER" and rule_arguments:
                try:
                    rule.max = float(rule_arguments[0])
                except (ValueError, IndexError):
                    pass
                    
            elif rule_type == "MIN_LENGTH" and rule_arguments:
                try:
                    rule.minLength = int(rule_arguments[0])
                except (ValueError, IndexError):
                    pass
                    
            elif rule_type == "MAX_LENGTH" and rule_arguments:
                try:
                    rule.maxLength = int(rule_arguments[0])
                except (ValueError, IndexError):
                    pass
                    
            elif rule_type == "REGEX" and rule_arguments:
                rule.pattern = rule_arguments[0]
                
            elif rule_type == "ALPHANUMERIC" and rule_arguments:
                # Handle NUMERIC_ONLY and other alphanumeric restrictions
                if "NUMERIC_ONLY" in rule_arguments:
                    rule.pattern = r"^\d+$"  # Equivalent regex for numeric only
                    rule.name = "NUMERIC_ONLY"
                    
            # Add more rule type mappings as needed
                
            return rule
            
        except Exception as e:
            logger.warning(f"Failed to parse validation rule v2: {e}")
            return None
    
    def _parse_property(self, prop_data: Dict[str, Any]) -> Optional[HubSpotProperty]:
        """Parse raw HubSpot property data into HubSpotProperty model"""
        try:
            # Parse options if they exist
            options = []
            if "options" in prop_data and prop_data["options"]:
                for opt in prop_data["options"]:
                    options.append(PropertyOption(
                        label=opt.get("label", ""),
                        value=opt.get("value", ""),
                        description=opt.get("description"),
                        hidden=opt.get("hidden", False),
                        displayOrder=opt.get("displayOrder")
                    ))
            
            # Map HubSpot types to our enum
            prop_type = self._map_property_type(prop_data.get("type", "string"))
            field_type = self._map_field_type(prop_data.get("fieldType", "text"))
            
            return HubSpotProperty(
                name=prop_data["name"],
                label=prop_data.get("label", prop_data["name"]),
                description=prop_data.get("description"),
                groupName=prop_data.get("groupName"),
                type=prop_type,
                fieldType=field_type,
                options=options,
                required=prop_data.get("required", False),
                searchableInGlobalSearch=prop_data.get("searchableInGlobalSearch", False),
                hasUniqueValue=prop_data.get("hasUniqueValue", False),
                hidden=prop_data.get("hidden", False),
                displayOrder=prop_data.get("displayOrder"),
                calculated=prop_data.get("calculated", False),
                externalOptions=prop_data.get("externalOptions", False),
                hubspotDefined=prop_data.get("hubspotDefined", False),
                showCurrencySymbol=prop_data.get("showCurrencySymbol"),
                createdAt=prop_data.get("createdAt"),
                updatedAt=prop_data.get("updatedAt"),
                archived=prop_data.get("archived", False)
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse property {prop_data.get('name', 'unknown')}: {e}")
            return None
    
    def _map_property_type(self, hubspot_type: str) -> PropertyType:
        """Map HubSpot property type to our enum"""
        type_mapping = {
            "string": PropertyType.STRING,
            "number": PropertyType.NUMBER,
            "date": PropertyType.DATE,
            "datetime": PropertyType.DATETIME,
            "enumeration": PropertyType.ENUMERATION,
            "bool": PropertyType.BOOL,
            "phone_number": PropertyType.PHONE_NUMBER,
            "json": PropertyType.JSON
        }
        return type_mapping.get(hubspot_type.lower(), PropertyType.STRING)
    
    def _map_field_type(self, hubspot_field_type: str) -> FieldType:
        """Map HubSpot field type to our enum"""
        field_type_mapping = {
            "text": FieldType.TEXT,
            "textarea": FieldType.TEXTAREA,
            "number": FieldType.NUMBER,
            "date": FieldType.DATE,
            "datetime": FieldType.DATETIME,
            "select": FieldType.SELECT,
            "radio": FieldType.RADIO,
            "checkbox": FieldType.CHECKBOX,
            "booleancheckbox": FieldType.BOOLEAN_CHECKBOX,
            "file": FieldType.FILE
        }
        return field_type_mapping.get(hubspot_field_type.lower(), FieldType.TEXT)