#!/usr/bin/env python3
"""Banana Claude -- shared pricing tables and cost lookup.

Single source of truth for per-model / per-resolution image pricing, imported
by both batch.py and cost_tracker.py so batch estimates and logged costs cannot
drift apart when prices change.
"""

# Cost per image in USD (approximate, based on ~1,290 output tokens).
PRICING = {
    "gemini-3.1-flash-image-preview": {"512": 0.020, "1K": 0.039, "2K": 0.078, "4K": 0.156},
    "gemini-2.5-flash-image": {"512": 0.020, "1K": 0.039},
}
DEFAULT_PRICING_MODEL = "gemini-3.1-flash-image-preview"
BATCH_DISCOUNT = 0.5  # Batch API gets a 50% discount.
VALID_RESOLUTIONS = {"512", "1K", "2K", "4K"}


def is_known_model(model):
    """Whether a model has pricing (exact or partial match)."""
    return model in PRICING or any(key in model or model in key for key in PRICING)


def model_pricing(model):
    """Return the pricing map for a model, falling back to the default model."""
    pricing = PRICING.get(model)
    if pricing:
        return pricing
    for key in PRICING:
        if key in model or model in key:
            return PRICING[key]
    return PRICING[DEFAULT_PRICING_MODEL]


def lookup_cost(model, resolution, batch=False):
    """Cost for a single image at model+resolution, optionally batch-discounted."""
    pricing = model_pricing(model)
    cost = pricing.get(resolution, pricing.get("1K", 0.039))
    if batch:
        cost *= BATCH_DISCOUNT
    return cost
