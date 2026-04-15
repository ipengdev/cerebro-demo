# AMO - Antonine Maronite Order

Comprehensive ERP management for the Antonine Maronite Order covering:

- **52 Companies** across Monasteries, Schools, Universities, and Social/Cultural Organizations
- **Country-specific Chart of Accounts** (Lebanon, Canada, Australia, Belgium, Italy, Switzerland, Syria)
- **Fixed Assets** with class/location tracking, WIP assets, and depreciation
- **Project Management & Inventory**
- **Country-specific Payroll**
- **Dynamic Reporting Dashboards** for Faculty, Program Financial Visibility, Tuition & Scholarship Governance

## Installation

```bash
bench get-app amo
bench --site [sitename] install-app amo
```

## Setup

After installation, run the AMO setup wizard:
```bash
bench --site [sitename] execute amo.amo_setup.setup.execute_full_setup
```
