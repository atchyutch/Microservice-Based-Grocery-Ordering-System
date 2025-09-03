# 🛒 Microservice-Based Grocery Ordering System

This project demonstrates a **microservices architecture** for a grocery ordering platform, built with **Flask**, containerized using **Docker**, and orchestrated with **docker-compose**.  
Each service is modular, runs in its own container, and communicates via REST APIs.

---

## 📂 Project Structure
Microservice-Based-Grocery-Ordering-System/
│── logs/
│ ├── app.py
│ ├── Dockerfile.logs
│ └── logs.sql
│
│── orders/
│ ├── app.py
│ └── Dockerfile.order
│
│── products/
│ ├── app.py
│ ├── Dockerfile.products
│ └── products.sql
│
│── search/
│ ├── app.py
│ └── Dockerfile.search
│
│── users/
│ ├── app.py
│ ├── Dockerfile.users
│ └── user.sql
│
│── compose.yaml
│── project3 schema.pdf


## ⚙️ Services

- **Users Service** → manages user accounts (signup, login, details)
- **Orders Service** → handles grocery orders
- **Products Service** → manages product catalog
- **Logs Service** → records and monitors activity
- **Search Service** → provides search/filter functionality

---

## 🛠 Tech Stack

- **Backend:** Python (Flask)
- **Databases:** SQLite (can be swapped with MySQL/Postgres)
- **Containerization:** Docker, docker-compose
- **Orchestration:** Multi-container setup
- **Other:** REST APIs, SQL schema files

---

## 🚀 Getting Started
docker-compose up --build

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/Microservice-Based-Grocery-Ordering-System.git
cd Microservice-Based-Grocery-Ordering-System
