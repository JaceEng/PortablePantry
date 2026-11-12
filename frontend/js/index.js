"use strict";
/* Main page. One class per piece of the screen; PantryApp at the bottom wires them together.
   Keep OPTIONS the same as the SRS and OllamaClient on the backend. */

const OPTIONS = Object.freeze({
  allergies: ["Peanuts", "Tree nuts", "Dairy", "Eggs", "Wheat", "Soy", "Fish", "Shellfish"],
  diets: ["Vegetarian", "Vegan", "Gluten-free", "Dairy-free", "Halal", "Kosher"],
  cookMethod: ["Baking", "Frying", "Steaming", "Grilling", "Boiling", "No-cook"],
  mealType: ["Breakfast", "Lunch", "Dinner", "Snack", "Dessert"],
  foodCategory: ["Soup", "Salad", "Pasta", "Sandwich", "Casserole", "Stir-fry"],
  cuisine: ["American", "Chinese", "Indian", "Italian", "Japanese", "Mexican", "Other"],
  flavor: ["Sweet", "Savory", "Spicy", "Sour", "Creamy", "Crunchy"],
  spiceLevel: ["1", "2", "3", "4", "5"],
  difficulty: ["1", "2", "3", "4"]
});

const $ = (id) => document.getElementById(id);

/* ---------- Data ---------- */

/** What gets sent to /api/recipes/generate. */
class RecipeQuery {
  constructor({ ingredients, filters, servings, exclude = [] }) {
    this.ingredients = ingredients;
    this.filters = filters;
    this.servings = servings;
    this.exclude = exclude;
  }
  withExclude(titles) { return new RecipeQuery({ ...this, exclude: titles }); }
  toJSON() {
    return { ingredients: this.ingredients, filters: this.filters, servings: this.servings, exclude: this.exclude };
  }
}

/** Talks to the recipe routes. */
class RecipeService {
  #api;
  constructor(api) { this.#api = api; }
  // A local AI model can take several minutes, so Generate waits up to 10.
  async generate(query) {
    return (await this.#api.post("/api/recipes/generate", query, { timeoutMs: 600000 })).recipes ?? [];
  }
  async search(ingredients) {
    return (await this.#api.get("/api/recipes/search", { ingredients: ingredients.join(",") })).recipes ?? [];
  }
  async refine(recipeIds, ingredients, filters) {
    return (await this.#api.post("/api/recipes/refine", { recipeIds, ingredients, filters })).recipes ?? [];
  }
  // ASSUMPTION: this route does not exist yet in the backend.
  async recommended() { return (await this.#api.get("/api/recipes/recommended")).recipes ?? []; }
}

/* ---------- Screen pieces ---------- */

class RecipeCard {
  #r;
  constructor(recipe) { this.#r = recipe; }

  #dots() {
    const level = Math.min(4, Math.max(0, Number(this.#r.difficulty) || 0));
    if (!level) return "";
    return `<span class="dots" title="Difficulty ${level} of 4">${"<i class='on'></i>".repeat(level)}${"<i></i>".repeat(4 - level)}</span>`;
  }

  html() {
    const r = this.#r, e = Html.escape;
    const label = e(r.cuisine || r.mealType || r.foodCategory || "Recipe");
    // Searched recipes (TheMealDB) have a photo; AI-generated ones get the colored band.
    const top = r.imageUrl
      ? `<div class="recipe-photo"><img src="${e(r.imageUrl)}" alt="" loading="lazy"><span>${label}</span></div>`
      : `<div class="recipe-top">${label}</div>`;
    return `
      <article class="recipe">
        ${top}
        <div class="recipe-body">
          <h3>${e(r.title || "Untitled recipe")}</h3>
          <p class="desc">${e(r.description)}</p>
          <div class="facts">
            ${r.cookTime ? `<span>${e(String(r.cookTime))} min</span>` : ""}
            ${r.calories ? `<span>~${e(String(r.calories))} cal</span>` : ""}
            ${this.#dots()}
          </div>
          ${r.id ? `<a class="btn small" href="recipe.html?id=${encodeURIComponent(r.id)}">View recipe</a>` : ""}
        </div>
      </article>`;
  }
}

/** The ingredient chips, including inline editing. */
class IngredientList {
  #items = [];
  #els;

  constructor(els) {
    this.#els = els;
    els.addBtn.addEventListener("click", () => this.#submit());
    els.input.addEventListener("keydown", (e) => { if (e.key === "Enter") this.#submit(); });
    els.list.addEventListener("click", (e) => this.#onClick(e));
    this.render();
  }

  get items() { return [...this.#items]; }

  #clean(raw) { return raw.trim().replace(/\s+/g, " "); }
  #exists(value, except = -1) {
    return this.#items.some((x, i) => i !== except && x.toLowerCase() === value.toLowerCase());
  }

  add(raw) {
    const value = this.#clean(raw);
    if (!value || this.#exists(value)) return false;
    this.#items.push(value);
    this.render();
    return true;
  }
  rename(index, raw) {
    const value = this.#clean(raw);
    if (value && !this.#exists(value, index)) this.#items[index] = value;
    this.render();
  }
  remove(index) { this.#items.splice(index, 1); this.render(); }

  #submit() {
    this.add(this.#els.input.value);
    this.#els.input.value = "";
    this.#els.input.focus();
  }

  #onClick(event) {
    const button = event.target.closest("button");
    if (!button) return;
    const index = Number(button.dataset.index);
    if (button.dataset.action === "remove") this.remove(index);
    if (button.dataset.action === "edit") this.#startEdit(button, index);
  }

  #startEdit(button, index) {
    const field = document.createElement("input");
    field.type = "text";
    field.value = this.#items[index];
    field.className = "chip-edit";
    field.setAttribute("aria-label", "Edit ingredient");
    let done = false;
    const finish = (save) => {
      if (done) return;
      done = true;
      save ? this.rename(index, field.value) : this.render();
    };
    field.addEventListener("keydown", (e) => {
      if (e.key === "Enter") finish(true);
      if (e.key === "Escape") finish(false);
    });
    field.addEventListener("blur", () => finish(true));
    button.replaceWith(field);
    field.focus();
    field.select();
  }

  render() {
    const e = Html.escape;
    this.#els.list.innerHTML = this.#items.map((name, i) => `
      <li class="chip">
        <button type="button" class="chip-text" data-action="edit" data-index="${i}" title="Click to edit">${e(name)}</button>
        <button type="button" class="chip-x" data-action="remove" data-index="${i}" aria-label="Remove ${e(name)}">&times;</button>
      </li>`).join("");
    this.#els.empty.hidden = this.#items.length > 0;
    this.#els.count.textContent = this.#items.length || "";
  }
}

/** Dropdowns, number boxes, and the two collapsible checkbox lists. */
class FilterPanel {
  static SELECTS = ["cookMethod", "mealType", "foodCategory", "cuisine", "flavor", "spiceLevel", "difficulty"];
  static NUMBERS = ["minCalories", "maxCalories", "servings"];
  #root;

  constructor(root) {
    this.#root = root;
    FilterPanel.SELECTS.forEach((id) => {
      $(id).innerHTML = `<option value="">Any</option>` +
        OPTIONS[id].map((v) => `<option value="${v}">${v}</option>`).join("");
    });
    this.#fillChecks("allergyOptions", OPTIONS.allergies, "allergy");
    this.#fillChecks("dietOptions", OPTIONS.diets, "diet");
    root.addEventListener("change", () => this.#updateBadges());
  }

  #fillChecks(id, values, name) {
    $(id).innerHTML = values
      .map((v) => `<label><input type="checkbox" name="${name}" value="${v}"><span>${v}</span></label>`)
      .join("");
  }
  #checked(name) {
    return [...this.#root.querySelectorAll(`input[name="${name}"]:checked`)].map((c) => c.value);
  }
  #number(id) {
    const raw = $(id).value.trim();
    const n = Number(raw);
    return raw === "" || !Number.isFinite(n) ? null : n;
  }
  #updateBadges() {
    $("allergyBadge").textContent = this.#checked("allergy").length || "";
    $("dietBadge").textContent = this.#checked("diet").length || "";
  }

  get servings() { return Math.max(1, this.#number("servings") || 2); }

  read() {
    const select = (id) => $(id).value || null;
    return {
      allergies: this.#checked("allergy"),
      dietaryRestrictions: this.#checked("diet"),
      cookMethod: select("cookMethod"),
      mealType: select("mealType"),
      foodCategory: select("foodCategory"),
      cuisine: select("cuisine"),
      flavor: select("flavor"),
      spiceLevel: this.#number("spiceLevel"),
      maxDifficulty: this.#number("difficulty"),
      minCalories: this.#number("minCalories"),
      maxCalories: this.#number("maxCalories")
    };
  }

  /** Returns a message if the filters don't make sense, otherwise null. */
  validate() {
    const { minCalories: lo, maxCalories: hi } = this.read();
    if ((lo !== null && lo < 0) || (hi !== null && hi < 0)) return "Calories can't be negative.";
    if (lo !== null && hi !== null && lo > hi) return "Min calories must be lower than max calories.";
    return null;
  }

  clear() {
    this.#root.querySelectorAll("input[type=checkbox]").forEach((c) => (c.checked = false));
    FilterPanel.SELECTS.forEach((id) => ($(id).value = ""));
    ["minCalories", "maxCalories"].forEach((id) => ($(id).value = ""));
    this.#updateBadges();
  }
}

/** Filters shown above search results, like a shopping site: search first, then narrow down. */
class RefinePanel {
  #els; #onChange;

  constructor(els, onChange) {
    this.#els = els;
    this.#onChange = onChange;
    this.#fillChecks(els.allergies, OPTIONS.allergies, "refineAllergy");
    this.#fillChecks(els.diets, OPTIONS.diets, "refineDiet");
    els.root.addEventListener("change", () => this.#onChange());
    els.clear.addEventListener("click", () => { this.reset(); this.#onChange(); });
  }

  #fillChecks(el, values, name) {
    el.innerHTML = values
      .map((v) => `<label><input type="checkbox" name="${name}" value="${Html.escape(v)}"><span>${Html.escape(v)}</span></label>`)
      .join("");
  }
  #checked(name) {
    return [...this.#els.root.querySelectorAll(`input[name="${name}"]:checked`)].map((c) => c.value);
  }

  /** Show the panel for a new set of search results. Categories come from the results, with counts. */
  show(recipes) {
    const counts = new Map();
    recipes.forEach((r) => { if (r.foodCategory) counts.set(r.foodCategory, (counts.get(r.foodCategory) || 0) + 1); });
    const e = Html.escape;
    this.#els.categories.innerHTML = [...counts.entries()]
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .map(([name, n]) => `<label><input type="checkbox" name="refineCategory" value="${e(name)}"><span>${e(name)} (${n})</span></label>`)
      .join("");
    this.reset();
    this.#els.root.hidden = false;
  }
  hide() { this.#els.root.hidden = true; }

  reset() {
    this.#els.root.querySelectorAll("input[type=checkbox]").forEach((c) => (c.checked = false));
    this.#els.missing.value = "";
  }

  get isEmpty() {
    const f = this.read();
    return !f.categories.length && !f.allergies.length && !f.dietaryRestrictions.length && f.maxMissing === null;
  }

  read() {
    const missing = this.#els.missing.value;
    return {
      categories: this.#checked("refineCategory"),
      allergies: this.#checked("refineAllergy"),
      dietaryRestrictions: this.#checked("refineDiet"),
      maxMissing: missing === "" ? null : Number(missing)
    };
  }

  count(shown, total) {
    this.#els.count.textContent = shown === total ? `${total} recipes` : `Showing ${shown} of ${total} recipes`;
  }
}

/** Status line + recipe grid + regenerate button. */
class ResultsView {
  #els;
  constructor(els) { this.#els = els; }

  status(message = "", isError = false) {
    this.#els.status.textContent = message;
    this.#els.status.className = isError ? "error" : "";
    this.#els.status.hidden = !message;
  }
  show(recipes, { canRegenerate = true, emptyMessage = "No recipes found. Try changing your ingredients or filters." } = {}) {
    this.#els.regenerate.hidden = !(canRegenerate && recipes.length > 0);
    if (!recipes.length) {
      this.#els.grid.innerHTML = "";
      this.status(emptyMessage);
      return;
    }
    this.status("");
    this.#els.grid.innerHTML = recipes.map((r) => new RecipeCard(r).html()).join("");
  }
  get shownTitles() { return [...this.#els.grid.querySelectorAll("h3")].map((h) => h.textContent); }
  setBusy(busy) {
    this.#els.generate.disabled = busy;
    this.#els.regenerate.disabled = busy;
  }
}

/** Top-right Menu button: Account/Log out for members, Log in/Sign up for guests. */
class MenuController {
  #button; #panel;
  constructor(button, panel, onLogout) {
    this.#button = button;
    this.#panel = panel;
    this.#panel.addEventListener("click", (e) => { if (e.target.id === "logoutBtn") onLogout(); });
    button.addEventListener("click", (e) => { e.stopPropagation(); this.#toggle(this.#panel.hidden); });
    document.addEventListener("click", () => this.#toggle(false));
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") this.#toggle(false); });
  }
  #toggle(open) {
    this.#panel.hidden = !open;
    this.#button.setAttribute("aria-expanded", String(open));
  }
  render() {
    this.#panel.innerHTML = Session.isLoggedIn
      ? `<a href="account.html">Account</a><button type="button" id="logoutBtn">Log out</button>`
      : `<a href="login.html">Log in</a><a href="signup.html">Sign up</a>`;
  }
}

/** Shows exactly one of: landing, welcome, app. */
class ScreenManager {
  static NAMES = ["landing", "welcome", "app"];
  show(name) { ScreenManager.NAMES.forEach((n) => ($(n).hidden = n !== name)); }
}

/** The login screen shown first: log in (main), create account, or continue as guest. */
class AuthScreen {
  #api; #callbacks; #mode = "login";

  constructor(api, callbacks) {
    this.#api = api;
    this.#callbacks = callbacks;
    $("loginForm").addEventListener("submit", (e) => this.#submit(e, "login"));
    $("signupForm").addEventListener("submit", (e) => this.#submit(e, "signup"));
    $("modeBtn").addEventListener("click", () => this.#setMode(this.#mode === "login" ? "signup" : "login"));
    $("guestBtn").addEventListener("click", callbacks.onGuest);
    $("showPassword").addEventListener("change", (e) => {
      $("loginPassword").type = e.target.checked ? "text" : "password";
    });
  }

  #setMode(mode, message = "") {
    this.#mode = mode;
    $("loginForm").hidden = mode !== "login";
    $("signupForm").hidden = mode !== "signup";
    $("modeBtn").textContent = mode === "login" ? "Create an account" : "Back to log in";
    this.#status(message);
    $(mode === "login" ? "loginEmail" : "signupName").focus();
  }

  #status(message = "", isError = false) {
    const el = $("authStatus");
    el.textContent = message;
    el.className = "auth-status" + (isError ? " error" : "");
    el.hidden = !message;
  }

  #read(mode) {
    const text = (id) => $(id).value.trim();
    const email = text(mode === "login" ? "loginEmail" : "signupEmail");
    const password = $(mode === "login" ? "loginPassword" : "signupPassword").value;
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return { error: "Enter a valid email address." };
    if (!password) return { error: "Enter your password." };
    if (mode === "login") return { data: { email, password } };
    const username = text("signupName");
    if (!username) return { error: "Choose a username." };
    if (password.length < 8) return { error: "Use a password of at least 8 characters." };
    return { data: { username, email, password } };
  }

  async #submit(event, mode) {
    event.preventDefault();
    const { data: credentials, error } = this.#read(mode);
    if (error) return this.#status(error, true);

    const button = event.currentTarget.querySelector("button[type=submit]");
    button.disabled = true;
    this.#status(mode === "login" ? "Logging in..." : "Creating your account...");
    try {
      const reply = await this.#api.post(`/api/auth/${mode}`, credentials);
      if (reply.access_token) {
        const user = reply.user || {};
        Session.logIn({
          token: reply.access_token,
          username: reply.username || user.username || user.name || credentials.username || credentials.email.split("@")[0]
        });
        $("loginPassword").value = "";
        $("signupPassword").value = "";
        this.#callbacks.onAuthenticated();
      } else if (mode === "signup") {
        this.#setMode("login", "Account created. Log in to continue.");
      } else {
        this.#status("The server accepted the login but sent no token.", true);
      }
    } catch (err) {
      this.#status(err.status === 404 ? "Accounts aren't available yet: the backend has no /api/auth routes." : err.message, true);
    } finally {
      button.disabled = false;
    }
  }
}

/* ---------- The app ---------- */

class PantryApp {
  #api = new ApiClient();
  #recipes = new RecipeService(this.#api);
  #screens = new ScreenManager();
  #auth = new AuthScreen(this.#api, {
    onGuest: () => { Session.startGuest(); this.#enter(); },
    onAuthenticated: () => this.start()
  });
  #ingredients = new IngredientList({
    input: $("ingredientInput"), addBtn: $("addIngredientBtn"), list: $("ingredientList"),
    empty: $("ingredientEmpty"), count: $("ingredientCount")
  });
  #filters = new FilterPanel($("filtersPanel"));
  #results = new ResultsView({
    status: $("status"), grid: $("results"), regenerate: $("regenerateBtn"), generate: $("generateBtn")
  });
  #menu = new MenuController($("menuBtn"), $("menu"), () => { Session.logOut(); location.reload(); });
  #refine = new RefinePanel({
    root: $("refine"), categories: $("refineCategories"), allergies: $("refineAllergies"), diets: $("refineDiets"),
    missing: $("refineMissing"), clear: $("refineClear"), count: $("refineCount")
  }, () => this.#refineSearch());
  #searchResults = [];     // everything the last search returned, before filters
  #searchIngredients = [];
  #lastQuery = null;
  #busy = false;
  #requestId = 0; // only the newest request may update the screen

  constructor() {
    $("generateBtn").addEventListener("click", () => this.#generate(this.#buildQuery()));
    $("regenerateBtn").addEventListener("click", () => this.#regenerate());
    $("clearFiltersBtn").addEventListener("click", () => this.#filters.clear());
    $("searchBtn").addEventListener("click", () => this.#search());
    $("searchListBtn").addEventListener("click", () => this.#search(this.#ingredients.items));
    $("searchInput").addEventListener("keydown", (e) => { if (e.key === "Enter") this.#search(); });
  }

  async start() {
    if (Session.isLoggedIn && !Session.hasWelcomed) {
      Session.markWelcomed();
      $("welcomeName").textContent = "Welcome, " + Session.username;
      this.#screens.show("welcome");
      await sleep(2500);
      this.#enter();
    } else if (Session.isLoggedIn || Session.isGuest) {
      this.#enter();
    } else {
      this.#screens.show("landing");
    }
  }

  #enter() {
    this.#screens.show("app");
    this.#menu.render();
    if (Session.isLoggedIn) this.#loadRecommended();
  }

  async #loadRecommended() {
    try {
      const recipes = await this.#recipes.recommended();
      if (!recipes.length) return;
      $("recommended").innerHTML = recipes.map((r) => new RecipeCard(r).html()).join("");
      $("recommendedPanel").hidden = false;
    } catch { /* No recommendations yet: leave the section hidden. */ }
  }

  #buildQuery() {
    return new RecipeQuery({
      ingredients: this.#ingredients.items,
      filters: this.#filters.read(),
      servings: this.#filters.servings
    });
  }

  #explain(err, fallback) {
    if (err.status === 401) { this.#menu.render(); return "Your session expired. Please log in again."; }
    return `${fallback} ${err.message}`;
  }

  async #generate(query) {
    if (this.#busy) return;
    if (!query.ingredients.length) return this.#results.status("Add at least one ingredient before generating recipes.", true);
    const problem = this.#filters.validate();
    if (problem) return this.#results.status(problem, true);

    const id = ++this.#requestId;
    this.#refine.hide();
    this.#busy = true;
    this.#results.setBusy(true);
    this.#results.status("Generating recipes with AI. This can take a minute or two...");
    try {
      const recipes = await this.#recipes.generate(query);
      if (id !== this.#requestId) return;
      this.#lastQuery = query;
      this.#results.show(recipes);
    } catch (err) {
      if (id === this.#requestId) this.#results.status(this.#explain(err, "Could not generate recipes."), true);
    } finally {
      this.#busy = false;
      this.#results.setBusy(false);
    }
  }

  #regenerate() {
    if (this.#lastQuery) this.#generate(this.#lastQuery.withExclude(this.#results.shownTitles));
  }

  /** Searches TheMealDB. Uses the search box (comma-separated), or the ingredient list if it is empty. */
  async #search(fromList) {
    const typed = $("searchInput").value.split(",").map((s) => s.trim()).filter(Boolean);
    const ingredients = fromList ?? (typed.length ? typed : this.#ingredients.items);
    if (!ingredients.length) return this.#results.status("Add or type at least one ingredient to search for.", true);
    const id = ++this.#requestId;
    this.#refine.hide();
    this.#results.status("Searching...");
    try {
      const recipes = await this.#recipes.search(ingredients);
      if (id !== this.#requestId) return;
      this.#searchResults = recipes;
      this.#searchIngredients = ingredients;
      this.#results.show(recipes, { canRegenerate: false });
      if (recipes.length) {
        this.#refine.show(recipes);
        this.#refine.count(recipes.length, recipes.length);
      }
    } catch (err) {
      if (id === this.#requestId) this.#results.status(this.#explain(err, "Search failed."), true);
    }
  }

  /** Re-filter the last search results on the server whenever a result filter changes. */
  async #refineSearch() {
    const all = this.#searchResults;
    const id = ++this.#requestId;
    if (this.#refine.isEmpty) {
      this.#results.show(all, { canRegenerate: false });
      return this.#refine.count(all.length, all.length);
    }
    try {
      const recipes = await this.#recipes.refine(all.map((r) => r.id), this.#searchIngredients, this.#refine.read());
      if (id !== this.#requestId) return;
      this.#results.show(recipes, { canRegenerate: false, emptyMessage: "No recipes match these filters. Try clearing some." });
      this.#refine.count(recipes.length, all.length);
    } catch (err) {
      if (id === this.#requestId) this.#results.status(this.#explain(err, "Could not filter the results."), true);
    }
  }
}

new PantryApp().start();