"""
Labelled evaluation set: 32 queries with the agent(s) and source document that
SHOULD handle them.

Labels were written from the knowledge base, not from the system's output - the
point is to measure the system, not to ratify it. Queries deliberately use
customer phrasing ("my money hasn't come back") rather than document vocabulary
("refund timeline"), because the gap between the two is exactly what embeddings
are supposed to close and keyword search is not.

expected_agents: correct if the predicted set overlaps this set.
expected_source: the document that should appear in the retrieved chunks
                 (None = don't score retrieval for this query).
"""

EVAL_SET: list[dict] = [
    # --- billing ----------------------------------------------------------
    {"query": "How long until my money comes back after I return something?",
     "expected_agents": ["billing"], "expected_source": "refund_policy.pdf"},
    {"query": "I was charged twice for the same order",
     "expected_agents": ["billing"], "expected_source": "refund_policy.pdf"},
    {"query": "The bank took the money but I never got an order confirmation",
     "expected_agents": ["billing"], "expected_source": "refund_policy.pdf"},
    {"query": "Can I get an invoice with my company GST number on it?",
     "expected_agents": ["billing", "product"], "expected_source": "pricing.pdf"},
    {"query": "Is there a fee for cash on delivery?",
     "expected_agents": ["billing", "faq"], "expected_source": "faq.pdf"},
    {"query": "I want to cancel my annual Premium and get my money back",
     "expected_agents": ["billing"], "expected_source": "faq.pdf"},
    {"query": "The item I bought is cheaper now, can I get the difference?",
     "expected_agents": ["billing", "product"], "expected_source": "pricing.pdf"},

    # --- technical --------------------------------------------------------
    {"query": "I can't log in, it says my account is locked",
     "expected_agents": ["technical"], "expected_source": "user_manual.pdf"},
    {"query": "The password reset email never arrived",
     "expected_agents": ["technical"], "expected_source": "user_manual.pdf"},
    {"query": "Only the left earbud is playing music",
     "expected_agents": ["technical"], "expected_source": "user_manual.pdf"},
    {"query": "My smart plug won't connect to my wifi during setup",
     "expected_agents": ["technical"], "expected_source": "installation_guide.pdf"},
    {"query": "Laptop is getting very hot and the fan is loud",
     "expected_agents": ["technical"], "expected_source": "user_manual.pdf"},
    {"query": "How do I pair my earbuds to a second phone?",
     "expected_agents": ["technical"], "expected_source": "installation_guide.pdf"},
    {"query": "I keep getting a blue screen on my new NoteBook",
     "expected_agents": ["technical"], "expected_source": "user_manual.pdf"},
    {"query": "Never received the OTP to verify my number",
     "expected_agents": ["technical"], "expected_source": "installation_guide.pdf"},
    {"query": "My soundbar subwoofer light keeps blinking",
     "expected_agents": ["technical"], "expected_source": "installation_guide.pdf"},

    # --- product ----------------------------------------------------------
    {"query": "What's the difference between the Air 14 and the Pro 16?",
     "expected_agents": ["product"], "expected_source": "pricing.pdf"},
    {"query": "How much does the Pulse Buds Pro cost?",
     "expected_agents": ["product"], "expected_source": "pricing.pdf"},
    {"query": "Can I upgrade the RAM in the NoteBook Go 13?",
     "expected_agents": ["product"], "expected_source": "products.pdf"},
    {"query": "Which laptop should I buy for video editing?",
     "expected_agents": ["product"], "expected_source": "pricing.pdf"},
    {"query": "How long does standard delivery take?",
     "expected_agents": ["product"], "expected_source": "shipping_policy.pdf"},
    {"query": "Do you deliver to my pincode in Assam?",
     "expected_agents": ["product"], "expected_source": "shipping_policy.pdf"},
    {"query": "Does the SmartCam work on a 5GHz network?",
     "expected_agents": ["product", "technical"], "expected_source": "products.pdf"},
    {"query": "How long is the warranty on a smartphone charger?",
     "expected_agents": ["product", "technical"], "expected_source": "warranty.pdf"},

    # --- complaint --------------------------------------------------------
    {"query": "This is the third time I'm chasing this refund. Absolutely unacceptable.",
     "expected_agents": ["complaint"], "expected_source": "refund_policy.pdf"},
    {"query": "Your service is terrible and I want to speak to a manager",
     "expected_agents": ["complaint"], "expected_source": "refund_policy.pdf"},
    {"query": "I'm going to take this to consumer court",
     "expected_agents": ["complaint"], "expected_source": "refund_policy.pdf"},
    {"query": "Nobody has replied to my emails for a week, I'm furious",
     "expected_agents": ["complaint"], "expected_source": None},

    # --- faq --------------------------------------------------------------
    {"query": "What are your customer support hours?",
     "expected_agents": ["faq"], "expected_source": "faq.pdf"},
    {"query": "Where is your head office located?",
     "expected_agents": ["faq"], "expected_source": "faq.pdf"},
    {"query": "How do I delete my account and my data?",
     "expected_agents": ["faq"], "expected_source": "faq.pdf"},

    # --- cross-domain (the headline requirement) --------------------------
    {"query": "I paid for Premium yesterday but it's still locked",
     "expected_agents": ["billing", "technical"], "expected_source": "user_manual.pdf"},
]
