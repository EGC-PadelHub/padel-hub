import pytest
from datetime import datetime, timezone

from app import db
from app.modules.auth.models import User
from app.modules.conftest import login, logout
from app.modules.dataset.models import (
    DataSet, DSMetaData, DSMetrics, DSDownloadRecord, DSViewRecord, TournamentType
)
from app.modules.profile.models import UserProfile


@pytest.fixture(scope="module")
def test_client(test_client):
    """Creates test data: 2 users, 4 datasets, downloads and views for metrics testing."""
    with test_client.application.app_context():
        # Create users
        user_test = User(email="metrics_user@example.com", password="test1234")
        other_user = User(email="other_user@example.com", password="test1234")
        db.session.add_all([user_test, other_user])
        db.session.commit()

        db.session.add_all([
            UserProfile(user_id=user_test.id, name="Metrics", surname="User"),
            UserProfile(user_id=other_user.id, name="Other", surname="User")
        ])
        db.session.commit()

        # Helper function to create dataset
        def create_dataset(user_id, title, doi, tags):
            metrics = DSMetrics(number_of_models="5", number_of_features="50")
            db.session.add(metrics)
            db.session.commit()
            
            metadata = DSMetaData(
                title=title, description=f"Description for {title}",
                tournament_type=TournamentType.MASTER,
                dataset_doi=doi, tags=tags, ds_metrics_id=metrics.id
            )
            db.session.add(metadata)
            db.session.commit()
            
            dataset = DataSet(user_id=user_id, ds_meta_data_id=metadata.id, created_at=datetime.now(timezone.utc))
            db.session.add(dataset)
            db.session.commit()
            return dataset

        # Create 3 datasets for metrics_user (2 with DOI, 1 without)
        ds1 = create_dataset(user_test.id, "Dataset 1", "10.1234/test.1", "test,metrics")
        ds2 = create_dataset(user_test.id, "Dataset 2", None, "test")
        ds3 = create_dataset(user_test.id, "Dataset 3", "10.1234/test.3", "test,sync")
        
        # Create 1 dataset for other_user
        ds_other = create_dataset(other_user.id, "Other Dataset", "10.1234/other.1", "other")

        # Create download records (3 downloads of metrics_user's datasets, 1 by metrics_user)
        db.session.add_all([
            DSDownloadRecord(
                user_id=other_user.id,
                dataset_id=ds1.id,
                download_date=datetime.now(timezone.utc),
                download_cookie=f"cookie-{i}"
            )
            for i in range(1, 4)
        ])
        db.session.add(
            DSDownloadRecord(
                user_id=user_test.id,
                dataset_id=ds_other.id,
                download_date=datetime.now(timezone.utc),
                download_cookie="cookie-4"
            )
        )

        # Create view records (4 views of metrics_user's datasets)
        db.session.add_all([
            DSViewRecord(
                user_id=other_user.id,
                dataset_id=ds.id,
                view_date=datetime.now(timezone.utc),
                view_cookie=f"view-{i}"
            )
            for i, ds in enumerate([ds1, ds1, ds2, ds3], 1)
        ])

        db.session.commit()

    yield test_client


def test_metrics_dashboard_access_without_login(test_client):
    """Test that the dashboard requires authentication and redirects to login."""
    response = test_client.get("/profile/metrics", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.location


def test_metrics_dashboard_access_with_login(test_client):
    """Test that authenticated users can access the dashboard."""
    login_response = login(test_client, "metrics_user@example.com", "test1234")
    assert login_response.status_code == 200

    response = test_client.get("/profile/metrics")
    assert response.status_code == 200
    assert b"My Metrics Dashboard" in response.data
    logout(test_client)


def test_metrics_dashboard_uploaded_datasets_and_synchronizations(test_client):
    """Test uploaded datasets (3) and synchronizations (2 with DOI) counts."""
    login_response = login(test_client, "metrics_user@example.com", "test1234")
    assert login_response.status_code == 200

    response = test_client.get("/profile/metrics")
    response_text = response.data.decode("utf-8")

    assert "Uploaded Datasets" in response_text and "3" in response_text
    assert "Synchronizations" in response_text and "2" in response_text
    logout(test_client)


def test_metrics_dashboard_downloads_metrics(test_client):
    """Test downloads of my datasets (3) and downloads I made (1)."""
    login_response = login(test_client, "metrics_user@example.com", "test1234")
    assert login_response.status_code == 200

    response = test_client.get("/profile/metrics")
    response_text = response.data.decode("utf-8")

    assert "Downloads of My Datasets" in response_text and "3" in response_text
    assert "Downloads I Made" in response_text and "1" in response_text
    logout(test_client)


def test_metrics_dashboard_complete_metrics_integration(test_client):
    """Integration test verifying all metrics, titles, descriptions, and HTML structure."""
    login_response = login(test_client, "metrics_user@example.com", "test1234")
    assert login_response.status_code == 200

    response = test_client.get("/profile/metrics")
    response_text = response.data.decode("utf-8")

    # Verify all card titles
    assert all(text in response_text for text in [
        "Uploaded Datasets", "Downloads Received", "Downloads Made", "Synchronized"
    ])

    # Verify descriptions
    assert all(text in response_text for text in [
        "Datasets you created", "Times your datasets were downloaded",
        "Datasets you downloaded", "Datasets with DOI"
    ])
    
    # Verify HTML structure
    assert all(cls in response_text for cls in ["container", "card", "metric-card"])
    logout(test_client)


def test_metrics_dashboard_user_isolation(test_client):
    """Test that each user sees only their own metrics (data isolation)."""
    # metrics_user: 3 datasets
    login(test_client, "metrics_user@example.com", "test1234")
    response1 = test_client.get("/profile/metrics")
    assert "3" in response1.data.decode("utf-8")
    logout(test_client)

    # other_user: 1 dataset
    login(test_client, "other_user@example.com", "test1234")
    response2 = test_client.get("/profile/metrics")
    assert "1" in response2.data.decode("utf-8")
    logout(test_client)


