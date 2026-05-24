# 🌿 Pantry Nova

**A secure, comprehensive household food inventory and waste reduction management system** integrating smart ingredient tracking and automated shelf-life notifications into a single centralized platform.

> IGNOU BCA Final Year Project · Built with Django 4.2 + Bootstrap 5 + Google Gemini AI

---

## ✨ Features

- **Smart Inventory Tracking** — categories, quantities, expiry, storage locations
- **Color-coded Expiry System** — Red (expired) / Amber (expiring soon) / Green (fresh)
- **Auto-generated Shopping Lists** when stock runs low
- **Waste Logging** with reason tracking, cost analysis, and CO₂ impact
- **Nova AI Assistant** powered by Google Gemini (recipes, storage tips, waste reduction)
- **Multi-role access** — Admin · Kitchen Manager · Family Member
- **Household join codes** — invite family members with a 6-character code
- **Dark/Light theme** with localStorage persistence
- **Analytics & Reports** — beautiful Chart.js visualizations + PDF/CSV export
- **Email OTP Password Reset** with 3-step verification flow
- **Complaints + Feedback** system

## 🎨 Design — "Fresh Intelligence"

| Color           | Usage                              | Hex       |
| --------------- | ---------------------------------- | --------- |
| Forest Green    | Primary, sidebar, navbar           | `#1B4332` |
| Fresh Lime      | Accent, success, CTAs              | `#52B788` |
| Warm Amber      | Warning, expiring soon             | `#F4A261` |
| Expiry Red      | Danger, expired items              | `#E63946` |
| Off-White       | Background                         | `#F8F9F0` |
| Soft Mint       | Surface, hover                     | `#D8F3DC` |

Typography: **Syne** (headings) + **Outfit** (body) — Google Fonts

## 🛠️ Tech Stack

| Layer       | Technology                                              |
| ----------- | ------------------------------------------------------- |
| Backend     | Django 4.2 (no DRF — pure views/forms/templates/ORM)    |
| Database    | SQLite3                                                 |
| Frontend    | HTML5 / CSS3 / ES6+ / Bootstrap 5                       |
| Charts      | Chart.js 4                                              |
| Tables      | DataTables 1.13                                         |
| Animation   | AOS, GSAP, custom CSS                                   |
| AI          | Google Gemini (`gemini-1.5-flash` via google-generativeai) |
| Auth        | Custom session-based role authentication                |

## 📂 Project Structure

```
pantrynova/
├── pantrynova/         # Project settings, urls, utils
├── accounts/           # Login model, password reset OTP, decorators, context processors
├── admin_panel/        # Admin views: dashboard, ingredients, telemetry, complaints, feedback
├── households/         # Household model
├── managers/           # KitchenManager + manager views (inventory, expiry, etc.)
├── members/            # FamilyMember + member views (stock, consumption, etc.)
├── inventory/          # Category + PantryItem models
├── waste/              # WasteLog model + auto-CO2 signal
├── shopping/           # ShoppingList + ShoppingItem
├── complaints/         # Complaint model
├── feedback/           # Feedback model
├── chatbot/            # ChatMessage + Gemini-powered Nova AI
├── templates/          # 32 pages: public, auth, admin, manager, member, chatbot
├── static/             # css/style.css, js/main.js
├── manage.py
└── requirements.txt
```

## 🚀 Quick Start

### 1. Install Python 3.11+ dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set your GEMINI_API_KEY (optional; fallback responses work without it)
```

### 3. Initialize database & seed sample data

```bash
python manage.py migrate
python manage.py seed
```

### 4. Run the server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000/** 🌿

## 🔑 Default Login Credentials

After running `python manage.py seed`:

| Role    | Username  | Password    | URL                        |
| ------- | --------- | ----------- | -------------------------- |
| Admin   | `admin`   | `admin123`  | `/login/admin/`            |
| Manager | `manager` | `manager123`| `/login/manager/`          |
| Member  | `member`  | `member123` | `/login/member/`           |

**Member join code:** `DEMO01` (use this to register additional family members)

## 📋 All Pages

### Public (1)
- `/` — Landing with GSAP animations, hero, features, impact stats, testimonials

### Authentication (5)
- `/register/manager/`, `/login/manager/`
- `/register/member/`, `/login/member/`
- `/login/admin/`

### Password Reset (3)
- `/password-reset/` — Request OTP via email
- `/password-reset/verify/` — 6-box OTP entry with countdown
- `/password-reset/new/` — Set new password with strength meter

### Admin (6)
- `/admin/dashboard/`, `/admin/ingredients/`, `/admin/households/`, `/admin/telemetry/`, `/admin/complaints/`, `/admin/feedback/`

### Kitchen Manager (8)
- `/manager/dashboard/`, `/manager/inventory/`, `/manager/expiry-alerts/`, `/manager/shopping-list/`, `/manager/waste-log/`, `/manager/analytics/`, `/manager/family/`, `/manager/profile/`

### Family Member (8)
- `/member/dashboard/`, `/member/stock/`, `/member/log-consumption/`, `/member/alerts/`, `/member/shopping-list/`, `/member/complaints/`, `/member/feedback/`, `/member/profile/`

### AI + Error (2)
- `/chatbot/` — Nova AI Assistant
- 404 page

## 🤖 Nova AI Configuration

Edit `.env`:

```
GEMINI_API_KEY=your-actual-gemini-api-key
```

Without the key, Nova falls back to keyword-based curated responses for storage, recipes, waste reduction, and shopping queries.

## 📊 CO₂ Calculation

Waste logs auto-calculate CO₂ equivalent on save (via `pre_save` signal):

| Category   | Factor (kg CO₂ per kg food) |
| ---------- | --------------------------- |
| Meat       | 27.0                        |
| Dairy      | 3.2                         |
| Produce    | 2.0                         |
| Grains     | 1.4                         |
| Other      | 1.8                         |

## 🧪 Testing

```bash
python manage.py check
python manage.py runserver
```

All 32 pages have been smoke-tested and return correct HTTP status codes.

## 📝 License

Educational project — IGNOU BCA Final Year Submission · 2026

---

Built with 🌱 by **Anushree** · Powered by **Django** + **Google Gemini**
