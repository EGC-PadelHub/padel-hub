import pytest
from app import db
from app.modules.explore.repositories import ExploreRepository
from app.modules.dataset.models import DataSet, DSMetaData, TournamentType, Author
from app.modules.featuremodel.models import FeatureModel, FMMetaData
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
            dataset_doi="10.001"
        )
        meta2 = DSMetaData(
            title="Tenis Dataset 2",
            description="Datos de Darío",
            authors=[author_dario],
            tournament_type=TournamentType.OPEN,
            dataset_doi="10.002"
        )
        meta3 = DSMetaData(
            title="Padel, con comas.",
            description="Un dataset más",
            authors=[author_jose],
            tournament_type=TournamentType.QUALIFYING,
            dataset_doi="10.003"
        )
        db.session.add_all([meta1, meta2, meta3])
        db.session.commit()

        ds1 = DataSet(ds_meta_data_id=meta1.id, user_id=test_user.id)
        ds2 = DataSet(ds_meta_data_id=meta2.id, user_id=test_user.id)
        ds3 = DataSet(ds_meta_data_id=meta3.id, user_id=test_user.id)

        db.session.add_all([ds1, ds2, ds3])
        db.session.commit()

        fm_meta1 = FMMetaData(
            title="FM Meta 1", description="FM de Padel", uvl_filename="fm_padel.uvl",
            tournament_type=TournamentType.MASTER
        )
        fm_meta2 = FMMetaData(
            title="FM Meta 2", description="FM de Tenis", uvl_filename="fm_tenis.uvl",
            tournament_type=TournamentType.OPEN
        )
        fm_meta3 = FMMetaData(
            title="FM Meta 3", description="FM de Padel 2", uvl_filename="fm_padel_2.uvl",
            tournament_type=TournamentType.QUALIFYING
        )

        db.session.add_all([fm_meta1, fm_meta2, fm_meta3])
        db.session.commit()

        fm1 = FeatureModel(fm_meta_data_id=fm_meta1.id, data_set_id=ds1.id)
        fm2 = FeatureModel(fm_meta_data_id=fm_meta2.id, data_set_id=ds2.id)
        fm3 = FeatureModel(fm_meta_data_id=fm_meta3.id, data_set_id=ds3.id)

        db.session.add_all([fm1, fm2, fm3])
        db.session.commit()

        yield db

    finally:
        db.session.rollback()
        pass


# ---------------------------------POR TÍTULO------------------------------------------

def test_explore_filter_by_title_single_word_match(populated_db):
    repository = ExploreRepository()
    results = repository.filter(title="Tenis")

    assert len(results) == 1
    assert results[0].ds_meta_data.title == "Tenis Dataset 2"


def test_explore_filter_by_title_multi_word_match_and(populated_db):
    repository = ExploreRepository()
    results = repository.filter(title="Padel 1")  # Busca 'Padel' Y '1'

    assert len(results) == 1
    assert results[0].ds_meta_data.title == "Padel Dataset 1 (Pádel)"


def test_explore_filter_by_title_multiple_matches(populated_db):
    repository = ExploreRepository()
    results = repository.filter(title="Padel")

    assert len(results) == 2
    titles = {r.ds_meta_data.title for r in results}
    assert "Padel Dataset 1 (Pádel)" in titles
    assert "Padel, con comas." in titles


def test_explore_filter_by_title_no_match(populated_db):
    repository = ExploreRepository()
    results = repository.filter(title="Baloncesto")

    assert len(results) == 0


def test_explore_filter_by_title_case_insensitive(populated_db):
    repository = ExploreRepository()
    results = repository.filter(title="tenis dataset")  # en minúsculas

    assert len(results) == 1
    assert results[0].ds_meta_data.title == "Tenis Dataset 2"


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
    assert "Tenis Dataset 2" in titles


def test_explore_filter_by_author_no_match(populated_db):
    repository = ExploreRepository()
    results = repository.filter(author="Jefe")
    assert len(results) == 0


def test_explore_filter_by_author_and_title_combined(populated_db):
    repository = ExploreRepository()
    results = repository.filter(title="Padel", author="javi")

    assert len(results) == 1
    assert results[0].ds_meta_data.title == "Padel Dataset 1 (Pádel)"
