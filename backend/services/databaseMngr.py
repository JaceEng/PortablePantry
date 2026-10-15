class DatabaseMngr:
    def __init__(self):
        self.recipes = {}

    def save_recipes(self, recipes):
        for recipe in recipes:
            self.recipes[recipe["id"]] = recipe

    def get_recipe(self, recipe_id):
        return self.recipes.get(recipe_id)

    def search_recipes(self, name):
        return [r for r in self.recipes.values() if name.lower() in r["title"].lower()]