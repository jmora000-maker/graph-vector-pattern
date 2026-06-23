import re

class CorporateTaxonomyNormalizer:
    def __init__(self):
        self.blocklist = {"Actions", "Steering Committee", "Security Review", "Discussion"}
        self.identity_map = {
            "maria chen": "Maria Chen",
            "david": "David Okafor", # Map "David" to the name in your CSV
            "david okafor": "David Okafor",
            "priya": "Priya Nair", # Map "Priya" to the name in your CSV
            "priya nair": "Priya Nair",
            "helen brooks": "Helen Brooks",
            "jonas": "Jonas Weber",
            "jonas weber": "Jonas Weber",
            "fatima": "Fatima Hassan", # Map "Fatima" to the name in your CSV
            "fatima hassan": "Fatima Hassan",
            "fatima al-sayed": "Fatima Hassan"
        }

        self.concern_taxonomy = {
            "audit logging": ["audit logging", "audit log", "logging controls", "access control",
                              "security architecture"],
            "training readiness": ["training readiness", "deployment schedules", "anxieties", "frontline deployment",
                                   "enablement"],
            "support infrastructure": ["support scripts", "vendor handoff", "infrastructure targets",
                                       "enablement blockages", "scripts"]
        }


    def normalize_name(self, name: str) -> str:
        # If the name is in the blocklist, force it to return an empty string
        if name.title() in self.blocklist:
            return ""

        cleaned = str(name).strip().lower().replace("-", " ")
        cleaned = re.sub(r'[:\s*•\-\d)]', ' ', cleaned)
        cleaned = " ".join(cleaned.split())
        if not cleaned:
            return ""
        if cleaned in self.identity_map:
            return self.identity_map[cleaned]
        for alias, canonical in self.identity_map.items():
            if alias in cleaned or cleaned in alias:
                return canonical
        return name.title()

    def classify_concern(self, text: str) -> str:
        lowered = text.lower()
        for category, triggers in self.concern_taxonomy.items():
            if any(trigger in lowered for trigger in triggers):
                return category
        return "general operational friction"
