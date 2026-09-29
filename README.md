# RMS & Warranty Management System

A unified service desk operations platform built with **Django** for managing **Repair Jobs (RMS)**, **Warranty Claims**, **Client Assets/Machines**, and **Executive Reporting** with built-in **Bikram Sambat (BS) Nepali Date** support and **Role-Based Access Control (RBAC)**.

---

## 🚀 Key Features

### 1. 🛠️ Repair Management System (RMS)
- **Intake Logging**: Record incoming machines with client info, brand/model, serial number, problem description, and intake date. Auto-generates unique sequential job numbers (`RMS-000001`).
- **Exit & Completion**:
  - **Completed**: Record technician, delivery challan number, solution details, collection contact, and exit date.
  - **Not Repaired (Returned)**: Specialized workflow for unrepairable units; dynamically adjusts required fields.
- **Delayed Repair Alerts**: Automatically highlights pending tickets older than 3 business days (Saturday-aware calculation).
- **Receipts & Exports**: Download printable single-ticket PDF receipts or multi-record tabular PDF reports with custom filters.

### 2. 🛡️ Warranty Claim Tracking
- **Claim Intake**: Log incoming warranty items with vendor/distributor sourcing (`bought_from`), delivery notes (`delivered_by`), and issue logs (`WAR-000001`).
- **Claim Lifecycle**: Track claim approval (*Pending Review*, *Approved*, *Rejected*) and resolution outcome (*Solved*, *Not Solved* with cause description).
- **PDF Slips**: Generates both Customer Drop-off Slips and Distributor Claim Slips.

### 3. 👥 Client & Machine Asset Registry
- **Flexible Profiles**: Support for corporate accounts (Company Name) and walk-in individuals (Contact Person) with either/or validation.
- **Machine Tracking**: Manage client-owned devices with unique serial numbers.
- **Quick-Add Modals**: Seamless asynchronous AJAX creation of clients and machines directly inside intake forms without losing form state.

### 4. 🇳🇵 Bikram Sambat (BS) Nepali Calendar Integration
- Automatic bi-directional AD ↔ BS date conversion across the entire system.
- Formats dates as Nepali months and years (e.g., *Shrawan 21, 2083*).
- Integrated across UI tables, ticket details, search results, and PDF documents.

### 5. 🔐 Role-Based Access Control (RBAC)
- **Repair Desk**: Access strictly partitioned to Repair intake, exit, edit, list, and PDF reporting.
- **Warranty Desk**: Access partitioned to Warranty intake, exit, edit, list, and PDF reporting.
- **Management / CEO**: Read-only KPI overview dashboard, turnaround metrics, monthly throughput charts, universal search, audit activity logs, and cross-department report exports.

### 6. 📄 Advanced Tabular PDF Reports
- Landscape tabular PDF generation using ReportLab.
- Export filtered querysets matching:
  - Date Range (*Date From* to *Date To*)
  - Status (*Pending*, *Completed*, *Not Repaired*, *Approved*, *Rejected*)
  - Client / Account
  - Serial Number (S/N)

---

## 🛠️ Tech Stack

- **Backend**: Python 3.13+, Django 6.0+
- **Database**: SQLite (default / development)
- **PDF Generation**: ReportLab 5.0+
- **Frontend**: Custom responsive CSS with modern design tokens, vanilla JavaScript (zero heavy frontend frameworks)
- **Environment Management**: `python-dotenv` / `python-decouple`
- **Static Assets**: WhiteNoise

---

## 📦 Installation & Setup

### 1. Clone the repository
```bash
git clone <repository-url>
cd rms_warranty
```

### 2. Create and activate virtual environment
```bash
python -m venv venv

# On Linux / macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory (or use default development settings):
```env
DEBUG=True
SECRET_KEY=your-secure-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 5. Run Database Migrations
```bash
python manage.py migrate
```

### 6. Create Superuser / Staff Accounts
```bash
python manage.py createsuperuser
```

To assign staff roles, log into the Django Admin (`/admin/`) and assign users to the appropriate groups:
- `Repair Desk`
- `Warranty Desk`
- `Management`

### 7. Run the Development Server
```bash
python manage.py runserver
```
Access the application at `http://127.0.0.1:8000/`.

---

## 🧪 Running Tests

Execute the automated test suite:
```bash
python manage.py test
```

---

## 📁 Project Structure

```text
rms_warranty/
├── config/                  # Django project configuration & settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── service/                 # Core application
│   ├── migrations/          # Database migrations
│   ├── static/              # CSS stylesheets, icons, fonts
│   ├── templates/           # Django HTML templates
│   │   ├── registration/    # Authentication & login views
│   │   └── service/         # Dashboards, repair/warranty forms, lists, tickets
│   ├── templatetags/        # Custom template filters (Nepali date tags, etc.)
│   ├── forms.py             # ModelForms & validation logic
│   ├── models.py            # Client, Machine, RepairJob, WarrantyClaim, ActivityLog
│   ├── nepali_date.py       # AD ↔ BS Nepali calendar conversion engine
│   ├── pdf_utils.py         # ReportLab receipt & tabular report generators
│   ├── tests.py             # Unit test suite
│   ├── urls.py              # Application route definitions
│   └── views.py             # View controllers & permission decorators
├── manage.py
├── requirements.txt
└── README.md
```

---

## 📄 License
Internal proprietary software for **Global Link Technology Pvt. Ltd.** All rights reserved.
