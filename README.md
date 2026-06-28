# Steam Store Clone

A Steam-inspired Game Store System with budget filtering, age verification, and wallet management.

## Installation

Install Flask

```bash
pip install flask
```

Run

```bash
python app.py
```

Open

```
http://127.0.0.1:5000
```

## Features

- Home Page with featured discounted games
- Browse & Search Game Store
- Filter by Genre and Budget
- Game Detail Page
- Age Verification on Checkout
- Wallet Balance Management
- Purchase History (Library)

## How It Works

1. On the Home Page, enter your **name**, **wallet balance (RM)**, and **age** to set up your account.
2. Browse the **Store** — filter games by keyword, genre, or maximum budget.
3. Click **View** on any game to see full details, then **Add to Cart & Buy**.
4. At **Checkout**, confirm your age (system blocks purchase if under the game's age rating).
5. If your wallet has enough balance, the purchase goes through and the game is added to your **Library**.

## Project Structure

```
Steam_Project/
├── app.py                  # Flask backend (routes + logic)
├── games.json              # Game catalog data
├── README.md
├── static/
│   └── style.css           # Steam dark theme CSS
└── templates/
    ├── base.html           # Base layout with navbar
    ├── index.html          # Home page
    ├── store.html          # Browse / filter games
    ├── detail.html         # Game detail page
    ├── checkout.html       # Age verification + purchase
    ├── success.html        # Purchase confirmation
    └── library.html        # Owned games
```
