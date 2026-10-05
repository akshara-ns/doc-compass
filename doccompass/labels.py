"""The one label list. Every dataset and model converts labels through this module."""

SPECIALTIES = [
    "Dermatology",
    "Orthopedics",
    "ENT",
    "Gastroenterology",
    "Neurology",
    "Urology",
    "Ob-Gyn",
    "Mental health",
    "Cardiology",
    "Eye care",
    "Dentistry",
]
GP = "Start with a GP"

# Router classes. The order fixes each label's integer id; append only.
LABELS = SPECIALTIES + [GP]
LABEL2ID = {label: i for i, label in enumerate(LABELS)}

# Used while labelling only; never router classes.
EMERGENCY = "Emergency"  # handled by the red-flag rules before the router runs
SKIP = "Skip"  # not a "which doctor" question
ANNOTATION_CHOICES = LABELS + [EMERGENCY, SKIP]
URGENCY = ["routine", "soon", "emergency"]

# What each label covers, in plain words. Shown to users and used in the labelling guideline.
SCOPE = {
    "Dermatology": "skin, hair and nails",
    "Orthopedics": "bones, joints, muscles, the back and neck, and sports injuries",
    "ENT": "ears, nose, throat and sinuses",
    "Gastroenterology": "the stomach, bowel, digestion and liver",
    "Neurology": "headaches, numbness or tingling, seizures and memory",
    "Urology": "urinary problems and male sexual or reproductive health",
    "Ob-Gyn": "periods, pregnancy and female reproductive health",
    "Mental health": "mood, anxiety, eating and addiction",
    "Cardiology": "the heart, palpitations and blood pressure",
    "Eye care": "vision and eye problems",
    "Dentistry": "teeth, gums and the mouth",
    GP: "problems with no clear single cause, and anything that normally needs a referral",
}
