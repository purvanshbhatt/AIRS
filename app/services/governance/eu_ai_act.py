"""
EU AI Act: first risk classification of an AI system from the owner's answers.

Regulation (EU) 2024/1689. Everything here is a fixed rule: the same answers
always give the same class and the same list of duties, and no language model
is involved.

What this is not: a legal opinion or a conformity assessment. ResilAI does not
verify the answers. A "high-risk" or "prohibited" result should be confirmed
by a lawyer before anyone relies on it.
"""

from typing import Any, Dict, List

ROLES: Dict[str, str] = {
    "deployer": "We use a system that someone else built",
    "provider": "We built it, or we supply it under our own name",
}

# (answer key, article, plain wording)
PROHIBITED_PRACTICES = (
    ("manipulation", "Article 5(1)(a)",
     "It uses hidden or manipulative techniques that change a person's behaviour and can cause them serious harm"),
    ("exploits_vulnerability", "Article 5(1)(b)",
     "It exploits a person's age, disability, or social or economic situation in a way that can cause serious harm"),
    ("social_scoring", "Article 5(1)(c)",
     "It scores people on their social behaviour or personal traits, leading to unfair treatment"),
    ("crime_prediction", "Article 5(1)(d)",
     "It predicts that a person will commit a crime from profiling or personality traits alone"),
    ("face_scraping", "Article 5(1)(e)",
     "It builds a face recognition database by scraping images from the internet or CCTV"),
    ("workplace_emotion", "Article 5(1)(f)",
     "It infers the emotions of staff at work or of students in education (medical and safety uses excepted)"),
    ("biometric_sensitive", "Article 5(1)(g)",
     "It sorts people by biometric data to infer race, political opinions, religion, union membership or sexual orientation"),
    ("realtime_biometric_id", "Article 5(1)(h)",
     "It identifies people remotely and in real time in public places for law enforcement"),
)

HIGH_RISK_AREAS = (
    ("biometrics", "Annex III(1)",
     "Remote biometric identification, sorting people by sensitive traits from biometric data, or emotion recognition"),
    ("critical_infrastructure", "Annex III(2)",
     "A safety part of critical digital infrastructure, road traffic, or water, gas, heating or electricity supply"),
    ("education", "Annex III(3)",
     "Decides admission, grades students, sets the level of education a person gets, or watches for cheating in tests"),
    ("employment", "Annex III(4)",
     "Recruits or screens job applicants, or decides promotion, dismissal, task allocation or performance review of staff"),
    ("essential_services", "Annex III(5)",
     "Decides who gets public benefits or healthcare services, scores creditworthiness, prices life or health insurance, "
     "or triages emergency calls or emergency patients"),
    ("law_enforcement", "Annex III(6)",
     "Used by or for law enforcement, for example to weigh evidence or the risk of offending"),
    ("migration", "Annex III(7)",
     "Used by or for authorities in migration, asylum or border control"),
    ("justice_democracy", "Annex III(8)",
     "Used by or for a court to research or apply the law, or meant to influence how people vote"),
)

REGULATED_PRODUCT = (
    "regulated_product", "Article 6(1) and Annex I",
    "It is, or is a safety part of, a regulated product that needs a third-party conformity assessment, "
    "such as a medical device",
)

TRANSPARENCY_TRIGGERS = (
    ("talks_to_people", "Article 50(1)",
     "People interact with it directly, for example a chatbot or a voice assistant"),
    ("generates_content", "Article 50(2)",
     "It generates text, images, audio or video"),
    ("emotion_or_biometric_categorisation", "Article 50(3)",
     "It recognises emotions or sorts people into categories from biometric data"),
    ("deepfake", "Article 50(4)",
     "It creates or alters images, audio or video of real people, places or events that look authentic, "
     "or writes text published to inform the public"),
)

# Article 6(3): an Annex III system is not high-risk when it only plays a limited role.
LIMITED_ROLE = (
    "limited_role", "Article 6(3)",
    "It only does a narrow procedural or preparatory task, improves work a person already finished, "
    "or flags patterns for a person to review, and it does not replace or steer the human decision",
)
PROFILES_PEOPLE = (
    "profiles_people", "Article 6(3)",
    "It profiles individual people: it uses personal data to evaluate or predict things about a person",
)
PUBLIC_SERVICE = (
    "public_service", "Article 27",
    "We are a public body, or we provide a public service such as publicly funded healthcare",
)

ANSWER_KEYS = frozenset(
    key for key, _, _ in (
        *PROHIBITED_PRACTICES, *HIGH_RISK_AREAS, *TRANSPARENCY_TRIGGERS,
        REGULATED_PRODUCT, LIMITED_ROLE, PROFILES_PEOPLE, PUBLIC_SERVICE,
    )
)

RISK_LABELS = {
    "prohibited": "Prohibited practice",
    "high": "High-risk",
    "limited": "Limited risk: transparency duties",
    "minimal": "Minimal risk",
}

OBLIGATION_STATUSES = ("not_answered", "in_place", "not_in_place")

DISCLAIMER = (
    "First classification from your own answers. ResilAI has not verified them. "
    "This is not legal advice: have a lawyer confirm a high-risk or prohibited result."
)


def questionnaire() -> Dict[str, Any]:
    """The questions, in the order they are asked. Served to the page so wording has one home."""
    def options(items):
        return [{"key": key, "article": article, "text": text} for key, article, text in items]

    return {
        "regulation": "Regulation (EU) 2024/1689",
        "scope_note": (
            "The Act applies if you are in the EU, or if what the system produces is used in the EU."
        ),
        "roles": [{"key": key, "text": text} for key, text in ROLES.items()],
        "sections": [
            {"id": "prohibited", "title": "Banned practices", "article": "Article 5",
             "help": "Tick any that describe what the system does.",
             "options": options(PROHIBITED_PRACTICES)},
            {"id": "high_risk", "title": "High-risk uses", "article": "Article 6 and Annex III",
             "help": "Tick any area the system is used in.",
             "options": options((*HIGH_RISK_AREAS, REGULATED_PRODUCT))},
            {"id": "exception", "title": "How much the system decides", "article": "Article 6(3)",
             "help": "Only matters if you ticked a high-risk use.",
             "options": options((LIMITED_ROLE, PROFILES_PEOPLE, PUBLIC_SERVICE))},
            {"id": "transparency", "title": "Transparency", "article": "Article 50",
             "help": "Tick any that apply.",
             "options": options(TRANSPARENCY_TRIGGERS)},
        ],
        "statuses": list(OBLIGATION_STATUSES),
        "disclaimer": DISCLAIMER,
    }


def _ticked(answers: Dict[str, Any], items) -> List[tuple]:
    return [item for item in items if answers.get(item[0]) is True]


def _duty(duty_id: str, article: str, title: str, detail: str, duty_of: str = "you") -> Dict[str, str]:
    return {"id": duty_id, "article": article, "title": title, "detail": detail, "duty_of": duty_of}


_AI_LITERACY = _duty(
    "ai_literacy", "Article 4", "AI literacy",
    "Make sure the staff who use or run the system understand it well enough for their job.",
)

_DEPLOYER_HIGH_RISK = (
    _duty("use_as_instructed", "Article 26(1)", "Use it as instructed",
          "Use the system the way the provider's instructions for use say."),
    _duty("human_oversight", "Article 26(2)", "Human oversight",
          "Give oversight to named people who have the training and the authority to override the system."),
    _duty("input_data", "Article 26(4)", "Input data",
          "Where you control the input data, make sure it is relevant for what the system is meant to do."),
    _duty("monitor_and_report", "Article 26(5)", "Monitor and report",
          "Watch how the system runs. If it presents a risk, tell the provider and stop using it. "
          "Report a serious incident."),
    _duty("keep_logs", "Article 26(6)", "Keep the logs",
          "Keep the logs the system produces for at least six months."),
    _duty("tell_staff", "Article 26(7)", "Tell your staff",
          "If you use it at work as an employer, tell the affected staff and their representatives first."),
    _duty("dpia", "Article 26(9)", "Data protection impact assessment",
          "Use the provider's information to carry out a data protection impact assessment where GDPR requires one."),
    _duty("tell_people", "Article 26(11)", "Tell the people affected",
          "Tell people that a high-risk AI system is used to make, or help make, decisions about them."),
    _duty("explain_decisions", "Article 86", "Explain decisions",
          "On request, give a person a clear explanation of the system's part in a decision that affects them."),
)

_PROVIDER_HIGH_RISK = (
    _duty("risk_management", "Article 9", "Risk management system",
          "Run a documented risk management process for the whole life of the system."),
    _duty("data_governance", "Article 10", "Data governance",
          "Train, validate and test on data that meets the Act's quality criteria."),
    _duty("technical_documentation", "Article 11", "Technical documentation",
          "Write and keep up to date the technical documentation before the system goes on the market."),
    _duty("record_keeping", "Article 12", "Automatic logging",
          "Build the system so it records events automatically over its lifetime."),
    _duty("instructions_for_use", "Article 13", "Instructions for use",
          "Give deployers clear instructions, including the system's limits and how to oversee it."),
    _duty("oversight_by_design", "Article 14", "Human oversight by design",
          "Design the system so people can oversee it, understand it and stop it."),
    _duty("accuracy_security", "Article 15", "Accuracy, robustness and cybersecurity",
          "Reach and declare an appropriate level of accuracy, robustness and cybersecurity."),
    _duty("quality_management", "Article 17", "Quality management system",
          "Run a documented quality management system."),
    _duty("conformity_assessment", "Article 43", "Conformity assessment",
          "Complete the conformity assessment before the system goes on the market or into service."),
    _duty("declaration_and_marking", "Articles 47 and 48", "EU declaration and CE marking",
          "Draw up the EU declaration of conformity and affix the CE marking."),
    _duty("registration", "Article 49", "Registration",
          "Register the system in the EU database before it goes on the market."),
    _duty("post_market_monitoring", "Article 72", "Post-market monitoring",
          "Collect and review how the system performs after it is in use."),
    _duty("incident_reporting", "Article 73", "Serious incident reporting",
          "Report serious incidents to the market surveillance authority."),
)


def _transparency_duties(role: str, answers: Dict[str, Any]) -> List[Dict[str, str]]:
    duties: List[Dict[str, str]] = []
    if answers.get("talks_to_people") is True:
        if role == "provider":
            duties.append(_duty("tell_users_ai", "Article 50(1)", "Say it is an AI",
                                "Design the system so people are told they are dealing with an AI."))
        else:
            duties.append(_duty("tell_users_ai", "Article 50(1)", "Say it is an AI",
                                "This is your supplier's duty. Check that people are told they are dealing with an AI.",
                                duty_of="supplier"))
    if answers.get("generates_content") is True:
        if role == "provider":
            duties.append(_duty("mark_generated_content", "Article 50(2)", "Mark generated content",
                                "Mark what the system generates as artificial, in a machine-readable way."))
        else:
            duties.append(_duty("mark_generated_content", "Article 50(2)", "Mark generated content",
                                "This is your supplier's duty. Check that generated content is marked as artificial.",
                                duty_of="supplier"))
    if answers.get("emotion_or_biometric_categorisation") is True and role == "deployer":
        duties.append(_duty("tell_people_exposed", "Article 50(3)", "Tell the people exposed",
                            "Tell people that emotion recognition or biometric categorisation is used on them."))
    if answers.get("deepfake") is True and role == "deployer":
        duties.append(_duty("disclose_deepfake", "Article 50(4)", "Disclose artificial content",
                            "Say clearly that the content was artificially generated or altered."))
    return duties


def classify(role: str, answers: Dict[str, Any]) -> Dict[str, Any]:
    """Return the risk class, the reasons for it, and the duties that follow.

    ``answers`` maps answer keys to booleans; a key that is absent counts as "no".
    """
    if role not in ROLES:
        raise ValueError(f"Unknown role: {role!r}")
    unknown = set(answers) - ANSWER_KEYS
    if unknown:
        raise ValueError(f"Unknown answer keys: {sorted(unknown)}")

    basis: List[Dict[str, str]] = []
    exception_note = None

    prohibited = _ticked(answers, PROHIBITED_PRACTICES)
    areas = _ticked(answers, HIGH_RISK_AREAS)
    regulated = answers.get(REGULATED_PRODUCT[0]) is True
    triggers = _ticked(answers, TRANSPARENCY_TRIGGERS)
    limited_role = answers.get("limited_role") is True
    profiles = answers.get("profiles_people") is True

    if prohibited:
        risk_class = "prohibited"
        basis = [{"article": article, "text": text} for _, article, text in prohibited]
    elif regulated or (areas and not (limited_role and not profiles)):
        risk_class = "high"
        if regulated:
            basis.append({"article": REGULATED_PRODUCT[1], "text": REGULATED_PRODUCT[2]})
        basis.extend({"article": article, "text": text} for _, article, text in areas)
        if areas and limited_role and profiles:
            basis.append({
                "article": "Article 6(3)",
                "text": "The limited-role exception does not apply because the system profiles people.",
            })
    else:
        if areas:
            # Annex III use, but the owner says the system only plays a limited role.
            exception_note = (
                "You ticked a high-risk use and said the system only plays a limited role. Under "
                "Article 6(3) that takes it out of the high-risk class, but the provider must document "
                "that assessment before the system goes on the market (Article 6(4)) and register it "
                "(Article 49(2)). Keep a written record of why the exception applies."
            )
            basis.extend({"article": article, "text": text} for _, article, text in areas)
            basis.append({"article": LIMITED_ROLE[1], "text": LIMITED_ROLE[2]})
        if triggers:
            risk_class = "limited"
            basis.extend({"article": article, "text": text} for _, article, text in triggers)
        else:
            risk_class = "minimal"
            if not areas:
                basis.append({
                    "article": "Article 6",
                    "text": "None of the banned practices, high-risk uses or transparency cases was ticked.",
                })

    if risk_class == "prohibited":
        obligations = [_duty(
            "stop_prohibited", "Article 5", "Do not use or supply it for this purpose",
            "The practice is banned in the EU. Stop, and take legal advice before any further use.",
        )]
    else:
        obligations = [_AI_LITERACY]
        if risk_class == "high":
            obligations.extend(_PROVIDER_HIGH_RISK if role == "provider" else _DEPLOYER_HIGH_RISK)
            if role == "deployer" and (
                answers.get("public_service") is True or answers.get("essential_services") is True
            ):
                obligations.append(_duty(
                    "fundamental_rights_assessment", "Article 27", "Fundamental rights impact assessment",
                    "Required before first use if you are a public body or provide a public service, "
                    "or if the system scores creditworthiness or prices life or health insurance.",
                ))
        obligations.extend(_transparency_duties(role, answers))

    return {
        "risk_class": risk_class,
        "risk_label": RISK_LABELS[risk_class],
        "basis": basis,
        "obligations": [dict(item) for item in obligations],
        "exception_note": exception_note,
        "disclaimer": DISCLAIMER,
    }
