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

### Installation

```bash
# Clone the repository
git clone https://github.com/EGC-PadelHub/padel-hub.git
cd padel-hub

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Initialize database
flask db upgrade

# Run development server
flask run
```

### Running with Docker

```bash
docker-compose -f docker/docker-compose.dev.yml up
```

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

## 📄 License

This project is developed by DiversoLab / EGC-PadelHub.

## Official documentation

Full documentation will be available soon.
