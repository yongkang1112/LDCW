from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "steam_secret_key_2026"  # Required for session

GAMES_FILE = "games.json"

def load_games():
    """Load all games from games.json"""
    with open(GAMES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_final_price(game):
    """Calculate final price after discount"""
    if game["discount"] > 0:
        return round(game["price"] * (1 - game["discount"] / 100), 2)
    return game["price"]


def get_cart_games():
    """Return the game objects currently stored in the cart session."""
    cart_ids = session.get("cart", [])
    all_games = load_games()
    return [g for g in all_games if g["id"] in cart_ids]


# ============================
# Home Page
# ============================
@app.route("/")
def home():
    games = load_games()
    # Show discounted games as "featured"
    featured = [g for g in games if g["discount"] > 0][:3]
    return render_template("index.html", featured=featured)


# ============================
# Setup Account (wallet + age)
# ============================
@app.route("/setup", methods=["POST"])
def setup():
    username = request.form.get("username", "").strip()
    wallet_str = request.form.get("wallet", "")
    age_str = request.form.get("age", "")

    # --- Input validation ---
    if len(username) < 2:
        flash("Username must be at least 2 characters.", "error")
        return redirect(url_for("home"))

    try:
        wallet = float(wallet_str)
        if wallet < 0:
            raise ValueError
    except ValueError:
        flash("Please enter a valid wallet amount.", "error")
        return redirect(url_for("home"))

    try:
        age = int(age_str)
        if age < 1 or age > 120:
            raise ValueError
    except ValueError:
        flash("Please enter a valid age.", "error")
        return redirect(url_for("home"))

    # Save to session
    session["username"] = username
    session["wallet"] = wallet
    session["age"] = age
    session["library"] = []  # List of owned game IDs
    session["cart"] = []  # List of game IDs in the cart

    flash(f"Welcome, {username}! Your wallet: RM {wallet:.2f}", "success")
    return redirect(url_for("store"))


# ============================
# Logout
# ============================
@app.route("/logout")
def logout():
    username = session.get("username", "Guest")
    session.clear()
    flash(f"You have been logged out, {username}. See you next time!", "success")
    return redirect(url_for("home"))


# ============================
# Store (Browse + Filter)
# ============================
@app.route("/store")
def store():
    keyword = request.args.get("keyword", "")
    genre = request.args.get("genre", "")
    budget_str = request.args.get("budget", "")

    all_games = load_games()
    result = []

    for g in all_games:
        final_price = get_final_price(g)

        # Filter by keyword
        keyword_ok = keyword == "" or keyword.lower() in g["name"].lower()

        # Filter by genre
        genre_ok = genre == "" or genre.lower() == g["genre"].lower()

        # Filter by budget (if provided, check final price)
        if budget_str:
            try:
                budget = float(budget_str)
                budget_ok = final_price <= budget
            except ValueError:
                budget_ok = True
        else:
            budget_ok = True

        if keyword_ok and genre_ok and budget_ok:
            result.append(g)

    return render_template(
        "store.html",
        games=result,
        keyword=keyword,
        genre=genre,
        budget=budget_str
    )


# ============================
# Game Detail
# ============================
@app.route("/game/<int:game_id>")
def detail(game_id):
    games = load_games()
    game = next((g for g in games if g["id"] == game_id), None)

    if game is None:
        flash("Game not found.", "error")
        return redirect(url_for("store"))

    final_price = get_final_price(game)
    return render_template("detail.html", game=game, final_price=final_price)


# ============================
# Checkout (Age + Wallet Check)
# ============================
@app.route("/checkout/<int:game_id>", methods=["GET", "POST"])
def checkout(game_id):
    # Check if user is set up
    if "wallet" not in session:
        flash("Please set up your account first.", "error")
        return redirect(url_for("home"))

    games = load_games()
    game = next((g for g in games if g["id"] == game_id), None)

    if game is None:
        flash("Game not found.", "error")
        return redirect(url_for("store"))

    library = session.get("library", [])
    if game_id in library:
        flash(f"You already own '{game['name']}'!", "error")
        return redirect(url_for("library"))

    final_price = get_final_price(game)

    if request.method == "POST":
        age_str = request.form.get("age", "")

        # --- Validation 1: Age input ---
        try:
            age = int(age_str)
            if age < 1 or age > 120:
                raise ValueError
        except ValueError:
            flash("Please enter a valid age.", "error")
            return render_template("checkout.html", game=game, final_price=final_price)

        # Update session age
        session["age"] = age

        # --- Validation 2: Age restriction check ---
        if game["age_rating"] > 0 and age < game["age_rating"]:
            flash(
                f"❌ Age Restriction: You must be at least {game['age_rating']} years old to purchase '{game['name']}'. "
                f"Your age: {age}.",
                "error"
            )
            return render_template("checkout.html", game=game, final_price=final_price)

        # --- Validation 3: Wallet balance check ---
        wallet = session.get("wallet", 0)
        if wallet < final_price:
            flash(
                f"❌ Insufficient Balance: Your wallet (RM {wallet:.2f}) is not enough to buy '{game['name']}' "
                f"(RM {final_price:.2f}). You need RM {final_price - wallet:.2f} more.",
                "error"
            )
            return render_template("checkout.html", game=game, final_price=final_price)

        # --- All checks passed: Process purchase ---
        session["wallet"] = round(wallet - final_price, 2)
        library.append(game_id)
        session["library"] = library

        # Generate order ID
        order_id = "STM" + datetime.now().strftime("%Y%m%d%H%M%S")

        return render_template(
            "success.html",
            game=game,
            amount_paid=final_price,
            remaining=session["wallet"],
            order_id=order_id
        )

    # GET request: show checkout page
    return render_template("checkout.html", game=game, final_price=final_price)


# ============================
# Library (Owned Games)
# ============================
@app.route("/library")
def library():
    if "library" not in session:
        flash("Please set up your account first.", "error")
        return redirect(url_for("home"))

    all_games = load_games()
    owned_ids = session.get("library", [])
    owned_games = [g for g in all_games if g["id"] in owned_ids]

    return render_template("library.html", library=owned_games)


# ============================
# Cart
# ============================
@app.route("/cart")
def cart():
    if "wallet" not in session:
        flash("Please set up your account first.", "error")
        return redirect(url_for("home"))

    cart_games = get_cart_games()
    total = round(sum(get_final_price(g) for g in cart_games), 2)
    return render_template("cart.html", cart_games=cart_games, total=total)


@app.route("/add_to_cart/<int:game_id>", methods=["POST"])
def add_to_cart(game_id):
    if "wallet" not in session:
        flash("Please set up your account first.", "error")
        return redirect(url_for("home"))

    games = load_games()
    game = next((g for g in games if g["id"] == game_id), None)

    if game is None:
        flash("Game not found.", "error")
        return redirect(url_for("store"))

    library = session.get("library", [])
    cart = session.get("cart", [])

    if game_id in library:
        flash(f"You already own '{game['name']}'!", "error")
        return redirect(url_for("library"))

    if game_id in cart:
        flash(f"'{game['name']}' is already in your cart.", "info")
        return redirect(request.referrer or url_for("store"))

    cart.append(game_id)
    session["cart"] = cart
    flash(f"Added to cart: '{game['name']}'.", "success")
    return redirect(request.referrer or url_for("store"))


@app.route("/remove_from_cart/<int:game_id>", methods=["POST"])
def remove_from_cart(game_id):
    cart = session.get("cart", [])
    if game_id in cart:
        cart.remove(game_id)
        session["cart"] = cart
        flash("Item removed from cart.", "success")
    return redirect(url_for("cart"))


@app.route("/checkout_cart", methods=["POST"])
def checkout_cart():
    if "wallet" not in session:
        flash("Please set up your account first.", "error")
        return redirect(url_for("home"))

    cart_ids = session.get("cart", [])
    if not cart_ids:
        flash("Your cart is empty.", "error")
        return redirect(url_for("cart"))

    age = session.get("age")
    if age is None:
        flash("Please set up your account first.", "error")
        return redirect(url_for("home"))

    games = load_games()
    library = session.get("library", [])
    wallet = session.get("wallet", 0)
    purchased_games = []

    for game_id in list(cart_ids):
        game = next((g for g in games if g["id"] == game_id), None)
        if game is None:
            continue

        if game_id in library:
            continue

        final_price = get_final_price(game)
        if game["age_rating"] > 0 and age < game["age_rating"]:
            flash(
                f"❌ Age Restriction: You must be at least {game['age_rating']} years old to purchase '{game['name']}'.",
                "error"
            )
            return redirect(url_for("cart"))

        if wallet < final_price:
            flash(
                f"❌ Insufficient Balance: Your wallet (RM {wallet:.2f}) is not enough to buy '{game['name']}'.",
                "error"
            )
            return redirect(url_for("cart"))

        wallet = round(wallet - final_price, 2)
        library.append(game_id)
        purchased_games.append(game)

    session["wallet"] = wallet
    session["library"] = library
    session["cart"] = []

    if purchased_games:
        order_id = "STM" + datetime.now().strftime("%Y%m%d%H%M%S")
        return render_template(
            "success.html",
            game=purchased_games[-1],
            amount_paid=sum(get_final_price(g) for g in purchased_games),
            remaining=wallet,
            order_id=order_id
        )

    flash("No new games were purchased.", "info")
    return redirect(url_for("library"))


# ============================
if __name__ == "__main__":
    app.run(debug=True)
