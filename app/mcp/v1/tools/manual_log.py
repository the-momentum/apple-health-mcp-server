from typing import Any

from fastmcp import FastMCP

from app.schemas.manual_log import FuelingCategory
from app.services.health.manual_logs import log_fueling_event as _log_fueling_event
from app.services.health.manual_logs import search_fueling_events as _search_fueling_events

manual_log_router = FastMCP(name="Manual Log MCP")


@manual_log_router.tool
def log_fueling_event(
    product_name: str,
    category: FuelingCategory,
    brand: str | None = None,
    quantity: str | None = None,
    shop_url: str | None = None,
    calories: float | None = None,
    carbs_g: float | None = None,
    sodium_mg: float | None = None,
    caffeine_mg: float | None = None,
    notes: str | None = None,
    logged_at: str | None = None,
) -> dict[str, Any]:
    """
    Log a single fueling event (a sports drink, gel, bar, chew, or food item
    the user consumed during a ride/workout) to the manual logs database.

    Parameters:
    - product_name: Name of the product, e.g. "Maurten Gel 100" (required).
    - category: One of "drink_mix", "gel", "bar", "chew", "real_food", "other".
    - brand: Brand/manufacturer name, if known.
    - quantity: Freeform amount, e.g. "1 gel", "500ml", "2 chews".
    - shop_url: A link to the product's shop/info page, if the user gave one.
    - calories, carbs_g, sodium_mg, caffeine_mg: Nutrition facts for the amount
      actually consumed, if known.
    - notes: Freeform notes, e.g. "felt great", "GI distress".
    - logged_at: ISO8601 timestamp of when it was consumed. Defaults to now
      if not given — pass this explicitly when the user is logging something
      that happened earlier (e.g. mid-ride, after the fact).

    Notes for LLMs:
    - If the user gives a shop_url, try to fetch the page first and extract
      calories/carbs_g/sodium_mg/caffeine_mg from the product's nutrition
      facts before calling this tool.
    - IMPORTANT - Do not guess, autofill, or assume any nutrition values.
      If they can't be determined from the page, pass them as null (omit
      them) rather than guessing — store the shop_url so they can be looked
      up later instead.
    """
    try:
        return _log_fueling_event(
            product_name=product_name,
            category=category,
            brand=brand,
            quantity=quantity,
            shop_url=shop_url,
            calories=calories,
            carbs_g=carbs_g,
            sodium_mg=sodium_mg,
            caffeine_mg=caffeine_mg,
            notes=notes,
            logged_at=logged_at,
        )
    except Exception as e:
        return {"error": f"Failed to log fueling event: {str(e)}"}


@manual_log_router.tool
def search_fueling_events(
    date_from: str | None = None,
    date_to: str | None = None,
    category: FuelingCategory | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Search previously logged fueling events from the manual logs database.

    Parameters:
    - date_from, date_to: Optional ISO8601 date strings to filter by logged_at.
    - category: Optional filter by one of "drink_mix", "gel", "bar", "chew",
      "real_food", "other".
    - limit: Maximum number of events to return (default 50), most recent first.

    Notes for LLMs:
    - Use this to pull fueling history for a ride, a day, or a reporting
      period (e.g. for a weekly report's nutrition/fueling section).
    - If there are multiple databases available (DuckDB, Elasticsearch), this
      tool only ever reads from the manual logs database — it is independent
      of which health-data backend the user picked.
    """
    try:
        return _search_fueling_events(
            date_from=date_from,
            date_to=date_to,
            category=category,
            limit=limit,
        )
    except Exception as e:
        return [{"error": f"Failed to search fueling events: {str(e)}"}]
