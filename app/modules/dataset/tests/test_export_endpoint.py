import io
import os
import zipfile

import pytest

from app import db
from app.modules.dataset.models import DataSet, DSMetaData, TournamentType
from app.modules.hubfile.models import Hubfile


@pytest.mark.usefixtures("test_client")
class TestDatasetExport:
    def _create_dataset_with_csv(self, user_id: int) -> DataSet:
        # Ensure WORKING_DIR is set so HubfileService resolves paths correctly
        os.environ.setdefault("WORKING_DIR", os.getcwd())

        # Minimal metadata
        dsmeta = DSMetaData(
            title="Test DS",
            description="Test",
            tournament_type=TournamentType.OTHER,
            publication_doi=None,
            dataset_doi=None,
            tags="a,b",
        )
        db.session.add(dsmeta)
        db.session.flush()

        dataset = DataSet(user_id=user_id, ds_meta_data_id=dsmeta.id)
        db.session.add(dataset)
        db.session.flush()

        # Ensure uploads path
        base = os.path.join(os.environ["WORKING_DIR"], "uploads", f"user_{user_id}", f"dataset_{dataset.id}")
        os.makedirs(base, exist_ok=True)
        csv_path = os.path.join(base, "data.csv")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("id,name\n1,Alice\n2,Bob\n")

        # File db entry
        size = os.path.getsize(csv_path)
        file = Hubfile(name="data.csv", checksum="dummy", size=size, dataset_id=dataset.id)
        db.session.add(file)
        db.session.commit()

        return dataset

    def test_export_zip_contains_converted_formats(self, test_client):
        # Ensure WORKING_DIR is set for the entire test
        os.environ.setdefault("WORKING_DIR", os.getcwd())
        
        # By default, tests create a user with id=1 in conftest
        user_id = 1
        dataset = self._create_dataset_with_csv(user_id)

        # Hit export endpoint
        resp = test_client.get(f"/dataset/export/{dataset.id}")
        assert resp.status_code == 200
        assert resp.mimetype == "application/zip"

        # Inspect zip content from response data stream
        data = b"".join(resp.response)
        zf = zipfile.ZipFile(io.BytesIO(data))
        names = zf.namelist()
        
        # Debug: print what's actually in the zip
        print(f"DEBUG: Files in zip: {names}")

        # Expect CSV copy and JSON/XML; XLSX may be skipped if openpyxl missing
        assert any(n.endswith("/csv/data.csv") for n in names), f"CSV not found. Files in zip: {names}"
        assert any(n.endswith("/json/data.json") for n in names)
        assert any(n.endswith("/xml/data.xml") for n in names)
        assert any(n.endswith("/tsv/data.tsv") for n in names)
        assert any(n.endswith("/yaml/data.yaml") for n in names)
        assert any(n.endswith("/txt/data.txt") for n in names)
        # XLSX is best-effort; if present, it should have this name
        maybe_xlsx = [n for n in names if n.endswith("/xlsx/data.xlsx")]
        if maybe_xlsx:
            # Basic sanity: file is a non-empty blob
            with zf.open(maybe_xlsx[0]) as fh:
                assert len(fh.read()) > 0

        zf.close()
