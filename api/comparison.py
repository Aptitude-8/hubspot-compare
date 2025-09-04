from typing import List, Dict, Set
from api.models import (
    HubSpotProperty, 
    PropertyComparison, 
    ComparisonResult, 
    ComparisonStatus,
    PropertyDiff
)
import logging

logger = logging.getLogger(__name__)

class PropertyComparer:
    """Handles comparison logic between HubSpot properties from different portals"""
    
    def compare_properties(self, properties_a: List[HubSpotProperty], properties_b: List[HubSpotProperty]) -> ComparisonResult:
        """Compare properties between two portals and return detailed comparison results"""
        
        # Create lookup dictionaries for faster access
        props_a_dict = {prop.name: prop for prop in properties_a}
        props_b_dict = {prop.name: prop for prop in properties_b}
        
        # Get all unique property names
        all_property_names = set(props_a_dict.keys()) | set(props_b_dict.keys())
        
        comparisons = []
        counters = {
            "identical": 0,
            "different": 0,
            "only_in_a": 0,
            "only_in_b": 0
        }
        
        for prop_name in sorted(all_property_names):
            prop_a = props_a_dict.get(prop_name)
            prop_b = props_b_dict.get(prop_name)
            
            if prop_a and prop_b:
                # Property exists in both portals - compare them
                comparison = self._compare_single_property(prop_a, prop_b)
                if comparison.status == ComparisonStatus.IDENTICAL:
                    counters["identical"] += 1
                else:
                    counters["different"] += 1
            elif prop_a and not prop_b:
                # Property only exists in portal A
                comparison = PropertyComparison(
                    property_name=prop_name,
                    status=ComparisonStatus.ONLY_IN_A,
                    property_a=prop_a,
                    property_b=None
                )
                counters["only_in_a"] += 1
            else:
                # Property only exists in portal B
                comparison = PropertyComparison(
                    property_name=prop_name,
                    status=ComparisonStatus.ONLY_IN_B,
                    property_a=None,
                    property_b=prop_b
                )
                counters["only_in_b"] += 1
            
            comparisons.append(comparison)
        
        return ComparisonResult(
            object_type="unknown",  # This will be set by the calling function
            total_properties_a=len(properties_a),
            total_properties_b=len(properties_b),
            identical_count=counters["identical"],
            different_count=counters["different"],
            only_in_a_count=counters["only_in_a"],
            only_in_b_count=counters["only_in_b"],
            comparisons=comparisons
        )
    
    def _compare_single_property(self, prop_a: HubSpotProperty, prop_b: HubSpotProperty) -> PropertyComparison:
        """Compare two properties with the same name from different portals"""
        differences = []
        
        # Compare basic attributes
        fields_to_compare = [
            ("label", "Label"),
            ("description", "Description"),
            ("groupName", "Group Name"),
            ("type", "Type"),
            ("fieldType", "Field Type"),
            ("required", "Required"),
            ("searchableInGlobalSearch", "Searchable in Global Search"),
            ("hasUniqueValue", "Has Unique Value"),
            ("hidden", "Hidden"),
            ("displayOrder", "Display Order"),
            ("calculated", "Calculated"),
            ("externalOptions", "External Options"),
            ("hubspotDefined", "HubSpot Defined"),
            ("showCurrencySymbol", "Show Currency Symbol")
        ]
        
        for field_name, display_name in fields_to_compare:
            value_a = getattr(prop_a, field_name)
            value_b = getattr(prop_b, field_name)
            
            if value_a != value_b:
                differences.append(PropertyDiff(
                    field_name=display_name,
                    portal_a_value=value_a,
                    portal_b_value=value_b,
                    status=ComparisonStatus.DIFFERENT
                ))
        
        # Compare options (for enumeration/select fields)
        if prop_a.options or prop_b.options:
            options_diff = self._compare_options(prop_a.options, prop_b.options)
            if options_diff:
                differences.extend(options_diff)
        
        # Compare validation rules
        if prop_a.validationRules or prop_b.validationRules:
            validation_diff = self._compare_validation_rules(prop_a.validationRules, prop_b.validationRules)
            if validation_diff:
                differences.extend(validation_diff)
        
        # Determine overall status
        status = ComparisonStatus.IDENTICAL if not differences else ComparisonStatus.DIFFERENT
        
        return PropertyComparison(
            property_name=prop_a.name,
            status=status,
            property_a=prop_a,
            property_b=prop_b,
            differences=differences
        )
    
    def _compare_options(self, options_a: List, options_b: List) -> List[PropertyDiff]:
        """Compare property options (for enumeration fields)"""
        differences = []
        
        # Convert to dictionaries for easier comparison
        opts_a_dict = {opt.value: opt for opt in options_a} if options_a else {}
        opts_b_dict = {opt.value: opt for opt in options_b} if options_b else {}
        
        all_option_values = set(opts_a_dict.keys()) | set(opts_b_dict.keys())
        
        # Check for options that exist in both portals
        for opt_value in all_option_values:
            opt_a = opts_a_dict.get(opt_value)
            opt_b = opts_b_dict.get(opt_value)
            
            if opt_a and opt_b:
                # Compare option properties
                if opt_a.label != opt_b.label:
                    differences.append(PropertyDiff(
                        field_name=f"Option '{opt_value}' Label",
                        portal_a_value=opt_a.label,
                        portal_b_value=opt_b.label,
                        status=ComparisonStatus.DIFFERENT
                    ))
                
                if opt_a.description != opt_b.description:
                    differences.append(PropertyDiff(
                        field_name=f"Option '{opt_value}' Description",
                        portal_a_value=opt_a.description,
                        portal_b_value=opt_b.description,
                        status=ComparisonStatus.DIFFERENT
                    ))
                
                if opt_a.hidden != opt_b.hidden:
                    differences.append(PropertyDiff(
                        field_name=f"Option '{opt_value}' Hidden",
                        portal_a_value=opt_a.hidden,
                        portal_b_value=opt_b.hidden,
                        status=ComparisonStatus.DIFFERENT
                    ))
                
                if opt_a.displayOrder != opt_b.displayOrder:
                    differences.append(PropertyDiff(
                        field_name=f"Option '{opt_value}' Display Order",
                        portal_a_value=opt_a.displayOrder,
                        portal_b_value=opt_b.displayOrder,
                        status=ComparisonStatus.DIFFERENT
                    ))
            
            elif opt_a and not opt_b:
                differences.append(PropertyDiff(
                    field_name=f"Option '{opt_value}'",
                    portal_a_value=f"{opt_a.label} ({opt_a.value})",
                    portal_b_value=None,
                    status=ComparisonStatus.ONLY_IN_A
                ))
            
            elif opt_b and not opt_a:
                differences.append(PropertyDiff(
                    field_name=f"Option '{opt_value}'",
                    portal_a_value=None,
                    portal_b_value=f"{opt_b.label} ({opt_b.value})",
                    status=ComparisonStatus.ONLY_IN_B
                ))
        
        return differences
    
    def _compare_validation_rules(self, rules_a: List, rules_b: List) -> List[PropertyDiff]:
        """Compare property validation rules"""
        differences = []
        
        # Convert to dictionaries for easier comparison
        rules_a_dict = {rule.name: rule for rule in rules_a} if rules_a else {}
        rules_b_dict = {rule.name: rule for rule in rules_b} if rules_b else {}
        
        all_rule_names = set(rules_a_dict.keys()) | set(rules_b_dict.keys())
        
        for rule_name in all_rule_names:
            rule_a = rules_a_dict.get(rule_name)
            rule_b = rules_b_dict.get(rule_name)
            
            if rule_a and rule_b:
                # Compare rule properties
                rule_fields = [
                    ("enabled", "Enabled"),
                    ("blocker", "Blocker"),
                    ("message", "Message"),
                    ("minLength", "Min Length"),
                    ("maxLength", "Max Length"),
                    ("min", "Min Value"),
                    ("max", "Max Value"),
                    ("pattern", "Regex Pattern"),
                    ("useDefaultBlockList", "Use Default Block List"),
                    ("domainBlockList", "Domain Block List")
                ]
                
                for field_name, display_name in rule_fields:
                    value_a = getattr(rule_a, field_name, None)
                    value_b = getattr(rule_b, field_name, None)
                    
                    if value_a != value_b:
                        differences.append(PropertyDiff(
                            field_name=f"Validation '{rule_name}' {display_name}",
                            portal_a_value=value_a,
                            portal_b_value=value_b,
                            status=ComparisonStatus.DIFFERENT
                        ))
            
            elif rule_a and not rule_b:
                differences.append(PropertyDiff(
                    field_name=f"Validation Rule '{rule_name}'",
                    portal_a_value=self._format_validation_rule(rule_a),
                    portal_b_value=None,
                    status=ComparisonStatus.ONLY_IN_A
                ))
            
            elif rule_b and not rule_a:
                differences.append(PropertyDiff(
                    field_name=f"Validation Rule '{rule_name}'",
                    portal_a_value=None,
                    portal_b_value=self._format_validation_rule(rule_b),
                    status=ComparisonStatus.ONLY_IN_B
                ))
        
        return differences
    
    def _format_validation_rule(self, rule) -> str:
        """Format validation rule for display"""
        parts = []
        if rule.minLength is not None:
            parts.append(f"Min: {rule.minLength}")
        if rule.maxLength is not None:
            parts.append(f"Max: {rule.maxLength}")
        if rule.pattern:
            parts.append(f"Pattern: {rule.pattern}")
        if rule.min is not None:
            parts.append(f"Min: {rule.min}")
        if rule.max is not None:
            parts.append(f"Max: {rule.max}")
        if not rule.enabled:
            parts.append("Disabled")
        if rule.blocker:
            parts.append("Blocker")
        
        return ", ".join(parts) if parts else "Rule exists"