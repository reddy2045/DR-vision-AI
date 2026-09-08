# DR Vision AI — PHC Diabetic Retinopathy Screening System

A Django-based Primary Health Centre (PHC) web application for automated diabetic retinopathy (DR) screening using a MATLAB ResNet-18 deep learning model.

---

## Features

- 🔬 **AI-Powered DR Screening** — ResNet-18 model classifies fundus images into 5 DR levels
- 🗺️ **Grad-CAM Visualization** — Highlights regions influencing the prediction
- 👥 **Employee Access Control** — Admin pre-approves Employee IDs; only approved IDs can register
- 📋 **Patient Management** — Record patient demographics and track screening history
- 📄 **Referral Slip Generation** — Auto-generate referral slips for referable DR cases
- 🏥 **Admin Dashboard** — Manage employees, view registrations, activate/deactivate access

---

## DR Classification Levels

| MATLAB Class | DR Level | Referral Urgency |
|---|---|---|
| No_DR | 0 | Routine |
| Mild | 1 | Routine |
| Moderate | 2 | Priority |
| Severe | 3 | Urgent |
| Proliferate_DR | 4 | Urgent |

---

## Prerequisites

- Python 3.11+
- MySQL 8.0+
- MATLAB R2026a with:
  - Deep Learning Toolbox
  - Image Processing Toolbox
  - MATLAB Engine for Python (installed from `extern/engines/python`)
- `trainedDRModel.mat` — ResNet-18 model file (not included; place separately)

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/reddy2045/DR-vision-AI.git
cd DR-vision-AI
```

### 2. Create and activate virtual environment

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install MATLAB Engine for Python

```bash
pip install "C:\Program Files\MATLAB\R2026a\extern\engines\python"
```

### 5. Configure environment variables

Copy `.env.example` to `.env` and fill in your values:

```bash
copy .env.example .env
```

Key variables to set:

```env
DB_PASSWORD=your_mysql_password
MATLAB_MODEL_PATH=C:\path\to\trainedDRModel.mat
DJANGO_SECRET_KEY=your-strong-secret-key
```

### 6. Create MySQL database

```sql
CREATE DATABASE phc_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 7. Apply migrations

```bash
python manage.py migrate
```

### 8. Create admin account

```bash
python manage.py setup_admin
```

Default admin credentials:
- **Username**: `admin`
- **Password**: `Admin@1234`

> ⚠️ Change the password immediately after first login.

### 9. Run the server

```bash
python manage.py runserver
```

Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## Admin Panel

| URL | Purpose |
|---|---|
| `/admin-login/` | Staff admin login |
| `/admin-dashboard/` | Employee ID management |
| `/admin/` | Django built-in admin |

---

## Project Structure

```
phc_screening/
├── ai_engine/
│   ├── matlab/
│   │   └── screen_fundus.m     # MATLAB screening function
│   ├── matlab_engine.py        # MATLAB Engine singleton
│   ├── predictor.py            # Python → MATLAB inference bridge
│   └── quality.py              # Image quality checks
├── phc_screening/
│   ├── settings.py
│   └── urls.py
├── screening/
│   ├── migrations/
│   ├── templates/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   └── admin.py
├── docs/
│   └── PROJECT_DOCUMENTATION.md
├── .env.example
├── manage.py
└── requirements.txt
```

---

## Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | insecure dev key | Django secret key |
| `DJANGO_ALLOWED_HOSTS` | localhost,127.0.0.1 | Comma-separated allowed hosts |
| `DB_NAME` | phc_db | MySQL database name |
| `DB_USER` | root | MySQL username |
| `DB_PASSWORD` | *(empty)* | MySQL password |
| `DB_HOST` | localhost | MySQL host |
| `DB_PORT` | 3306 | MySQL port |
| `MATLAB_MODEL_PATH` | — | Path to `trainedDRModel.mat` |
| `EMAIL_HOST_USER` | *(empty)* | SMTP email address |
| `EMAIL_HOST_PASSWORD` | *(empty)* | SMTP app password |

---

## License

Research prototype — for educational and evaluation purposes only.

> The AI model output is not a medical diagnosis. All referable results must be reviewed by a qualified ophthalmologist.
