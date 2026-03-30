### Queue Management

Queue Management System for Frappe / ERPNext.

### Requirements

- **Frappe** v16+ (required)
- **ERPNext / HRMS** (optional — enables Employee doctype integration for staff assignment sync)

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch main
bench install-app queue_management
bench migrate
```

### Post-Installation Setup

1. Go to **QMS Settings** and configure:
   - Hospital/Organization Name
   - Default Country Code
   - Sender Email Address (or link an Email Account)
   - Enable/disable features (feedback, QR codes, online booking, etc.)
2. Create **QMS Locations**, **QMS Services**, and **QMS Counters**
3. Assign the **QMS Operator** or **Healthcare Administrator** role to users

> **Note:** If ERPNext/HRMS is installed, custom fields are automatically added to the Employee doctype for counter assignment tracking. Without ERPNext, the app works standalone — staff assignments still function, just without Employee record sync.

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/queue_management
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
