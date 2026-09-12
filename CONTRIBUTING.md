# Contributing to LifeConnect

Thank you for your interest in contributing to LifeConnect! We welcome contributions from everyone. By participating in this project, you agree to abide by our code of conduct and best practices.

## How Can I Contribute?

### Reporting Bugs
If you find a bug, please create an issue on GitHub. Include as much information as possible:
- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Your environment (browser, OS, etc.)

### Suggesting Enhancements
We are always open to new ideas. If you have a feature request or an enhancement idea, please create an issue explaining the motivation and how it would work.

### Code Contributions
1. **Fork the repository** and create your branch from `main`.
2. **Set up the project locally** by following the instructions in `docs/setup.md`.
3. **Make your changes**. 
   - Follow the established code style (PEP 8 for Python, ESLint/Prettier for JavaScript).
   - Write clear, concise commit messages.
   - Add or update tests as appropriate.
4. **Run the tests** (if applicable) to ensure nothing is broken.
5. **Issue a Pull Request (PR)**. Ensure the PR description clearly describes the problem and solution.

## Development Guidelines

### Backend (FastAPI)
- **Dependency Management:** We use `uv` for managing Python dependencies. Ensure `pyproject.toml` is updated if you add new packages.
- **Routing:** API routes should be placed in `app/api/v1/`.
- **Database:** Use SQLAlchemy for models and Alembic for migrations. If you change a model in `app/models/`, run `alembic revision --autogenerate -m "description"` to create a migration script.
- **Authentication:** Endpoints meant only for admins or donors should use the respective dependency guards (`get_current_admin`, `get_current_donor`).

### Frontend (React/Vite)
- **Components:** Place reusable components in `src/components/`.
- **Pages:** Top-level views should go in `src/pages/`.
- **Styling:** We use standard CSS (or modular CSS). Ensure class names are descriptive.
- **API Calls:** All external requests should go through the central API service in `src/services/api.js`. Do not hardcode URLs in components.

## Getting Help
If you need help with your contribution, feel free to ask questions in the issue or PR comments. We are happy to help!
