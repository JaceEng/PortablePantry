# Portable Pantry: project context (IT 326 Software Design Principles, Team A)

This summary is the current source of truth. The class list PDF (`Portable_Pantry_Class_List_Final_v2.pdf`) is the full reference, but it still shows `searchByName` and `keyword` because it hasn't been updated for ingredient search.

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

## Class design (42 classes)

### Domain classes

These hold data only: private attributes, read-only properties, and values set through the constructor.
- `User(userId, username, email, profile)`. Whether to keep `passwordHash` is undecided, because Supabase Auth can handle passwords.
- `UserProfile(displayName, pantry)`
- `Pantry(savedIngredients, favoriteIngredients, allergies, dietaryRestrictions, savedRecipes, completedRecipes)`
- `Ingredient(ingredientId, name, category, quantity, unit)`
- `Allergy(allergyId, name)` and `DietaryRestriction(restrictionId, name)`
- `Recipe(recipeId, title, description, category, imageUrl, source, servings, calories?, difficulty?, spiceLevel?, ingredients, steps)`. Cuisine, prep time, and cook time were removed.
- `RecipeStep(stepNumber, instructionText)`
- `RecipeRating(user, recipe, stars)`
- `PersonalNote(user, recipe, noteText, updatedAt)`
- `RecipeQuery(ingredients, keyword, filters, portionSize)`. The `keyword` field is stale now that search is by ingredient.

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

`UserRepository`, `PantryRepository`, `RecipeRepository`, and `UserRecipeRepository`, all using `SupabaseClient`.

### Controllers

`AuthController`, `AccountController`, `RecipeController`, `UserRecipeController`, `PantryController`.

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

- `backend/models/pantry.py`, `recipe.py`, and `recipe_step.py` are reported as done in OO style. **As of this commit they are not in the repo** (there is no `backend/models/` folder), so they still need to be committed.
- `backend/services/ollamaClient.py` has the pydantic schema, `build_prompt`, and `request_recipes`, with cuisine and cook time removed. It should be refactored into `OllamaRecipeGenerator`. Make `steps` and `ingredients` use `Field(min_length=1)` so empty lists trigger a retry.
- The older procedural `routes/*.py` and `frontend/index.html`, `login.html`, and `recipe.html` must be replaced or refactored to the controller/service design.

## Known fixes already applied

- Blueprint `url_prefix` needs a leading slash (`"/api/recipes"`).
- `Config.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")`. The `OLLAMA_KEy` typo was fixed.
- Generated recipes must be saved, or the "Recipe not found" error appears.
- Use one cloned repo folder (via GitHub Desktop), not a ZIP copy.
- Put the Supabase secret key only in `backend/.env`. Never commit it or put it in the frontend.

## Next steps

1. Write the remaining domain classes: `User`, `UserProfile`, `Ingredient`, `Allergy`, `DietaryRestriction`.
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
7. Rewrite sections 4.3.1 and 4.3.2.1 for the 42-class design.
8. Check git history for secrets, then make the repo public. Note that `backend/.env.txt` is committed (since commit `71b2034`) and is not covered by `.gitignore`.
