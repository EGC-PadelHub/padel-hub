<div style="text-align: center;">
  <img src="app/static/img/logos/logo-dark.png" alt="Logo">
</div>

# Padelhub.io

Padelhub — a CSV-first platform focused on tabular match datasets and tools for padel match analysis. Developed by DiversoLab / EGC-PadelHub.

## 🎾 Overview

PadelHub is a specialized repository platform for padel match datasets. It validates, stores, and provides access to structured CSV files containing padel match information, enabling researchers and analysts to share and discover padel data.

## 📊 CSV Structure Requirements

All datasets uploaded to PadelHub must follow a specific CSV structure. Each CSV file represents a collection of padel matches, with each row containing information about a single match.

### Required Columns

Your CSV files must include these **21 mandatory columns** in order:

1. `nombre_torneo` - Tournament name
2. `anio_torneo` - Tournament year (YYYY)
3. `fecha_inicio_torneo` - Start date (DD.MM.YYYY)
4. `fecha_final_torneo` - End date (DD.MM.YYYY)
5. `pista_principal` - Main court/venue
6. `categoria` - Category (Masculino/Femenino/Mixed)
7. `fase` - Phase/Stage
8. `ronda` - Round type
9. `pareja1_jugador1` - Team 1 - Player 1
10. `pareja1_jugador2` - Team 1 - Player 2
11. `pareja2_jugador1` - Team 2 - Player 1
12. `pareja2_jugador2` - Team 2 - Player 2
13. `set1_pareja1` - Set 1 Team 1 score
14. `set1_pareja2` - Set 1 Team 2 score
15. `set2_pareja1` - Set 2 Team 1 score
16. `set2_pareja2` - Set 2 Team 2 score
17. `set3_pareja1` - Set 3 Team 1 score (optional)
18. `set3_pareja2` - Set 3 Team 2 score (optional)
19. `pareja_ganadora` - Winning team
20. `pareja_perdedora` - Losing team
21. `resultado_string` - Match result string

### Example CSV

```csv
nombre_torneo,anio_torneo,fecha_inicio_torneo,fecha_final_torneo,pista_principal,categoria,fase,ronda,pareja1_jugador1,pareja1_jugador2,pareja2_jugador1,pareja2_jugador2,set1_pareja1,set1_pareja2,set2_pareja1,set2_pareja2,set3_pareja1,set3_pareja2,pareja_ganadora,pareja_perdedora,resultado_string
Madrid Premier Padel P1 2024,2024,02.09.2024,08.09.2024,Wizink Center,Femenino,Final,Cuadro,Ariana Sánchez Fallada,Paula Josemaría Martín,Beatriz González,Delfina Brea,6,4,7,5,,,Ariana Sánchez Fallada_Paula Josemaría Martín,Beatriz González_Delfina Brea,6-4 / 7-5
```

### Validation Rules

- **Year**: Must be numeric (1900-2100)
- **Dates**: Must follow DD.MM.YYYY format
- **Category**: Must be one of: Masculino, Femenino, Mixed
- **Player names**: Cannot be empty
- **Set scores**: Must be numeric (0-99)
- **Encoding**: UTF-8 recommended (UTF-16, Latin-1, CP1252 also supported)

See example CSV files in `app/modules/dataset/csv_examples/` for reference.

## 🚀 Features

- **Automated CSV Validation**: Ensures all uploaded files meet the required padel match structure
- **Syntax Checking**: Validates CSV syntax and encoding before acceptance
- **Rich Previews**: Display match information in an easy-to-read format
- **Multiple Export Formats**: Download datasets as CSV, JSON, XML, XLSX, TSV, YAML, or TXT
- **DOI Integration**: Permanent dataset storage with Zenodo integration
- **Dataset Metrics**: Automatic calculation of tournament and player statistics
- **Search & Discovery**: Find datasets by tournament, players, category, or date range

## 🛠️ Development

### Prerequisites

- Python 3.8+
- MariaDB/MySQL
- Docker (optional)

## 🚀 Deployment

### 🖥️ Local Development

**Requirements:** Python 3.12+, MariaDB, Virtual Environment

**Quick Start:**
```bash
# Create virtual environment (first time only)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the application
./run_local.sh
```

**Access:** http://localhost:5000

**What it does:**
- Configures `.env` from `.env.local.example`
- Stops Docker containers if running
- Frees port 5000
- Starts MariaDB if not running
- Activates virtual environment
- Installs dependencies if needed
- Verifies database connection
- Runs migrations automatically if database is empty
- Starts Flask with hot reload

---

### 🐳 Docker (Recommended)

**Requirements:** Docker & Docker Compose ([Install Docker](https://docs.docker.com/get-docker/))

**Quick Start:**
```bash
# Run the application
./run_docker.sh

# Stop the application
./stop_docker.sh
```

**Access:** http://localhost

**What it does:**
- Configures `.env` from `.env.docker.example`
- Stops local MariaDB if running
- Frees occupied ports (80, 3306, 5000, 4444)
- Stops previous containers
- Builds and starts all services
- Waits for services to be ready
- Runs migrations automatically

**Services included:**
- Flask application (port 80 via Nginx)
- MariaDB database (port 3306)
- Selenium Grid (port 4444)
- VNC Chrome (port 5900)
- VNC Firefox (port 5901)

**Useful commands:**
```bash
# View logs
docker compose -f docker/docker-compose.dev.yml logs -f web

# Access container
docker exec -it web_app_container bash

# Restart services
docker compose -f docker/docker-compose.dev.yml restart web

# Clean rebuild
docker compose -f docker/docker-compose.dev.yml down -v
docker compose -f docker/docker-compose.dev.yml build --no-cache
./run_docker.sh
```

---

### ☁️ Render.com

Deploy directly from GitHub to [Render.com](https://render.com) for production hosting

## 📝 API Documentation

Coming soon.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest app/modules/dataset/tests/test_padel_validation.py

# Run with coverage
pytest --cov=app
```

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

## 📄 Documentation

### Academic Project Documentation (`/docs`)

Complete project documentation for academic submission:

| Document | Description |
|----------|-------------|
| **[Project-Document.md](docs/Project-Document.md)** | Complete academic project documentation with team info, metrics, system architecture, and development process |
| **[Team-Diary.md](docs/Team-Diary.md)** | Team meeting records with 9 meeting summaries and project evolution timeline |
| **[Cover-Template.md](docs/Cover-Template.md)** | Project cover page with team information, repository links, and course details |
| **[CI-CD-Workflows.md](docs/CI-CD-Workflows.md)** | Detailed explanation of GitHub Actions workflows, CI/CD automation, and semantic versioning system |
| **[CONTRIBUTING.md](docs/CONTRIBUTING.md)** | Complete development workflow guide with branching strategy, commit conventions, and merge processes |
| **[CONTRIBUTING_EN_EXAMPLES.md](docs/CONTRIBUTING_EN_EXAMPLES.md)** | English examples of commit messages and merge formats for international contributors |

### Additional Technical Documentation

- **[Issue Templates](.github/ISSUE_TEMPLATE/)** - Standardized templates for bug reports, feature requests, and documentation improvements
- **[Git Hooks](.githooks/)** - Automated commit validation with installation instructions

- **[Fakenodo README](app/modules/fakenodo/README.md)** - Mock Zenodo API for development and testing
- **[CSV Errors README](app/modules/dataset/padel_csv_errors/README.md)** - Test files with validation errors for CSV structure testing

### Getting Started

1. Read the [Contributing Guide](docs/CONTRIBUTING.md)
2. Install Git hooks: `cp .githooks/commit-msg .git/hooks/commit-msg && chmod +x .git/hooks/commit-msg`
3. Configure commit template: `git config commit.template .gitmessage`
4. Create an issue using our templates
5. Follow the branch and commit workflow

### Branch Strategy

- **main** - Production code
- **trunk** - Development integration
- **bugfix** - Shared bug fixes
- **feature/*** - New features (deleted after merge)
- **document/*** - Documentation updates (deleted after merge)

## ⚠️ Production Limitations and Known Issues

### Database Reset in Production

**Issue:** Datasets uploaded by users may become inaccessible or appear empty after database resets in production.

**Root Causes:**
- **Render.com Free Tier:** The application uses Render.com's free hosting tier, which includes automatic database resets that can occur during maintenance windows or when resources are freed
- **Fakenodo Integration:** PadelHub integrates with Fakenodo (a mock Zenodo API) for development and testing purposes. In production, this can cause data inconsistency if the integration isn't properly isolated

**Impact:**
- Historical datasets uploaded by users may show as empty after a database reset
- Users won't be able to download previously uploaded CSV files
- No loss of uploaded files themselves, but metadata and database records are affected

**Recommended Solutions for Production Deployment:**
1. Upgrade to a paid Render.com tier with persistent database storage
2. Use a managed database service (e.g., AWS RDS, Azure Database for MySQL)
3. Implement database backup and restore procedures
4. Replace Fakenodo with a real Zenodo API integration for production environments
5. Implement a data persistence strategy with regular backups

**Current Development Status:**
This is a university project developed as part of a software engineering course. For production use beyond educational purposes, these infrastructure issues should be addressed with proper database management and persistent storage solutions.

## 📄 License

This project is developed by DiversoLab / EGC-PadelHub.
