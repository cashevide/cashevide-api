# Cashevide API 🚀

Cashevide API is an open-source initiative built to ensure payment security and client transparency for freelancers. Powered by Python and the Django REST Framework, it provides a robust backend system for managing freelance operations securely and efficiently.

## 🌟 Key Features

### 🔐 User Authentication & Management

* Secure, multi-platform JWT-based login.
* Comprehensive profile and account management.

### 💬 Transparent Review System

* Allows freelancers to post and manage reviews for business clients.
* Uses pre-defined tags (e.g., *'Good Service'*, *'High Price'*) to help the freelancer community make informed decisions.

### 🤝 Client Management

* Dedicated space to add, edit, and track personal clients.
* Easily monitor and manage clients used for generating invoices.

### 📦 Service & Product Catalog

* Maintain a customized catalog of products or services.
* Built-in usage limit tracking to monitor offerings efficiently.

### 🧾 Advanced Invoicing System

* Complete workflow to generate professional invoices.
* Add specific invoice items, track payment records, and monitor outstanding due balances.

### ☁️ Scalable Cloud Integrations

* **Caching:** Redis for lightning-fast caching and performance.
* **Email Delivery:** AWS SES for reliable, secure email communication.
* **Media Storage:** Cloudflare R2 / AWS S3 for secure, scalable media and file storage.

### 📄 PDF Generation Ready

* Configured with **WeasyPrint** to dynamically generate and export professional, high-quality PDF invoices.

## 🛠️ Tech Stack

* **Backend Framework:** Django & Django REST Framework (DRF)
* **Language:** Python
* **Database:** PostgreSQL
* **Caching & Queue:** Redis
* **Cloud Storage:** Cloudflare R2 / AWS S3
* **Mailing Service:** AWS SES
* **PDF Engine:** WeasyPrint
