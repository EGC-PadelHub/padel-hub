import pytest
from datetime import datetime, timedelta
from app import db
from app.modules.explore.repositories import ExploreRepository
from app.modules.dataset.models import DataSet, DSMetaData, TournamentType, Author
from app.modules.auth.models import User


@pytest.fixture(scope="function")
def populated_db(clean_database):
    try:
        test_user = User(email="test@example.com", password="password")
        author_javi = Author(name="Javi Pallarés")
        author_dario = Author(name="Darío Zafra")
        author_jose = Author(name="José María")
        db.session.add_all([test_user, author_javi, author_dario, author_jose])
        db.session.commit()

        meta1 = DSMetaData(
            title="Padel Dataset 1 (Pádel)",
            description="Datos de Javi",
            authors=[author_javi],
            tournament_type=TournamentType.MASTER,
            dataset_doi="10.001",
            tags="padel, master, 2024"
        )
        meta2 = DSMetaData(
            title="Padel Dataset 2",
            description="Datos de Darío",
            authors=[author_dario],
            tournament_type=TournamentType.OPEN,
            dataset_doi="10.002",
            tags="padel, open, spain"
        )
        meta3 = DSMetaData(
            title="Padel, con comas.",
            description="Un dataset más",
            authors=[author_jose],
            tournament_type=TournamentType.QUALIFYING,
            dataset_doi="10.003",
            tags="qualifying, future"
        )
        db.session.add_all([meta1, meta2, meta3])
        db.session.commit()

        # Definimos fechas específicas para probar el sorting
        # ds1: HOY (El más nuevo)
        # ds2: AYER
        # ds3: ANTEAYER (El más antiguo)
        ds1 = DataSet(ds_meta_data_id=meta1.id, user_id=test_user.id, created_at=datetime.now())
        ds2 = DataSet(ds_meta_data_id=meta2.id, user_id=test_user.id, created_at=datetime.now() - timedelta(days=1))
        ds3 = DataSet(ds_meta_data_id=meta3.id, user_id=test_user.id, created_at=datetime.now() - timedelta(days=2))

        db.session.add_all([ds1, ds2, ds3])
        db.session.commit()

        yield db

    finally:
        db.session.rollback()
        pass


# ---------------------------------POR TÍTULO------------------------------------------

def test_explore_filter_by_title_single_word_match(populated_db):
    repository = ExploreRepository()
    results = repository.filter(title="Padel")

    assert len(results) == 3
    titles = {r.ds_meta_data.title for r in results}
    assert "Padel Dataset 1 (Pádel)" in titles
    assert "Padel Dataset 2" in titles
    assert "Padel, con comas." in titles


def test_explore_filter_by_title_multi_word_match_and(populated_db):
    repository = ExploreRepository()
    results = repository.filter(title="Padel 1")  # Busca 'Padel' Y '1'

    assert len(results) == 1
    assert results[0].ds_meta_data.title == "Padel Dataset 1 (Pádel)"


def test_explore_filter_by_title_multiple_matches(populated_db):
    repository = ExploreRepository()
    results = repository.filter(title="Padel")

    assert len(results) == 3
    titles = {r.ds_meta_data.title for r in results}
    assert "Padel Dataset 1 (Pádel)" in titles
    assert "Padel, con comas." in titles
    assert "Padel Dataset 2" in titles


def test_explore_filter_by_title_no_match(populated_db):
    repository = ExploreRepository()
    results = repository.filter(title="Baloncesto")

    assert len(results) == 0


def test_explore_filter_by_title_case_insensitive(populated_db):
    repository = ExploreRepository()
    results = repository.filter(title="padel dataset")  # en minúsculas

    assert len(results) == 2


def test_explore_filter_by_title_empty_string_returns_all(populated_db):
    repository = ExploreRepository()
    results = repository.filter(title="")

    assert len(results) == 3


# ---------------------------------POR AUTOR------------------------------------------


def test_explore_filter_by_author_javi(populated_db):
    repository = ExploreRepository()
    results = repository.filter(author="Javi")

    assert len(results) == 1
    titles = {r.ds_meta_data.title for r in results}
    assert "Padel Dataset 1 (Pádel)" in titles


def test_explore_filter_by_author_dario_case_insensitive(populated_db):
    repository = ExploreRepository()
    results = repository.filter(author="darío")
    assert len(results) == 1
    titles = {r.ds_meta_data.title for r in results}
    assert "Padel Dataset 2" in titles


def test_explore_filter_by_author_no_match(populated_db):
    repository = ExploreRepository()
    results = repository.filter(author="Jefe")
    assert len(results) == 0


def test_explore_filter_by_author_and_title_combined(populated_db):
    repository = ExploreRepository()
    results = repository.filter(title="Padel", author="javi")

    assert len(results) == 1
    assert results[0].ds_meta_data.title == "Padel Dataset 1 (Pádel)"


# ---------------------------------POR TIPO DE TORNEO------------------------------------------

def test_explore_filter_by_tournament_type_master(populated_db):
    repository = ExploreRepository()
    results = repository.filter(tournament_type="master")

    assert len(results) == 1
    titles = {r.ds_meta_data.title for r in results}
    assert "Padel Dataset 1 (Pádel)" in titles


def test_explore_filter_by_tournament_type_open(populated_db):
    repository = ExploreRepository()
    results = repository.filter(tournament_type="open")

    assert len(results) == 1
    titles = {r.ds_meta_data.title for r in results}
    assert "Padel Dataset 2" in titles

def test_explore_filter_by_tournament_type_qualifying(populated_db):
    repository = ExploreRepository()
    results = repository.filter(tournament_type="qualifying")

    assert len(results) == 1
    titles = {r.ds_meta_data.title for r in results}
    assert "Padel, con comas." in titles

def test_explore_filter_by_tournament_type_any(populated_db):
    repository = ExploreRepository()
    results = repository.filter(tournament_type="any")

    assert len(results) == 3

# ---------------------------------POR DESCRIPCIÓN------------------------------------------

def test_explore_filter_by_description_common(populated_db):
    repository = ExploreRepository()
    results = repository.filter(description="Datos")

    assert len(results) == 2
    titles = {r.ds_meta_data.title for r in results}
    assert "Padel Dataset 1 (Pádel)" in titles
    assert "Padel Dataset 2" in titles

def test_explore_filter_by_description_no_match(populated_db):
    repository = ExploreRepository()
    results = repository.filter(description="Datos de Juan")

    assert len(results) == 0

#---------------------------------POR ETIQUETAS------------------------------------------

def test_explore_filter_by_tags_no_tags(populated_db):
    repository = ExploreRepository()
    results = repository.filter(tags=[])

    assert len(results) == 3  # Todos los datasets deberían ser devueltos

def test_explore_filter_by_single_tag(populated_db):
    repository = ExploreRepository()
    results = repository.filter(tags=["master"])

    assert len(results) == 1
    assert results[0].ds_meta_data.title == "Padel Dataset 1 (Pádel)"

def test_explore_filter_by_multiple_tags_and_logic(populated_db):
    repository = ExploreRepository()
    results = repository.filter(tags=["padel", "spain"])

    assert len(results) == 1
    assert results[0].ds_meta_data.title == "Padel Dataset 2"

def test_explore_filter_by_tags_no_match(populated_db):
    repository = ExploreRepository()
    results = repository.filter(tags=["nada"])

    assert len(results) == 0


def test_explore_filter_by_tags_partial_match(populated_db):
    # Dataset 3 tiene "qualifying, future"
    repository = ExploreRepository()
    results = repository.filter(tags=["qualif"]) # Debería funcionar con ilike %tag%

    assert len(results) == 1
    assert results[0].ds_meta_data.title == "Padel, con comas."

#--------------------------------SORTING------------------------------------------

def test_explore_filter_sorting_newest(populated_db):
    repository = ExploreRepository()
    results = repository.filter(sorting="newest")

    assert len(results) == 3
    # El primero debe ser el más nuevo (ds1)
    assert results[0].ds_meta_data.title == "Padel Dataset 1 (Pádel)"
    # El último debe ser el más antiguo (ds3)
    assert results[2].ds_meta_data.title == "Padel, con comas."

def test_explore_filter_sorting_oldest(populated_db):
    repository = ExploreRepository()
    results = repository.filter(sorting="oldest")

    assert len(results) == 3
    # El primero debe ser el más antiguo (ds3)
    assert results[0].ds_meta_data.title == "Padel, con comas."
    # El último debe ser el más nuevo (ds1)
    assert results[2].ds_meta_data.title == "Padel Dataset 1 (Pádel)"