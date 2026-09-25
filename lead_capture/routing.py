"""Authoritative, server-side industry routing and explainable qualification."""

INDUSTRIES = {
    "logistics": {"slug": "logistics-ai", "campaign": "LOGISTICS_AI", "name": "Transportation and logistics", "solutions": ["logistics_ai_platform", "dispatch_automation", "ai_receptionist"]},
    "legal": {"slug": "legal-ai", "campaign": "LEGAL_AI", "name": "Law firms and legal services", "solutions": ["legal_ai_platform", "legal_ai_receptionist", "intake_automation"]},
    "healthcare": {"slug": "healthcare-ai", "campaign": "HEALTHCARE_AI", "name": "Private healthcare", "solutions": ["healthcare_ai_platform", "patient_portal", "medical_ai_receptionist"]},
    "senior_care": {"slug": "senior-care-ai", "campaign": "SENIOR_CARE_AI", "name": "Senior care and medical transportation", "solutions": ["senior_care_ai_platform", "transportation_portal"]},
    "real_estate": {"slug": "real-estate-ai", "campaign": "REAL_ESTATE_AI", "name": "Real estate and property management", "solutions": ["real_estate_ai_platform", "showing_automation"]},
    "financial_services": {"slug": "financial-services-ai", "campaign": "FINANCIAL_AI", "name": "Financial services and insurance", "solutions": ["financial_services_ai_platform", "controlled_intake"]},
    "ecommerce": {"slug": "ecommerce-ai", "campaign": "ECOMMERCE_AI", "name": "Retail and e-commerce", "solutions": ["ecommerce_ai_platform", "shopping_assistant"]},
    "hospitality": {"slug": "hospitality-ai", "campaign": "HOSPITALITY_AI", "name": "Hotels, travel and hospitality", "solutions": ["hospitality_ai_platform", "guest_assistant"]},
    "construction": {"slug": "construction-ai", "campaign": "CONSTRUCTION_AI", "name": "Construction and home services", "solutions": ["construction_ai_platform", "field_service_automation"]},
    "agriculture": {"slug": "agriculture-ai", "campaign": "AGRICULTURE_AI", "name": "Agriculture and food production", "solutions": ["agriculture_ai_platform", "farm_management"]},
    "education": {"slug": "education-ai", "campaign": "EDUCATION_AI", "name": "Education and training", "solutions": ["education_ai_platform", "student_experience"]},
    "dental": {"slug": "dental-ai", "campaign": "DENTAL_AI", "name": "Dental practices", "solutions": ["dental_ai_platform", "dental_patient_system"]},
    "veterinary": {"slug": "veterinary-ai", "campaign": "VETERINARY_AI", "name": "Veterinary practices", "solutions": ["veterinary_ai_platform", "pet_owner_experience"]},
    "automotive": {"slug": "automotive-ai", "campaign": "AUTOMOTIVE_AI", "name": "Automotive dealerships and repair", "solutions": ["automotive_ai_platform", "automotive_operations"]},
    "restaurant": {"slug": "restaurant-ai", "campaign": "RESTAURANT_AI", "name": "Restaurants and food service", "solutions": ["restaurant_ai_platform", "guest_order_experience"]},
    "manufacturing": {"slug": "manufacturing-ai", "campaign": "MANUFACTURING_AI", "name": "Manufacturing", "solutions": ["manufacturing_ai_platform", "manufacturing_operations"]},
    "recruitment": {"slug": "recruitment-ai", "campaign": "RECRUITMENT_AI", "name": "Recruitment and human resources", "solutions": ["recruitment_ai_platform", "hiring_workflow"]},
    "nonprofit": {"slug": "nonprofit-ai", "campaign": "NONPROFIT_AI", "name": "Nonprofits and community organizations", "solutions": ["nonprofit_ai_platform", "community_operations"]},
    "public_services": {"slug": "public-services-ai", "campaign": "PUBLIC_SERVICES_AI", "name": "Government and public services", "solutions": ["public_services_ai_platform", "public_service_delivery"]},
    "energy": {"slug": "energy-ai", "campaign": "ENERGY_AI", "name": "Energy, solar and utilities", "solutions": ["energy_ai_platform", "connected_energy"]},
    "telecom_it": {"slug": "telecom-it-ai", "campaign": "TELECOM_IT_AI", "name": "Telecommunications and managed IT", "solutions": ["telecom_it_ai_platform", "support_operations"]},
    "wellness": {"slug": "wellness-ai", "campaign": "WELLNESS_AI", "name": "Beauty, wellness and fitness", "solutions": ["wellness_ai_platform", "wellness_growth"]},
    "security_services": {"slug": "security-services-ai", "campaign": "SECURITY_SERVICES_AI", "name": "Security and alarm companies", "solutions": ["security_services_ai_platform", "security_operations"]},
    "marketing_media": {"slug": "marketing-media-ai", "campaign": "MARKETING_MEDIA_AI", "name": "Marketing agencies and media", "solutions": ["marketing_media_ai_platform", "agency_workflow"]},
    "gaming_entertainment": {"slug": "gaming-entertainment-ai", "campaign": "GAMING_ENTERTAINMENT_AI", "name": "Gaming and entertainment", "solutions": ["gaming_entertainment_ai_platform", "entertainment_platform"]},
}
for _route in INDUSTRIES.values():
    _route.update(team_code="INDUSTRY_AI_SALES", source_code="CODESTRA_WEBSITE", medium_code="WEBSITE", queue_code="INDUSTRY_AI_INBOUND")

ALIASES = {item["name"].lower(): code for code, item in INDUSTRIES.items()}
ALIASES.update({item["slug"]: code for code, item in INDUSTRIES.items()})
ALIASES.update({code: code for code in INDUSTRIES})

CTA_SLA_MINUTES = {"call_codestra": 5, "request_demo": 15, "request_pricing": 30, "project_consultation": 120}

def resolve_industry(value):
    code = ALIASES.get(str(value).strip().lower().replace("-", "_")) or ALIASES.get(str(value).strip().lower())
    if not code:
        raise ValueError("unsupported_industry")
    return code, INDUSTRIES[code]

def resolve_solution(industry_code, value):
    allowed = INDUSTRIES[industry_code]["solutions"]
    return value if value in allowed else allowed[0]

def score_lead(data):
    score = 0
    reasons = []
    for condition, points, reason in [
        (bool(data.get("work_email")), 15, "business_email"),
        (bool(data.get("phone_number")), 15, "valid_phone"),
        (data.get("employee_count") not in ("", "1-10"), 10, "company_size"),
        (bool(data.get("monthly_call_volume")), 10, "monthly_volume"),
        (len(data.get("message", "").strip()) >= 20, 15, "clear_requirement"),
        (data.get("cta_clicked") in CTA_SLA_MINUTES, 20, "high_intent_cta"),
        (bool(data.get("preferred_demo_date")), 15, "demo_timing"),
    ]:
        if condition: score += points; reasons.append(reason)
    score = min(score, 100)
    classification = "nurture" if score < 30 else "marketing_qualified" if score < 60 else "sales_qualified" if score < 80 else "priority_opportunity"
    return score, classification, reasons
