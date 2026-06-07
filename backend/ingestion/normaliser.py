"""
Data normalisation module for scheme ingestion.
"""
import json
import logging
import re
from typing import Dict, Any, List


logger = logging.getLogger(__name__)


class SchemeNormaliser:
    """Normalise scheme data from various sources to standard schema."""
    
    @staticmethod
    def normalise(raw: Dict[str, Any], source: str) -> Dict[str, Any]:
        """
        Normalise scheme data from any source.
        
        Args:
            raw: Raw scheme data from source.
            source: Source identifier (data.gov.in, myscheme, jan_samarth, etc.).
        
        Returns:
            Normalised scheme data.
        """
        normalised = {
            "name": SchemeNormaliser._get_name(raw),
            "ministry": SchemeNormaliser._get_ministry(raw),
            "level": SchemeNormaliser._get_level(raw, source),
            "state": SchemeNormaliser._get_state(raw, source),
            "category": SchemeNormaliser._get_category(raw),
            "description": SchemeNormaliser._get_description(raw),
            "benefits": SchemeNormaliser._get_benefits(raw),
            "eligibility_criteria": SchemeNormaliser._normalise_eligibility(raw),
            "required_documents": SchemeNormaliser._get_documents(raw),
            "application_mode": SchemeNormaliser._get_application_mode(raw),
            "application_url": SchemeNormaliser._get_application_url(raw),
            "source_url": SchemeNormaliser._get_source_url(raw),
            "is_active": False,  # Manual activation required
        }
        
        return normalised
    
    @staticmethod
    def _get_name(raw: Dict[str, Any]) -> str:
        """Extract scheme name."""
        candidates = ["name", "scheme_name", "title", "scheme_title"]
        for key in candidates:
            if key in raw and raw[key]:
                return str(raw[key]).strip()
        return "Unknown Scheme"
    
    @staticmethod
    def _get_ministry(raw: Dict[str, Any]) -> str:
        """Extract ministry."""
        candidates = ["ministry", "ministry_name", "department"]
        for key in candidates:
            if key in raw and raw[key]:
                return str(raw[key]).strip()
        return None
    
    @staticmethod
    def _get_level(raw: Dict[str, Any], source: str) -> str:
        """Extract scheme level."""
        if "level" in raw:
            level_str = str(raw["level"]).lower()
            if "central" in level_str or "national" in level_str:
                return "central"
            elif "state" in level_str:
                return "state"
        
        # Default based on source
        if "state" in source.lower():
            return "state"
        return "central"
    
    @staticmethod
    def _get_state(raw: Dict[str, Any], source: str) -> str:
        """Extract state (for state-level schemes)."""
        if "state" in raw and raw["state"]:
            return str(raw["state"]).strip()
        
        # Extract from source if state-specific
        state_map = {
            "karnataka": "Karnataka",
            "maharashtra": "Maharashtra",
            "tamil_nadu": "Tamil Nadu",
            "uttar_pradesh": "Uttar Pradesh",
            "west_bengal": "West Bengal",
        }
        
        for key, value in state_map.items():
            if key in source.lower():
                return value
        
        return None
    
    @staticmethod
    def _get_category(raw: Dict[str, Any]) -> List[str]:
        """Extract scheme categories."""
        categories = []
        
        if "category" in raw:
            cat = raw["category"]
            if isinstance(cat, list):
                categories = cat
            else:
                categories = [str(cat).strip()]
        
        # Add categories based on content
        description = (raw.get("description", "") or "").lower()
        benefits = (raw.get("benefits", "") or "").lower()
        combined = f"{description} {benefits}"
        
        if "farmer" in combined:
            categories.append("Agriculture")
        if "student" in combined or "education" in combined:
            categories.append("Education")
        if "health" in combined or "medical" in combined:
            categories.append("Health")
        if "woman" in combined or "female" in combined or "women" in combined:
            categories.append("Women")
        if "sc" in combined or "st" in combined or "obc" in combined:
            categories.append("SC/ST/OBC")
        if "disability" in combined or "disabled" in combined:
            categories.append("Disability")
        if "senior" in combined or "elderly" in combined or "aged" in combined:
            categories.append("Senior Citizens")
        if "poor" in combined or "bpl" in combined or "ration" in combined:
            categories.append("Poverty Alleviation")
        
        return list(set(categories)) or ["General"]
    
    @staticmethod
    def _get_description(raw: Dict[str, Any]) -> str:
        """Extract scheme description."""
        candidates = ["description", "overview", "detail", "details"]
        for key in candidates:
            if key in raw and raw[key]:
                return str(raw[key]).strip()[:1000]  # Limit to 1000 chars
        return "No description available"
    
    @staticmethod
    def _get_benefits(raw: Dict[str, Any]) -> str:
        """Extract scheme benefits."""
        candidates = ["benefits", "benefit", "assistance", "grants"]
        for key in candidates:
            if key in raw and raw[key]:
                return str(raw[key]).strip()[:1000]
        return "Benefits details not specified"
    
    @staticmethod
    def _normalise_eligibility(raw: Dict[str, Any]) -> Dict[str, Any]:
        """Normalise eligibility criteria to standard JSONB format."""
        criteria = {}
        
        # Age
        if "age_min" in raw:
            criteria["age_min"] = int(raw["age_min"]) if raw["age_min"] else None
        if "age_max" in raw:
            criteria["age_max"] = int(raw["age_max"]) if raw["age_max"] else None
        
        # Parse age range from text (e.g., "18-60 years")
        if "age_range" in raw and not criteria:
            match = re.findall(r"(\d+)-(\d+)", str(raw["age_range"]))
            if match:
                criteria["age_min"] = int(match[0][0])
                criteria["age_max"] = int(match[0][1])
        
        # Gender
        if "gender" in raw and raw["gender"]:
            gender_val = str(raw["gender"]).lower()
            if "female" in gender_val or "women" in gender_val or "woman" in gender_val:
                criteria["gender"] = ["female"]
            elif "male" in gender_val:
                criteria["gender"] = ["male"]
            elif "both" in gender_val or "any" in gender_val:
                criteria["gender"] = ["male", "female", "other"]
        
        # Income
        if "income_max_annual" in raw:
            income = raw["income_max_annual"]
            if isinstance(income, str):
                income = float(re.sub(r"[^0-9]", "", income))
                # Convert lakhs to rupees if needed
                if income < 1000:
                    income *= 100000
            criteria["income_max_annual"] = int(income) if income else None
        
        # Caste
        if "caste" in raw and raw["caste"]:
            caste_str = str(raw["caste"]).upper()
            caste_list = []
            if "SC" in caste_str:
                caste_list.append("SC")
            if "ST" in caste_str:
                caste_list.append("ST")
            if "OBC" in caste_str:
                caste_list.append("OBC")
            if caste_list:
                criteria["caste"] = caste_list
        
        # BPL
        if "bpl_required" in raw:
            bpl_val = str(raw["bpl_required"]).lower()
            criteria["bpl_required"] = bpl_val in ["yes", "true", "1"]
        
        # State of residence
        if "state_of_residence" in raw and raw["state_of_residence"]:
            if isinstance(raw["state_of_residence"], list):
                criteria["state_of_residence"] = raw["state_of_residence"]
            else:
                criteria["state_of_residence"] = [str(raw["state_of_residence"])]
        
        # Land holding
        if "land_holding_max_acres" in raw:
            criteria["land_holding_max_acres"] = float(raw["land_holding_max_acres"]) if raw["land_holding_max_acres"] else None
        
        # Custom rules (unmapped narrative conditions)
        custom_rules = raw.get("custom_rules", [])
        if isinstance(custom_rules, str):
            custom_rules = [custom_rules]
        if custom_rules:
            criteria["custom_rules"] = custom_rules
        
        return criteria
    
    @staticmethod
    def _get_documents(raw: Dict[str, Any]) -> List[str]:
        """Extract required documents."""
        candidates = ["required_documents", "documents", "document_requirement"]
        for key in candidates:
            if key in raw and raw[key]:
                docs = raw[key]
                if isinstance(docs, list):
                    return docs
                elif isinstance(docs, str):
                    # Split comma-separated documents
                    return [d.strip() for d in docs.split(",")]
        return []
    
    @staticmethod
    def _get_application_mode(raw: Dict[str, Any]) -> str:
        """Extract application mode."""
        if "application_mode" in raw:
            mode = str(raw["application_mode"]).lower()
            if "online" in mode:
                return "online"
            elif "offline" in mode:
                return "offline"
            elif "csc" in mode:
                return "csc"
        return None
    
    @staticmethod
    def _get_application_url(raw: Dict[str, Any]) -> str:
        """Extract application URL."""
        candidates = ["application_url", "url", "apply_url", "application_link"]
        for key in candidates:
            if key in raw and raw[key]:
                return str(raw[key]).strip()
        return None
    
    @staticmethod
    def _get_source_url(raw: Dict[str, Any]) -> str:
        """Extract source URL."""
        candidates = ["source_url", "url", "source_link"]
        for key in candidates:
            if key in raw and raw[key]:
                return str(raw[key]).strip()
        return None
