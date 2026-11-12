# Portable Pantry: project context (IT 326 Software Design Principles, Team A)

This summary is the current source of truth. The full class list, with every attribute and method, is `docs/Portable_Pantry_Class_List_v3.pdf` (43 classes). Older class lists and the Lucidchart diagram are out of date.

## Project

This is a recipe web app for a class and will never be released. The course goal is software that follows design principles and uses design patterns only where they are needed, written in object-oriented Python.

Stack:
- Flask backend. The plain HTML/CSS/JS frontend is served by Flask from `../frontend`.
- Supabase for the database, auth, and user information.
- Ollama for recipe generation. TheMealDB for searching existing recipes.
- Guests get a temporary, unsaved `User`, `UserProfile`, and `Pantry`.

## How the app works

1. **Generate:** the user enters ingredients and filters, and Ollama generates recipes.
2. **Search:** the user searches TheMealDB by ingredients, not by name. TheMealDB's free filter-by-ingredient call takes one ingredient at a time and returns only the name, thumbnail, and id. The searcher calls it once per ingredient, counts matches, then fetches full details for the best candidates, with a cap on the number of calls. This behavior comes from third-party descriptions, so verify it on the official site.
3. `PantryIngredientFilter(available, maxMissing)` keeps recipes missing at most `maxMissing` ingredients, sorted with the fewest missing first.
4. TheMealDB has no calorie, difficulty, or spice data, so those three filters only work on Ollama recipes.

## Professor rules (Deliverable 2 feedback)

- No `RegisteredUser`, `CompletedRecipe`, or `GuestUser` classes, and no `registered` flag.
- `User` has no methods. Logic goes in service classes.
- Getters and setters are assumed. Pass values through constructors instead of using setters.
- All methods need typed parameters and return types.
- `AuthService` associates with `User`, not `UserProfile`.
- `Ingredient` has no allergy flags.
- The design needs controllers and persistence.
- The repo must be made public. Check git history for secrets first.
- Use a design pattern so recommendation sources can be swapped (Ollama, AllRecipes, BBC).
- **Do not use the Strategy pattern.** The user said this explicitly.

## Layering

Controller → Service → Repository → Supabase. Controllers never call repositories. Dependencies are injected through constructors.

## Class design (43 classes)

### Domain classes

These hold data only: private attributes, read-only properties, and values set through the constructor.
- `User(userId, username, email, profile)`. Whether to keep `passwordHash` is undecided, because Supabase Auth can handle passwords.
- `UserProfile(displayName, pantry)`
- `Pantry(savedIngredients, favoriteIngredients, allergies, dietaryRestrictions, savedRecipes, completedRecipes)`
- `Ingredient(ingredientId, name, category, quantity, unit)`
- `Allergy(allergyId, name)` and `DietaryRestriction(restrictionId, name)`
- `Recipe(recipeId, title, description, category, source, servings, calories?, difficulty?, spiceLevel?, ingredients, steps)`. Cuisine, prep time, cook time, and images were removed.
- `RecipeStep(stepNumber, instructionText)`
- `RecipeRating(user, recipe, stars)`
- `PersonalNote(user, recipe, noteText, updatedAt)`
- `RecipeQuery(ingredients, filters, portionSize)`. `keyword` was removed now that search is by ingredient.

### Filters

Abstract `Filter` with `apply(recipes): List<Recipe>`. Each subclass takes its values through the constructor: `AllergyFilter`, `DietaryRestrictionFilter`, `FoodCategoryFilter`, `CalorieFilter`, `DifficultyFilter`, `SpiceLevelFilter`, `PantryIngredientFilter`. The cook time and cuisine filters were removed.

### Recipe sources

Both implementations convert external data into `Recipe` (Adapter pattern).
- Interface `RecipeGenerator` with `generateRecipes(query: RecipeQuery): List<Recipe>`, implemented by `OllamaRecipeGenerator`.
- Interface `RecipeSearcher` with `searchByIngredients(ingredients: List<Ingredient>): List<Recipe>`, implemented by `MealDbRecipeSearcher`. Its private helpers are `filterByIngredient(name): List<String>`, `lookupRecipe(id): Recipe`, and `toRecipe(json)`.

### Factories

The professor wanted two factories.
- `RecipeGeneratorFactory.createGenerator(type: String): RecipeGenerator`, used by `RecommendationService`.
- `APIFactory.createSearcher(type: String): RecipeSearcher`, used by `RecipeService`.
- `FilterFactory.createFilters(settings: Map<String,Object>, pantry: Pantry): List<Filter>`

### Services

- `RecommendationService`: `generateRecipes(query)`, `regenerateRecipes(query, shown)`
- `RecipeService`: `searchRecipes(ingredients: List<Ingredient>)`, `filterRecipes(recipes, filters)`, `getRecipe(recipeId)`, `scaleRecipe(recipe, servings)`
- `UserRecipeService`: save, remove, rate, note, mark completed, share, get saved, get completed
- `IngredientService`: add, remove, edit, get, mark and unmark favorite
- `ProfileService`, `AuthService`, `AccountService`

### Repositories

`UserRepository`, `PantryRepository`, `RecipeRepository`, and `UserRecipeRepository`, all sharing one `DatabaseManager` (the single Supabase connection; it replaces the earlier `SupabaseClient` name). The team chose to keep separate repositories rather than one large database class.

### Controllers

`AuthController`, `AccountController`, `RecipeController`, `UserRecipeController`, `PantryController`. These replace `IngredientController` and `RecommendationController` from the Lucidchart diagram. `PortionCalculator` was dropped in favor of `RecipeService.scaleRecipe`.

### Patterns

The design uses Factory, Adapter, Repository, and dependency injection. Filters use inheritance and the recipe sources use interfaces. These are structurally similar to Strategy but are not labeled Strategy.

Still open: whether to keep the polymorphic `Filter` hierarchy and the source interfaces as plain inheritance, or flatten the filters into one `FilterService`.

## UML arrows

| Relationship | Line | Arrowhead |
| --- | --- | --- |
| Inheritance | solid | hollow triangle at the parent |
| Realization (implements) | dashed | hollow triangle at the interface |
| Composition | solid | filled diamond at the whole |
| Aggregation | solid | hollow diamond at the whole |
| Association | solid | open arrow at the class being used |
| Dependency | dashed | open arrow at the class depended on |

Each factory has dashed «creates» arrows to its interface and to its concrete class. Each service has a solid association to its factory.

## Code status

- All 11 domain classes are done in `backend/models/` (snake_case attributes, read-only properties, no setters). `Recipe` constructor order: `recipe_id, title, description, category, source, servings, calories, difficulty, spice_level, ingredients, steps`.
- TheMealDB search works end to end: `sources/recipe_searcher.py` (`RecipeSearcher` ABC), `sources/meal_db_recipe_searcher.py`, `factories/api_factory.py`, `services/recipe_service.py`, and `GET /api/recipes/search?ingredients=a,b` in `routes/recipes.py`. `app.py` builds the objects and injects them. Verified against the live API: filter.php matches exact ingredient names only (so the searcher also tries the singular/plural form), and passing several ingredients in one call returns nothing on the free key. TheMealDB has no servings, so `DEFAULT_SERVINGS = 4`. Recipe ids are `mealdb-<idMeal>`.
- `repositories/recipe_repository.py` is TEMPORARY in-memory storage with the final public methods. Swap its internals to Supabase once the tables exist.
- Generation still uses the old `OllamaClient` + `DatabaseMngr`; `get_recipe` checks `RecipeService` first, then the legacy store.
- Tests live in `backend/tests/`. Run `pytest` from `backend/` (`pytest.ini` sets the import path).
- `backend/services/databaseMngr.py` is a temporary in-memory dictionary and will be replaced by `DatabaseManager` and the repositories.
- `backend/services/ollamaClient.py` has the pydantic schema, `build_prompt`, and `request_recipes`, with cuisine and cook time removed. It should be refactored into `OllamaRecipeGenerator`. Make `steps` and `ingredients` use `Field(min_length=1)` so empty lists trigger a retry.
- The older procedural `routes/*.py` and `frontend/index.html`, `login.html`, and `recipe.html` must be replaced or refactored to the controller/service design.

## Known fixes already applied

- Blueprint `url_prefix` needs a leading slash (`"/api/recipes"`).
- `Config.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")`. The `OLLAMA_KEy` typo was fixed.
- Generated recipes must be saved, or the "Recipe not found" error appears.
- Use one cloned repo folder (via GitHub Desktop), not a ZIP copy.
- Put the Supabase secret key only in `backend/.env`. Never commit it or put it in the frontend.

## Next steps

1. ~~Write the remaining domain classes.~~ Done.
2. Write the filters, sources, factories, services, repositories, and controllers.
3. Decide on the Supabase Auth question and design the tables, including a user-to-recipe link table.
4. Clean up `index.html` and `recipe.html`: remove the cook time and cuisine controls, and change the name search to ingredient search.
5. Update the SRS:
   - Split Manage Account into Edit Account, Reset Account (extends Edit Account), and Delete Account.
   - Remove the Cook Time and Cuisine filter use cases and renumber.
   - Change Search Recipe to search by ingredients.
   - Fix the pre/post-condition wording ("profile", "list").
   - Add TheMealDB.
6. Update the use case and activity diagrams: remove the Rate and Filter diagrams, and add Search by Ingredients.
7. Update the Lucidchart class diagram to match the v3 class list, and rewrite sections 4.3.1 and 4.3.2.1 for the 43-class design.
8. Make the repo public. `backend/.env.txt` was removed from tracking and `.gitignore` now covers `.env.*`, but the file is still in git history (since commit `71b2034`). Rotate any real keys that were in it before going public, and optionally scrub history with `git filter-repo`.
