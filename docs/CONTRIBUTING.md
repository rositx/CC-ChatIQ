# Contributing to OpenDesk ChatIQ

Thank you for your interest in contributing to OpenDesk ChatIQ! We welcome contributions from the community to help make our open-source customer support platform even better.

## Development Workflow

1. **Fork the Repository**: Create a personal fork on GitHub.
2. **Clone the Fork**: Clone it locally on your computer:
   ```bash
   git clone https://github.com/your-username/OpenDesk-ChatIQ.git
   cd OpenDesk-ChatIQ
   ```
3. **Install Dependencies**: OpenDesk ChatIQ is a monorepo managed with npm workspaces. Install all packages and root dependencies:
   ```bash
   npm install
   ```
4. **Create a Feature Branch**: Use descriptive branch names:
   ```bash
   git checkout -b feature/your-awesome-feature
   ```

## Repository Guidelines & Clean Code Standards

We maintain a strict code style to ensure code readability and reliability. Please adhere to the following rules:
- **Clean Architecture & Decoupling**: Do not import database context (`storage/db.py`) or SQLAlchemy ORM structures directly inside routes or business logic. All database updates and queries must go through repository instances (`repositories/session.py`, `repositories/message.py`).
- **Function Length**: Keep Python functions short and focused. No function should exceed 40 lines.
- **File Length**: Keep files modular. Files should not exceed 200 lines.
- **Type Annotations**: Provide type annotations for all new Python functions and TypeScript components.

## Testing and Verification

Before submitting a Pull Request, run the test suites to ensure everything works:
- **Backend Tests**:
  ```bash
  python -m pytest
  ```
- **Frontend Builds**:
  ```bash
  npm run build:all
  ```

## Code of Conduct

Be respectful and constructive in all communication, including issues, pull requests, and code reviews.
