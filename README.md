# E-Commerce API (Django REST Framework)

Backend API for a simple e-commerce system with:

- JWT auth stored in **HttpOnly cookies**
- Product CRUD (admin)
- Cart & checkout
- Stripe PaymentIntent integration

Source idea: https://roadmap.sh/projects/ecommerce-api

---

## 🚀 Quickstart

```powershell
# clone project url
git clone https://github.com/Mohammed2372/E-Commerce-API.git
# enter project folder
cd E-Commerce-API
# create virtualenv & install dependencies
python -m venv env
& .\env\Scripts\activate
pip install -r requirements.txt
```

Create `.env`:

```
DJANGO_SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# PostgreSQL
DATABASE_NAME=
DATABASE_USER=
DATABASE_PASSWORD=
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Stripe
STRIPE_PUBLISHABLE_KEY=
STRIPE_SECRET_KEY=
```

Run:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## 💳 How to Test Stripe Payments (Manual Flow)

This flow simulates Stripe checkout using Postman (no frontend needed).

### **A. Login → Get Cookies**

```
POST http://127.0.0.1:8000/login/
Body: {"username": "admin", "password": "password"}
```

---

### **B. Add Item to Cart**

```
POST http://127.0.0.1:8000/cart/add_item/
Body: {"product_id": 1, "quantity": 2}
```

---

### **C. Checkout (Create PaymentIntent)**

```
POST http://127.0.0.1:8000/cart/checkout/
```

Response:

```json
{
  "clientSecret": "pi_3SV..._secret_...",
  "amount": 50.0
}
```

Extract PaymentIntent ID:

```
pi_3SVezgRw59upba3b0PR1pPvh
```

---

### **D. Simulate Payment (Force Stripe Confirmation)**

```
POST https://api.stripe.com/v1/payment_intents/{PAYMENT_INTENT_ID}/confirm
Auth: Bearer <STRIPE_SECRET_KEY>
Body: payment_method=pm_card_visa
```

Stripe returns `"status": "succeeded"`.

---

### **E. Confirm Payment in Django**

```
POST http://127.0.0.1:8000/cart/confirm_payment/
Body: {"payment_intent_id": "pi_3SVezgRw59upba3b0PR1pPvh"}
```

Response:

```json
{
  "message": "Payment confirmed!",
  "order": { "status": "Paid" }
}
```

---

## 🔧 Useful Commands

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
python manage.py test
```

---

# 📘 API Reference (Route Tables)

## 🔐 **Authentication**

| Method | Endpoint     | Description                   |
| ------ | ------------ | ----------------------------- |
| POST   | `/register/` | Create a new account          |
| POST   | `/login/`    | Login (sets HttpOnly cookies) |
| POST   | `/logout/`   | Logout (clears cookies)       |
| POST   | `/refresh/`  | Refresh access token          |
| GET    | `/user/`     | Get current user details      |

---

## 🛒 **Shopping Cart**

| Method | Endpoint                   | Description                         |
| ------ | -------------------------- | ----------------------------------- |
| GET    | `/cart/my_cart/`           | Get active shopping cart            |
| GET    | `/cart/`                   | List order history (paid carts)     |
| POST   | `/cart/add_item/`          | Add item to cart                    |
| POST   | `/cart/checkout/`          | Initialize Stripe PaymentIntent     |
| POST   | `/cart/confirm_payment/`   | Finalize order after Stripe success |
| POST   | `/cart/clear_active_cart/` | Empty the current active cart       |

---

## 📦 **Products**

| Method | Endpoint          | Description                 |
| ------ | ----------------- | --------------------------- |
| GET    | `/products/`      | List all products           |
| GET    | `/products/{id}/` | Get single product detail   |
| POST   | `/products/`      | Create product (admin only) |
| PUT    | `/products/{id}/` | Update product (admin only) |
| DELETE | `/products/{id}/` | Delete product (admin only) |
