from enum import Enum

class DepartmentType(str, Enum):
    """Core standard departments in the organization."""
    SALES = 'sales'
    MARKETING = 'marketing'
    OPERATIONS = 'operations'
    FINANCE = 'finance'
    HR = 'hr'
    IT = 'it'
    CONTACT_CENTER = 'contact_center'
    BUSINESS_EFFICIENCY = 'business_efficiency'
    SOFTWARE_DEVELOPMENT = 'software_development'
    CLOUD_AND_AUTOMATION = 'cloud_and_automation'
    ARTIFICIAL_INTELLIGENCE = 'artificial_intelligence'

def get_all_departments() -> list[str]:
    return [dept.value for dept in DepartmentType]
