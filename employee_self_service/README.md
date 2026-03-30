### Employee Self Service Portal

A self-service portal for employees to view their HR information — leave balances, attendance, payslips, holidays, and certificate requests.

### Requirements

- **Frappe** v16+ (required)
- **ERPNext** (required — provides Employee, Company, Salary Slip, Attendance, and Holiday doctypes)
- **HRMS** (recommended — provides Leave Application, Leave Allocation, and leave balance calculation. Without HRMS, leave features will show an error message.)

### Installation

Install using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch main
bench install-app employee_self_service
```

### Building Frontend

After installation or after making frontend changes:

```bash
cd apps/employee_self_service/frontend
yarn install
yarn build
```

Then run `bench build --app employee_self_service` to copy assets.

### Features

- **Dashboard** — Quick overview of leave balance, recent leaves, and upcoming holidays
- **Leave Management** — View balance, apply for leave, track application status
- **Attendance** — Monthly attendance calendar view
- **Payslips** — View salary slips with earnings/deductions breakdown
- **Holidays** — Company holiday calendar
- **Certificates** — Request employment/salary/experience certificates

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/employee_self_service
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
