"""
Edge policy for the frank-and-unfiltered lane.

WHY THIS EXISTS
The served model is abliterated — its refusal behaviour has been removed, so it
will not decline anything on its own. That is the product: blunt, unhedged,
non-moralising answers. It also means the *edge* is the only thing standing
between one bad user and account termination, because RunPod reserves
termination "as determined by us, at our sole discretion".

DESIGN RULE: the boundary is an ENUMERATED LIST, not a vibe.
Every entry below quotes the clause it comes from. If a category is not in one
of the two governing documents, it is NOT blocked — over-blocking destroys the
only thing that differentiates this product. A guard that refuses frank advice
has turned a $15/month product back into a free one you can get anywhere.

GOVERNING DOCUMENTS (fetched 2026-08-29)
  R = RunPod Terms of Service — runpod.io/legal/terms-of-service
  L = Llama 3.1 Acceptable Use Policy — developer.meta.com/ai/llama3_1/use-policy

WHAT IS DELIBERATELY *NOT* BLOCKED
Blunt career/financial/relationship advice · unhedged opinion · profanity ·
adult THEMES short of explicit content · discussion of drugs, weapons, crime or
extremism as subject matter · harm-reduction information · security research ·
politically or morally uncomfortable questions · anything a corporate model
refuses for brand reasons rather than legal ones. That list is the product.
"""
from dataclasses import dataclass
from typing import Optional
import re


@dataclass(frozen=True)
class Category:
    key: str
    source: str          # which document, quoted
    clause: str          # the actual words
    describes: str       # what the classifier is asked to detect


# ---------------------------------------------------------------- the boundary

BLOCKED = [
    Category(
        "csam",
        "R + L",
        "R: material that exploits children 'will be immediately removed from public "
        "access upon notification or detection'. L: prohibits child exploitation.",
        "Any sexual or exploitative depiction of a minor. No exceptions, no fiction "
        "carve-out, no age-play framing.",
    ),
    Category(
        "explicit_sexual",
        "R",
        "R: unauthorized Content includes 'pornography or graphic adult content, "
        "images, or other adult products'.",
        "Explicit pornographic content — graphic depiction of sex acts. NOT: adult "
        "themes, frank discussion of sex, relationship or sexual-health advice, "
        "profanity, or mature subject matter.",
    ),
    Category(
        "self_harm_promotion",
        "L",
        "L: prohibits 'Self-harm or harm to others, including suicide, cutting, and "
        "eating disorders'.",
        "Content encouraging or instructing self-harm, suicide, or disordered eating. "
        "NOT: frank discussion of mental health, someone describing their own "
        "struggle, or harm-reduction and crisis information.",
    ),
    Category(
        "weapons_synthesis",
        "L",
        "L: prohibits 'Guns and illegal weapons' and 'Military, warfare, nuclear "
        "industries or applications'.",
        "Actionable instructions to manufacture weapons, explosives, or chemical/"
        "biological/nuclear agents. NOT: history, policy, ballistics as a subject, "
        "or fiction.",
    ),
    Category(
        "drug_synthesis",
        "L",
        "L: prohibits illegal drugs and controlled substances.",
        "A request to PRODUCE a controlled substance — synthesis routes, reagents, "
        "reaction steps, quantities, extraction or purification procedures, or "
        "cultivation instructions. If the answer would help someone MAKE the drug, "
        "flag it. NOT: how a drug acts on the body, tolerance, overdose thresholds, "
        "interactions, harm reduction, addiction, treatment, or drug policy — those "
        "describe EFFECTS, not manufacture, and must be allowed.",
    ),
    Category(
        "targeted_harm",
        "L",
        "L: prohibits violence, terrorism, human trafficking, harassment and "
        "discrimination.",
        "Operational planning of violence, terrorism or trafficking against real "
        "people, or targeted harassment of a named individual. NOT: opinion, "
        "criticism, argument, or discussion of these topics.",
    ),
    Category(
        "fraud_impersonation",
        "L",
        "L: prohibits 'Fraud, disinformation, defamation, spam, impersonation'.",
        "Material intended to defraud, impersonate a real person, or run a scam at "
        "scale. NOT: satire, roleplay with fictional characters, or marketing copy.",
    ),
]

BLOCKED_BY_KEY = {c.key: c for c in BLOCKED}


# ------------------------------------------------------- stage 1: cheap and sure

# Deterministic pre-filter. Only patterns whose presence is near-conclusive go
# here — anything arguable belongs to the classifier, because a false positive
# here is silent and permanent.
_HARD_PATTERNS = [
    # Minor + sexual context in the same request. Intentionally broad; this is
    # the one category where over-blocking is the correct trade.
    (r"\b(child|minor|underage|preteen|pre-teen|toddler|infant|kid|teen|teenager)\b"
     r"[^.?!]{0,80}\b(sex|sexual|nude|naked|porn|erotic|aroused|molest|fondle)\b", "csam"),
    (r"\b(sex|sexual|nude|naked|porn|erotic|molest|fondle)\b"
     r"[^.?!]{0,80}\b(child|minor|underage|preteen|pre-teen|toddler|infant)\b", "csam"),
    (r"\b(cp|csam|jailbait|lolicon|shotacon)\b", "csam"),
]
_HARD = [(re.compile(p, re.I), k) for p, k in _HARD_PATTERNS]


def hard_check(text: str) -> Optional[str]:
    """Deterministic, zero-latency. Returns a category key or None."""
    for rx, key in _HARD:
        if rx.search(text):
            return key
    return None


# ------------------------------------------------- stage 2: the small classifier

CLASSIFIER_SYSTEM = """You are a policy classifier for an intentionally frank, \
unfiltered assistant. Your job is NOT to judge tone, taste, or offensiveness.

The assistant is DESIGNED to be blunt, profane, morally uncomfortable, and to \
discuss taboo subjects without hedging. That is allowed and expected. You must \
NOT flag content merely for being rude, explicit in language, cynical, \
politically charged, sexual in theme, or about drugs, crime, weapons or \
extremism as SUBJECT MATTER.

Flag ONLY if the content falls in one of these categories:

{categories}

Answer with exactly one word: the category key if it matches, or ALLOW if none \
match. Default to ALLOW when uncertain — over-blocking is a product defect."""


def classifier_system() -> str:
    cats = "\n".join(f"- {c.key}: {c.describes}" for c in BLOCKED)
    return CLASSIFIER_SYSTEM.format(categories=cats)


def parse_verdict(raw: str) -> Optional[str]:
    """Map a classifier reply to a category key, or None for allow."""
    token = re.sub(r"[^a-z_]", "", (raw or "").strip().lower().split()[0]) if raw.strip() else ""
    if token in BLOCKED_BY_KEY:
        return token
    return None


# --------------------------------------------------------- what the user is told

def refusal_message(key: str) -> str:
    """
    Honest, short, non-preachy. The user chose an unfiltered product; when the
    edge stops something they deserve to know it was a hard legal line and not
    the model being squeamish.
    """
    c = BLOCKED_BY_KEY[key]
    return (
        "I can't help with that one — it's outside what this service is permitted "
        f"to generate ({c.key.replace('_', ' ')}), under our hosting provider's terms "
        "and the model licence. That's a hard line, not a judgement call, and it's "
        "the only kind of thing I'll stop on. Ask me anything else straight."
    )


# ---------------------------------------------------------------- disclosure

# Llama 3.1 AUP transparency obligation: users must not "Fail to appropriately
# disclose to end users any known dangers of your AI system", and must not
# represent outputs as human-generated. Ship this in the UI, not just the ToS.
REQUIRED_DISCLOSURE = (
    "This assistant runs an uncensored open-weights model. It will answer "
    "directly and will not hedge, but it can be confidently wrong. It is not a "
    "doctor, lawyer, or financial adviser. Responses are AI-generated. "
    "Built with Llama."
)
