
import json
import uuid

import requests
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from pydantic.alias_generators import to_camel

from config import Config

# Allowed values. Keep these the same as OPTIONS in frontend/index.html and the SRS.
COOK_METHODS = ["Baking", "Frying", "Steaming", "Grilling", "Boiling", "No-cook"]
MEAL_TYPES = ["Breakfast", "Lunch", "Dinner", "Snack", "Dessert"]
FOOD_CATEGORIES = ["Soup", "Salad", "Pasta", "Sandwich", "Casserole", "Stir-fry"]
CUISINES = ["American", "Chinese", "Indian", "Italian", "Japanese", "Mexican", "Other"]
FLAVORS = ["Sweet", "Savory", "Spicy", "Sour", "Creamy", "Crunchy"]


class OllamaError(Exception):
    """Raised when Ollama is unreachable or returns something we can't use."""


# ---- Output schema (also sent to Ollama so the model returns matching JSON) ----
class _Base(BaseModel):
    # Fields are snake_case in Python and camelCase in JSON (cookTime, spiceLevel, ...),
    # which matches what the frontend expects.
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class IngredientOut(_Base):
    name: str
    quantity: float
    unit: str  # use "" for counted items such as "3 eggs"


class StepOut(_Base):
    step_number: int
    instruction_text: str


class RecipeOut(_Base):
    # Only the fields the Recipe class keeps. Every extra field is more text
    # for the model to write, which makes generation slower.
    title: str
    description: str
    food_category: str = Field(json_schema_extra={"enum": FOOD_CATEGORIES})
    servings: int
    calories: int = Field(description="Estimated calories per serving")
    difficulty: int = Field(ge=1, le=4)
    spice_level: int = Field(ge=1, le=5)
    ingredients: list[IngredientOut] = Field(min_length=1)  # empty lists fail validation and retry
    steps: list[StepOut] = Field(min_length=1)


class RecipeBatch(_Base):
    recipes: list[RecipeOut]


def _read(source, name, default=None):
    """Read a value from a dict or from an object with attributes."""
    if isinstance(source, dict):
        return source.get(name, default)
    return getattr(source, name, default)


class OllamaClient:
    SYSTEM_MESSAGE = (
        "You are a recipe generator for a pantry app. "
        "Respond only with JSON that matches the requested schema."
    )

    # Ollama sends the reply a few words at a time (streaming), so this limit is
    # the longest wait for the NEXT piece, not for the whole reply. Loading the
    # model into memory before the first word can take a while on a laptop.
    CONNECT_TIMEOUT = 5
    READ_TIMEOUT = 180
    # Keep the model loaded between requests so later requests start faster.
    KEEP_ALIVE = "30m"
    # Upper limit on generated tokens, so a confused model can't run forever.
    MAX_TOKENS = 3000

    def __init__(self, base_url=None, model=None, timeout=READ_TIMEOUT, num_recipes=None):
        self.base_url = (base_url or Config.OLLAMA_URL).rstrip("/")
        self.model = model or Config.OLLAMA_MODEL
        self.timeout = timeout
        self.num_recipes = num_recipes or Config.OLLAMA_RECIPE_COUNT

    # ------------------------------------------------------------------
    # Prompt
    # ------------------------------------------------------------------
    def build_prompt(self, query):
        """
        Turn a recipe query into prompt text.

        `query` can be a dict like the one the frontend sends:
          {
            "ingredients": ["eggs", "spinach"],
            "filters": {"allergies": [...], "dietaryRestrictions": [...],
                        "maxCookTime": 30, "cookMethod": "Baking", "mealType": "Dinner",
                        "foodCategory": None, "cuisine": None, "flavor": None,
                        "spiceLevel": 3, "maxDifficulty": 2,
                        "minCalories": None, "maxCalories": 600},
            "servings": 2,
            "exclude": ["Titles of recipes to avoid repeating"]
          }
        or an object with the same attribute names.
        """
        ingredients = _read(query, "ingredients", []) or []
        filters = _read(query, "filters", {}) or {}
        servings = _read(query, "servings", 2) or 2
        exclude = _read(query, "exclude", []) or []

        lines = [
            f"Create {self.num_recipes} different recipes.",
            "Use mainly these ingredients: " + ", ".join(ingredients) + ".",
            "You may also assume common staples such as salt, pepper, oil, and water.",
            f"Scale every recipe to {servings} servings.",
            "Estimate calories per serving.",
            "Keep it short: a one-sentence description, at most 10 ingredients,",
            "and at most 6 steps of one or two sentences each.",
            "",
            "Requirements:",
        ]

        allergies = filters.get("allergies") or []
        if allergies:
            lines.append(
                "- Must NOT contain, or be made with anything derived from: "
                + ", ".join(allergies) + "."
            )

        restrictions = filters.get("dietaryRestrictions") or []
        if restrictions:
            lines.append("- Must follow these dietary restrictions: " + ", ".join(restrictions) + ".")

        if filters.get("maxCookTime"):
            lines.append(f"- Total cooking time of at most {filters['maxCookTime']} minutes.")
        if filters.get("cookMethod"):
            lines.append(f"- Cook method: {filters['cookMethod']}.")
        if filters.get("mealType"):
            lines.append(f"- Meal type: {filters['mealType']}.")
        if filters.get("foodCategory"):
            lines.append(f"- Food category: {filters['foodCategory']}.")
        if filters.get("cuisine"):
            lines.append(f"- Cuisine: {filters['cuisine']}.")
        if filters.get("flavor"):
            lines.append(f"- Flavor: {filters['flavor']}.")
        if filters.get("spiceLevel"):
            lines.append(f"- Spice level {filters['spiceLevel']} on a scale of 1 to 5.")
        if filters.get("maxDifficulty"):
            lines.append(f"- Difficulty of at most {filters['maxDifficulty']} on a scale of 1 to 4.")
        if filters.get("minCalories"):
            lines.append(f"- At least {filters['minCalories']} calories per serving.")
        if filters.get("maxCalories"):
            lines.append(f"- At most {filters['maxCalories']} calories per serving.")

        if lines[-1] == "Requirements:":
            lines.append("- None. Any recipe that fits the ingredients is fine.")

        if exclude:
            lines.append("")
            lines.append("Do not repeat these recipes: " + ", ".join(exclude) + ".")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Request
    # ------------------------------------------------------------------
    def request_recipes(self, prompt, temperature=0.7, attempts=2):
        """
        Send the prompt to Ollama and return a list of recipe dictionaries
        (camelCase keys, each with a generated "id").
        Retries once if the model returns JSON that doesn't match the schema.
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_MESSAGE},
                {"role": "user", "content": prompt},
            ],
            "format": RecipeBatch.model_json_schema(by_alias=True),
            "stream": True,
            "keep_alive": self.KEEP_ALIVE,
            "options": {"temperature": temperature, "num_predict": self.MAX_TOKENS},
        }

        last_problem = "unknown problem"
        for _ in range(attempts):
            try:
                content = self._stream_reply(payload)
            except requests.exceptions.ConnectionError:
                raise OllamaError(
                    f"Could not connect to Ollama at {self.base_url}. Is it running?"
                )
            except requests.exceptions.Timeout:
                raise OllamaError(
                    f"Ollama stopped responding for {self.timeout} seconds. "
                    "Check that it is still running, or try a smaller model such as llama3.2."
                )
            except requests.exceptions.HTTPError as err:
                raise OllamaError(
                    f"Ollama returned an error ({err}). "
                    f"Check that the model '{self.model}' has been pulled."
                )

            try:
                batch = RecipeBatch.model_validate_json(content)
            except (KeyError, ValueError, ValidationError) as err:
                last_problem = str(err)
                continue  # try again with the same prompt

            recipes = []
            for recipe in batch.recipes:
                data = recipe.model_dump(by_alias=True)
                data["id"] = str(uuid.uuid4())  # temporary id until recipes are stored
                recipes.append(data)
            return recipes

        raise OllamaError("The model returned invalid recipe data: " + last_problem)

    def _stream_reply(self, payload):
        """Send the request and join the streamed pieces into the full reply text.
        Each line Ollama sends is JSON like {"message": {"content": "..."}, "done": false}."""
        pieces = []
        with requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            stream=True,
            timeout=(self.CONNECT_TIMEOUT, self.timeout),
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except ValueError:
                    continue
                if chunk.get("error"):
                    raise OllamaError("Ollama reported an error: " + str(chunk["error"]))
                pieces.append((chunk.get("message") or {}).get("content", ""))
                if chunk.get("done"):
                    break
        return "".join(pieces)

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------
    def generate(self, query, temperature=0.7):
        """Build the prompt for a query and request recipes."""
        return self.request_recipes(self.build_prompt(query), temperature=temperature)

    def is_available(self):
        """True if the Ollama server answers."""
        try:
            return requests.get(f"{self.base_url}/api/tags", timeout=3).ok
        except requests.exceptions.RequestException:
            return False