"""Insurance plans offered in the dropdown. Fictional, same ids as the frontend's demo data.

Plans are only echoed back as `planName` for now: the checks compare against CGHS
reference rates, not insurer-specific tariffs.
"""
PLANS = [
    {"id": "demo-basic", "name": "Demo Shield Basic (fictional)"},
    {"id": "demo-family", "name": "Demo CareFirst Family Floater (fictional)"},
    {"id": "demo-senior", "name": "Demo Senior Secure Plus (fictional)"},
]


def plan_name(plan_id: str) -> str:
    return next((p["name"] for p in PLANS if p["id"] == plan_id), "Selected plan")
