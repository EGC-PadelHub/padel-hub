"""
Tests for padel-specific CSV structure validation.
"""
import os
import tempfile
from app.modules.dataset.types.tabular import TabularDataset


def test_validate_padel_structure_valid():
    """Test validation with a valid padel match CSV structure."""
    valid_csv = (
        "nombre_torneo,anio_torneo,fecha_inicio_torneo,fecha_final_torneo,pista_principal,"
        "categoria,fase,ronda,pareja1_jugador1,pareja1_jugador2,pareja2_jugador1,pareja2_jugador2,"
        "set1_pareja1,set1_pareja2,set2_pareja1,set2_pareja2,set3_pareja1,set3_pareja2,"
        "pareja_ganadora,pareja_perdedora,resultado_string\n"
        "Madrid Premier Padel P1 2024,2024,02.09.2024,08.09.2024,Wizink Center,Femenino,Final,Cuadro,"
        "Ariana Sánchez Fallada,Paula Josemaría Martín,Beatriz González,Delfina Brea,6,4,7,5,,,"
        "Ariana Sánchez Fallada_Paula Josemaría Martín,Beatriz González_Delfina Brea,6-4 / 7-5\n"
    )
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(valid_csv)
        path = f.name

    try:
        tab = TabularDataset(None)
        result = tab.validate_padel_structure(path)
        assert result['valid'] is True
        assert 'errors' not in result or len(result.get('errors', [])) == 0
    finally:
        os.remove(path)


def test_validate_padel_structure_missing_columns():
    """Test validation fails when required columns are missing."""
    # Missing several columns
    invalid_csv = """nombre_torneo,anio_torneo,categoria
Madrid Premier Padel P1 2024,2024,Femenino
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(invalid_csv)
        path = f.name

    try:
        tab = TabularDataset(None)
        result = tab.validate_padel_structure(path)
        assert result['valid'] is False
        assert 'errors' in result
        assert len(result['errors']) > 0
        assert 'required_columns' in result
        # Check that missing columns error is reported
        error_text = ' '.join(result['errors'])
        assert 'Missing required columns' in error_text
    finally:
        os.remove(path)


def test_validate_padel_structure_invalid_year():
    """Test validation fails with invalid year format."""
    invalid_csv = (
        "nombre_torneo,anio_torneo,fecha_inicio_torneo,fecha_final_torneo,pista_principal,"
        "categoria,fase,ronda,pareja1_jugador1,pareja1_jugador2,pareja2_jugador1,pareja2_jugador2,"
        "set1_pareja1,set1_pareja2,set2_pareja1,set2_pareja2,set3_pareja1,set3_pareja2,"
        "pareja_ganadora,pareja_perdedora,resultado_string\n"
        "Madrid Premier Padel P1 2024,NotAYear,02.09.2024,08.09.2024,Wizink Center,Femenino,"
        "Final,Cuadro,Ariana Sánchez,Paula Josemaría,Beatriz González,Delfina Brea,6,4,7,5,,,"
        "Team1,Team2,6-4 / 7-5\n"
    )
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(invalid_csv)
        path = f.name

    try:
        tab = TabularDataset(None)
        result = tab.validate_padel_structure(path)
        assert result['valid'] is False
        assert 'errors' in result
        error_text = ' '.join(result['errors'])
        assert 'anio_torneo' in error_text
        assert 'numeric' in error_text
    finally:
        os.remove(path)


def test_validate_padel_structure_invalid_date_format():
    """Test validation fails with wrong date format."""
    invalid_csv = (
        "nombre_torneo,anio_torneo,fecha_inicio_torneo,fecha_final_torneo,pista_principal,"
        "categoria,fase,ronda,pareja1_jugador1,pareja1_jugador2,pareja2_jugador1,pareja2_jugador2,"
        "set1_pareja1,set1_pareja2,set2_pareja1,set2_pareja2,set3_pareja1,set3_pareja2,"
        "pareja_ganadora,pareja_perdedora,resultado_string\n"
        "Madrid Premier Padel P1 2024,2024,2024-09-02,2024-09-08,Wizink Center,Femenino,"
        "Final,Cuadro,Ariana Sánchez,Paula Josemaría,Beatriz González,Delfina Brea,6,4,7,5,,,"
        "Team1,Team2,6-4 / 7-5\n"
    )
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(invalid_csv)
        path = f.name

    try:
        tab = TabularDataset(None)
        result = tab.validate_padel_structure(path)
        assert result['valid'] is False
        assert 'errors' in result
        error_text = ' '.join(result['errors'])
        assert 'DD.MM.YYYY' in error_text
    finally:
        os.remove(path)


def test_validate_padel_structure_invalid_category():
    """Test validation fails with invalid category."""
    invalid_csv = (
        "nombre_torneo,anio_torneo,fecha_inicio_torneo,fecha_final_torneo,pista_principal,"
        "categoria,fase,ronda,pareja1_jugador1,pareja1_jugador2,pareja2_jugador1,pareja2_jugador2,"
        "set1_pareja1,set1_pareja2,set2_pareja1,set2_pareja2,set3_pareja1,set3_pareja2,"
        "pareja_ganadora,pareja_perdedora,resultado_string\n"
        "Madrid Premier Padel P1 2024,2024,02.09.2024,08.09.2024,Wizink Center,InvalidCategory,"
        "Final,Cuadro,Ariana Sánchez,Paula Josemaría,Beatriz González,Delfina Brea,6,4,7,5,,,"
        "Team1,Team2,6-4 / 7-5\n"
    )
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(invalid_csv)
        path = f.name

    try:
        tab = TabularDataset(None)
        result = tab.validate_padel_structure(path)
        assert result['valid'] is False
        assert 'errors' in result
        error_text = ' '.join(result['errors'])
        assert 'categoria' in error_text
    finally:
        os.remove(path)


def test_validate_padel_structure_non_numeric_score():
    """Test validation fails when set scores are not numeric."""
    invalid_csv = (
        "nombre_torneo,anio_torneo,fecha_inicio_torneo,fecha_final_torneo,pista_principal,"
        "categoria,fase,ronda,pareja1_jugador1,pareja1_jugador2,pareja2_jugador1,pareja2_jugador2,"
        "set1_pareja1,set1_pareja2,set2_pareja1,set2_pareja2,set3_pareja1,set3_pareja2,"
        "pareja_ganadora,pareja_perdedora,resultado_string\n"
        "Madrid Premier Padel P1 2024,2024,02.09.2024,08.09.2024,Wizink Center,Masculino,"
        "Final,Cuadro,Juan Lebrón,Ale Galán,Paquito Navarro,Martín Di Nenno,six,4,7,five,,,"
        "Team1,Team2,6-4 / 7-5\n"
    )
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(invalid_csv)
        path = f.name

    try:
        tab = TabularDataset(None)
        result = tab.validate_padel_structure(path)
        assert result['valid'] is False
        assert 'errors' in result
        error_text = ' '.join(result['errors'])
        assert 'numeric' in error_text
    finally:
        os.remove(path)


def test_validate_padel_structure_empty_player_names():
    """Test validation fails when player names are empty."""
    invalid_csv = (
        "nombre_torneo,anio_torneo,fecha_inicio_torneo,fecha_final_torneo,pista_principal,"
        "categoria,fase,ronda,pareja1_jugador1,pareja1_jugador2,pareja2_jugador1,pareja2_jugador2,"
        "set1_pareja1,set1_pareja2,set2_pareja1,set2_pareja2,set3_pareja1,set3_pareja2,"
        "pareja_ganadora,pareja_perdedora,resultado_string\n"
        "Madrid Premier Padel P1 2024,2024,02.09.2024,08.09.2024,Wizink Center,Masculino,"
        "Final,Cuadro,,Ale Galán,Paquito Navarro,Martín Di Nenno,6,4,7,5,,,Team1,Team2,6-4 / 7-5\n"
    )
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(invalid_csv)
        path = f.name

    try:
        tab = TabularDataset(None)
        result = tab.validate_padel_structure(path)
        assert result['valid'] is False
        assert 'errors' in result
        error_text = ' '.join(result['errors'])
        assert 'cannot be empty' in error_text
    finally:
        os.remove(path)


def test_validate_padel_structure_valid_with_set3():
    """Test validation passes with valid 3-set match."""
    valid_csv = (
        "nombre_torneo,anio_torneo,fecha_inicio_torneo,fecha_final_torneo,pista_principal,"
        "categoria,fase,ronda,pareja1_jugador1,pareja1_jugador2,pareja2_jugador1,pareja2_jugador2,"
        "set1_pareja1,set1_pareja2,set2_pareja1,set2_pareja2,set3_pareja1,set3_pareja2,"
        "pareja_ganadora,pareja_perdedora,resultado_string\n"
        "Barcelona Open 2023,2023,15.04.2023,21.04.2023,Palau Sant Jordi,Mixed,Semifinal,Cuadro,"
        "Juan Lebrón,Adrián Allemandi,Paquito Navarro,Martin Di Nenno,4,6,7,5,6,4,"
        "Juan Lebrón_Adrián Allemandi,Paquito Navarro_Martin Di Nenno,4-6 / 7-5 / 6-4\n"
    )
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(valid_csv)
        path = f.name

    try:
        tab = TabularDataset(None)
        result = tab.validate_padel_structure(path)
        assert result['valid'] is True
    finally:
        os.remove(path)


def test_validate_padel_structure_file_not_found():
    """Test validation handles missing file gracefully."""
    tab = TabularDataset(None)
    result = tab.validate_padel_structure('/nonexistent/path/file.csv')
    assert result['valid'] is False
    assert 'errors' in result
    assert 'File not found' in result['errors'][0]
