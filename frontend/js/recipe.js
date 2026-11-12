"use strict";
/* Recipe details page. Uses ApiClient, Session, and Html from core.js. */

const $ = (id) => document.getElementById(id);

/** The backend routes for one recipe. */
class RecipeService {
    #api; #id;
    constructor(api, id) { this.#api = api; this.#id = encodeURIComponent(id); }
    load() { return this.#api.get(`/api/recipes/${this.#id}`); }
    rate(stars) { return this.#api.post(`/api/recipes/${this.#id}/rating`, { stars }); }
    saveNote(text) { return this.#api.post(`/api/recipes/${this.#id}/note`, { text }); }
    markCompleted() { return this.#api.post(`/api/recipes/${this.#id}/completed`); }
    setSaved(saved) {
    const path = `/api/pantry/recipes/${this.#id}`;
    return saved ? this.#api.post(path) : this.#api.delete(path);
    }
}

/** Fills in the read-only parts of the page: title, facts, ingredients (scaled), steps. */
class RecipeDetail {
    #r;
    constructor(recipe) {
    this.#r = recipe;
    $("servingsInput").addEventListener("input", () => this.#renderIngredients());
    }

    static amount(quantity) {
    const n = Number(quantity);
    return n > 0 ? String(Math.round(n * 100) / 100) : "";
    }

    render() {
    const r = this.#r;
    document.title = (r.title || "Recipe") + " - Portable Pantry";
    $("title").textContent = r.title || "Untitled recipe";
    $("description").textContent = r.description || "";
    $("category").textContent = r.foodCategory || "";
    $("category").hidden = !r.foodCategory;
    // Only searched recipes (TheMealDB) have pictures. AI-generated ones don't.
    if (r.imageUrl) {
        $("image").src = r.imageUrl;
        $("image").alt = r.title || "Recipe photo";
        $("image").hidden = false;
        $("image").addEventListener("error", () => { $("image").hidden = true; });
    }
    $("estimate").textContent = r.source === "themealdb"
        ? "Recipe from TheMealDB. Always check ingredients for allergens."
        : "Recipes and calorie counts are AI-generated estimates. Always check ingredients for allergens.";
    $("meta").replaceChildren(...this.#facts());
    $("servingsInput").value = r.servings || 2;
    this.#renderIngredients();
    this.#renderSteps();
    }

    #facts() {
    const r = this.#r;
    return [
        ["Prep time", r.prepTime, " min"], ["Cook time", r.cookTime, " min"],
        ["Difficulty", r.difficulty, " of 4"], ["Calories", r.calories, " per serving (estimate)"],
        ["Spice level", r.spiceLevel, " of 5"], ["Cuisine", r.cuisine], ["Meal type", r.mealType],
        ["Cook method", r.cookMethod], ["Flavor", r.flavor]
    ]
        .filter(([, value]) => value !== undefined && value !== null && value !== "")
        .map(([label, value, suffix = ""]) => {
        const li = document.createElement("li");
        li.textContent = `${label}: ${value}${suffix}`;
        return li;
        });
    }

    #renderIngredients() {
    const base = this.#r.servings || 1;
    const wanted = Number($("servingsInput").value);
    const factor = wanted >= 1 ? wanted / base : 1;
    $("ingredients").replaceChildren(...(this.#r.ingredients || []).map((item) => {
        const li = document.createElement("li");
        const amount = document.createElement("span");
        amount.className = "amount";
        amount.textContent = [RecipeDetail.amount(item.quantity * factor), item.unit].filter(Boolean).join(" ");
        const name = document.createElement("span");
        name.textContent = item.name;
        li.append(amount, name);
        return li;
    }));
    }

    #renderSteps() {
    const steps = [...(this.#r.steps || [])].sort((a, b) => a.stepNumber - b.stepNumber);
    // Each step is a big numbered row the cook can tick off.
    $("steps").replaceChildren(...steps.map((step, i) => {
        const li = document.createElement("li");
        const label = document.createElement("label");
        label.className = "step";
        const box = document.createElement("input");
        box.type = "checkbox";
        box.setAttribute("aria-label", `Step ${i + 1} done`);
        const number = document.createElement("span");
        number.className = "step-num";
        number.textContent = String(i + 1);
        const text = document.createElement("span");
        text.className = "step-text";
        text.textContent = step.instructionText;
        label.append(box, number, text);
        li.append(label);
        return li;
    }));
    }
}

/** Save, rate, note, and completed buttons for logged-in users. */
class RecipeActions {
    #service; #saved; #pending = false;

    constructor(service, recipe) {
    this.#service = service;
    this.#saved = Boolean(recipe.saved);
    this.#buildStars();
    if (recipe.userRating) this.#showStars(recipe.userRating);
    if (recipe.userNote) $("noteInput").value = recipe.userNote;
    if (recipe.completed) this.#showCompleted();
    this.#updateSaveButton();
    $("saveBtn").addEventListener("click", () => this.#toggleSaved());
    $("completedBtn").addEventListener("click", () => this.#complete());
    $("noteBtn").addEventListener("click", () => this.#saveNote());
    }

    #status(message, isError = false) {
    $("actionStatus").textContent = message;
    $("actionStatus").className = isError ? "error" : "";
    }

  /** Runs one request at a time and reports success or the error message. */
    async #run(task, successMessage, onSuccess) {
    if (this.#pending) return;
    this.#pending = true;
    this.#status("Saving...");
    try {
        await task();
        onSuccess?.();
        this.#status(successMessage);
    } catch (err) {
        this.#status(err.status === 401 ? "Your session has expired. Please log in again." : err.message, true);
    } finally {
        this.#pending = false;
    }
    }

    #buildStars() {
    const buttons = [1, 2, 3, 4, 5].map((n) => {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = "\u2605";
        button.setAttribute("aria-label", n + (n === 1 ? " star" : " stars"));
        button.addEventListener("click", () => this.#rate(n));
        return button;
    });
    $("stars").replaceChildren(...buttons);
    }

    #showStars(count) {
    $("stars").querySelectorAll("button").forEach((button, i) => {
        button.classList.toggle("on", i < count);
        button.setAttribute("aria-pressed", String(i + 1 === count));
    });
    }

    #updateSaveButton() { $("saveBtn").textContent = this.#saved ? "Remove from saved recipes" : "Save recipe"; }
    #showCompleted() { $("completedBtn").textContent = "Completed \u2713"; $("completedBtn").disabled = true; }

    #rate(stars) { return this.#run(() => this.#service.rate(stars), "Rating saved.", () => this.#showStars(stars)); }
    #complete() { return this.#run(() => this.#service.markCompleted(), "Marked as completed.", () => this.#showCompleted()); }

    #saveNote() {
    const text = $("noteInput").value.trim();
    if (!text) return this.#status("Write a note before saving.", true);
    return this.#run(() => this.#service.saveNote(text), "Note saved.");
    }

    #toggleSaved() {
    const next = !this.#saved;
    return this.#run(
        () => this.#service.setSaved(next),
        next ? "Recipe saved." : "Recipe removed from your saved recipes.",
        () => { this.#saved = next; this.#updateSaveButton(); }
    );
    }
}

class RecipePage {
    #fail(message) {
    $("status").textContent = message;
    $("status").className = "error";
    }

    async start() {
    const id = new URLSearchParams(window.location.search).get("id");
    if (!id) return this.#fail("No recipe was selected. Go back and choose a recipe.");

    const service = new RecipeService(new ApiClient(), id);
    let recipe;
    try {
        recipe = await service.load();
    } catch (err) {
        return this.#fail(err.status === 404
        ? "Recipe not found. It may no longer be available."
        : "Could not load the recipe. " + err.message);
    }

    new RecipeDetail(recipe).render();
    $("status").hidden = true;
    $("recipe").hidden = false;

    if (Session.isLoggedIn) {
        $("actions").hidden = false;
        new RecipeActions(service, recipe);
    } else {
        $("guestNote").hidden = false;
        $("guestLoginBtn").addEventListener("click", () => { Session.logOut(); window.location.href = "index.html"; });
    }
    }
}

new RecipePage().start();