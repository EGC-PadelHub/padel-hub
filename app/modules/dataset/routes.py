import json
import logging
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from zipfile import ZipFile
from io import BytesIO
import re

from flask import (
    abort,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required
from flask_wtf.csrf import generate_csrf

from app.modules.dataset import dataset_bp
from app.modules.dataset.forms import DataSetForm
from app.modules.dataset.models import DSDownloadRecord
from app.modules.dataset.services import (
    AuthorService,
    DataSetService,
    DOIMappingService,
    DSDownloadRecordService,
    DSMetaDataService,
    DSViewRecordService,
)
from app.modules.zenodo.services import ZenodoService
from app.modules.dataset.types.tabular import TabularDataset

# Optional imports for feature model conversions
try:
    from flamapy.metamodels.fm_metamodel.transformations import UVLReader
    from flamapy.metamodels.pysat_metamodel.transformations import DimacsWriter, FmToPysat
except Exception:  # pragma: no cover - only needed when exporting UVL to CNF/DIMACS
    UVLReader = None
    DimacsWriter = None
    FmToPysat = None

logger = logging.getLogger(__name__)


dataset_service = DataSetService()
author_service = AuthorService()
dsmetadata_service = DSMetaDataService()
zenodo_service = ZenodoService()
doi_mapping_service = DOIMappingService()
ds_view_record_service = DSViewRecordService()


@dataset_bp.route("/dataset/upload", methods=["GET", "POST"])
@login_required
def create_dataset():
    form = DataSetForm()
    if request.method == "POST":

        dataset = None

        if not form.validate_on_submit():
            logger.error(f"Dataset form validation failed: {form.errors}")
            # Return structured errors so the frontend can show specific field messages
            return jsonify({"message": "Form validation failed", "errors": form.errors}), 400

        try:
            logger.info("Creating dataset...")
            dataset = dataset_service.create_from_form(form=form, current_user=current_user)
            logger.info(f"Created dataset: {dataset}")
            dataset_service.move_feature_models(dataset)
        except Exception as exc:
            logger.exception(f"Exception while create dataset data in local {exc}")
            return jsonify({"Exception while create dataset data in local: ": str(exc)}), 400

        # send dataset as deposition to Zenodo
        data = {}
        # If user chose to save as draft or as anonymous upload, skip contacting Zenodo/fakenodo now.
        # Anonymous uploads must remain local (unsynchronized) until the user explicitly clicks Sync.
        if getattr(form, 'upload_type', None) and form.upload_type.data in ('draft', 'anonymous'):
            data = {}
            zenodo_response_json = {}
        else:
            try:
                zenodo_response_json = zenodo_service.create_new_deposition(dataset)
                response_data = json.dumps(zenodo_response_json)
                data = json.loads(response_data)
            except Exception as exc:
                data = {}
                zenodo_response_json = {}
                logger.exception(f"Exception while create dataset data in Zenodo {exc}")

        # Some Zenodo/fakenodo endpoints may not return `conceptrecid` but they do return an `id`.
        # Accept either `conceptrecid` or `id` as indication that the deposition was created.
        if data.get("conceptrecid") or data.get("id"):
            deposition_id = data.get("id")

            # update dataset with deposition id in Zenodo
            dataset_service.update_dsmetadata(dataset.ds_meta_data_id, deposition_id=deposition_id)

            try:
                # iterate for each feature model (one feature model = one request to Zenodo)
                for feature_model in dataset.feature_models:
                    zenodo_service.upload_file(dataset, deposition_id, feature_model)

                # publish deposition
                zenodo_service.publish_deposition(deposition_id)

                # update DOI
                deposition_doi = zenodo_service.get_doi(deposition_id)
                dataset_service.update_dsmetadata(dataset.ds_meta_data_id, dataset_doi=deposition_doi)
            except Exception as e:
                msg = f"it has not been possible upload feature models in Zenodo and update the DOI: {e}"
                return jsonify({"message": msg}), 200

        # Delete temp folder
        file_path = current_user.temp_folder()
        if os.path.exists(file_path) and os.path.isdir(file_path):
            shutil.rmtree(file_path)

        msg = "Everything works!"
        return jsonify({"message": msg}), 200

    return render_template("dataset/upload_dataset.html", form=form)


@dataset_bp.route("/dataset/list", methods=["GET", "POST"])
@login_required
def list_dataset():
    # Ensure a CSRF token is available for inline forms (e.g. sync action)
    csrf_token = None
    try:
        csrf_token = generate_csrf()
    except Exception:
        csrf_token = None

    return render_template(
        "dataset/list_datasets.html",
        datasets=dataset_service.get_synchronized(current_user.id),
        local_datasets=dataset_service.get_unsynchronized(current_user.id),
        csrf_token=csrf_token,
    )


@dataset_bp.route("/dataset/file/upload", methods=["POST"])
@login_required
def upload():
    file = request.files["file"]
    temp_folder = current_user.temp_folder()

    # Only accept CSV files for padel-hub
    if not file or not file.filename.lower().endswith(".csv"):
        return jsonify({"message": "No valid file. Only .csv files are accepted."}), 400

    # create temp folder
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    file_path = os.path.join(temp_folder, file.filename)

    if os.path.exists(file_path):
        # Generate unique filename (by recursion)
        base_name, extension = os.path.splitext(file.filename)
        i = 1
        while os.path.exists(os.path.join(temp_folder, f"{base_name} ({i}){extension}")):
            i += 1
        new_filename = f"{base_name} ({i}){extension}"
        file_path = os.path.join(temp_folder, new_filename)
    else:
        new_filename = file.filename

    try:
        file.save(file_path)
    except Exception as e:
        return jsonify({"message": str(e)}), 500

    # After saving, validate CSV syntax and report first syntax error (if any)
    try:
        tab = TabularDataset(None)
        validation = tab.validate_syntax(file_path)
    except Exception as e:
        validation = {"valid": False, "message": f"Internal validation error: {e}"}

    if not validation.get("valid"):
        # Return helpful info to the user: line and message when available
        resp = {"message": "CSV syntax error", "filename": new_filename}
        if "line" in validation:
            resp["line"] = validation["line"]
        if "message" in validation:
            resp["error"] = validation["message"]
        if "encoding" in validation:
            resp["encoding_attempted"] = validation["encoding"]
        if "snippet" in validation and validation.get("snippet"):
            resp["snippet"] = validation.get("snippet")
        # Remove the saved file on validation failure to avoid leaving temp files
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.exception(f"Failed to remove temp file after validation failure: {e}")

        return jsonify(resp), 400

    return (
        jsonify(
            {
                "message": "CSV uploaded and validated successfully",
                "filename": new_filename,
                "encoding": validation.get("encoding"),
            }
        ),
        200,
    )


@dataset_bp.route("/dataset/file/delete", methods=["POST"])
def delete():
    data = request.get_json()
    filename = data.get("file")
    temp_folder = current_user.temp_folder()
    filepath = os.path.join(temp_folder, filename)

    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"message": "File deleted successfully"})

    return jsonify({"error": "Error: File not found"})


@dataset_bp.route("/dataset/download/<int:dataset_id>", methods=["GET"])
def download_dataset(dataset_id):
    dataset = dataset_service.get_or_404(dataset_id)

    file_path = f"uploads/user_{dataset.user_id}/dataset_{dataset.id}/"

    # Build a friendly base name using the dataset title
    def slugify(value: str) -> str:
        value = value.strip().lower()
        value = re.sub(r"[^a-z0-9\-\._]+", "-", value)
        value = re.sub(r"-+", "-", value).strip("-")
        return value or f"dataset-{dataset.id}"

    ds_title = getattr(dataset, "name", None)
    if callable(ds_title):
        ds_title = ds_title()
    if not ds_title:
        ds_title = dataset.ds_meta_data.title if dataset.ds_meta_data and dataset.ds_meta_data.title else f"dataset-{dataset.id}"
    base_name = f"{slugify(ds_title)}-{dataset.id}"

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"{base_name}.zip")

    with ZipFile(zip_path, "w") as zipf:
        for subdir, dirs, files in os.walk(file_path):
            for file in files:
                full_path = os.path.join(subdir, file)

                relative_path = os.path.relpath(full_path, file_path)

                zipf.write(
                    full_path,
                    arcname=os.path.join(base_name, relative_path),
                )

    user_cookie = request.cookies.get("download_cookie")
    if not user_cookie:
        user_cookie = str(uuid.uuid4())  # Generate a new unique identifier if it does not exist

    # Record the download in the database (always, for each download action)
    logger.info(f"Recording download for dataset_id={dataset_id}, user_id={current_user.id if current_user.is_authenticated else None}, cookie={user_cookie}")
    download_record = DSDownloadRecordService().create(
        user_id=current_user.id if current_user.is_authenticated else None,
        dataset_id=dataset_id,
        download_date=datetime.now(timezone.utc),
        download_cookie=user_cookie,
    )
    logger.info(f"Download record created: {download_record}")

    # Send the file
    resp = make_response(
        send_from_directory(
            temp_dir,
            f"{base_name}.zip",
            as_attachment=True,
            mimetype="application/zip",
        )
    )
    
    # Save/update the cookie in the user's browser
    resp.set_cookie("download_cookie", user_cookie)

    return resp


@dataset_bp.route("/dataset/export/<int:dataset_id>", methods=["GET"])
def export_dataset(dataset_id: int):
    """Export the dataset into multiple formats and return a single ZIP.

    For each CSV file in the dataset, generate: CSV (copy), JSON, XML, XLSX.
    For each UVL file in the dataset (if any), generate: CNF (DIMACS).

    The resulting ZIP structure is:
        dataset_<id>/
          csv/<name>.csv
          json/<name>.json
          xml/<name>.xml
          xlsx/<name>.xlsx
          dimacs/<name>.cnf
    """
    dataset = dataset_service.get_or_404(dataset_id)

    # Base folder where original files are stored
    # We'll resolve file paths using HubfileService to be robust to WORKING_DIR and avoid 404
    from app.modules.hubfile.services import HubfileService

    # Friendly base name for ZIP and top-level folder
    def slugify(value: str) -> str:
        value = value.strip().lower()
        value = re.sub(r"[^a-z0-9\-\._]+", "-", value)
        value = re.sub(r"-+", "-", value).strip("-")
        return value or f"dataset-{dataset.id}"

    ds_title = getattr(dataset, "name", None)
    if callable(ds_title):
        ds_title = ds_title()
    if not ds_title:
        ds_title = dataset.ds_meta_data.title if dataset.ds_meta_data and dataset.ds_meta_data.title else f"dataset-{dataset.id}"
    base_name = f"{slugify(ds_title)}-{dataset.id}"

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"{base_name}_different-formats.zip")

    def _detect_header(csv_path: str):
        import csv as _csv

        # Try to detect encoding first (reuse validate_syntax heuristics)
        encodings_to_try = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        enc = "utf-8"
        for e in encodings_to_try:
            try:
                with open(csv_path, "r", encoding=e, newline="") as f:
                    sample = f.read(2048)
                enc = e
                break
            except Exception:
                continue

        has_header = False
        try:
            with open(csv_path, "r", encoding=enc, newline="") as f:
                sample = f.read(2048)
                f.seek(0)
                try:
                    has_header = _csv.Sniffer().has_header(sample)
                except Exception:
                    has_header = True  # default to header
        except Exception:
            has_header = True
        return enc, has_header

    def _csv_to_json_bytes(csv_path: str) -> bytes:
        import csv as _csv

        enc, has_header = _detect_header(csv_path)
        with open(csv_path, "r", encoding=enc, newline="") as f:
            if has_header:
                reader = _csv.DictReader(f)
                data = list(reader)
            else:
                reader = _csv.reader(f)
                data = list(reader)
        return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")

    def _csv_to_xml_bytes(csv_path: str) -> bytes:
        import csv as _csv
        import xml.etree.ElementTree as ET

        enc, has_header = _detect_header(csv_path)
        root = ET.Element("rows")
        with open(csv_path, "r", encoding=enc, newline="") as f:
            if has_header:
                reader = _csv.DictReader(f)
                for row in reader:
                    row_el = ET.SubElement(root, "row")
                    for k, v in row.items():
                        col_el = ET.SubElement(row_el, "col", name=str(k))
                        col_el.text = str(v) if v is not None else ""
            else:
                reader = _csv.reader(f)
                for r in reader:
                    row_el = ET.SubElement(root, "row")
                    for idx, v in enumerate(r):
                        col_el = ET.SubElement(row_el, "col", name=f"col{idx+1}")
                        col_el.text = str(v) if v is not None else ""

        xml_bytes = BytesIO()
        tree = ET.ElementTree(root)
        tree.write(xml_bytes, encoding="utf-8", xml_declaration=True)
        return xml_bytes.getvalue()

    def _csv_to_xlsx_bytes(csv_path: str) -> bytes:
        # Lazy import to avoid hard dependency during app startup
        try:
            from openpyxl import Workbook  # type: ignore
        except Exception:
            logger.warning("openpyxl not available; skipping XLSX export for %s", csv_path)
            return b""

        import csv as _csv

        enc, _ = _detect_header(csv_path)
        wb = Workbook()
        ws = wb.active
        with open(csv_path, "r", encoding=enc, newline="") as f:
            reader = _csv.reader(f)
            for row in reader:
                ws.append(list(row))
        bio = BytesIO()
        wb.save(bio)
        return bio.getvalue()

    def _uvl_to_dimacs_bytes(uvl_path: str) -> bytes:
        if not (UVLReader and DimacsWriter and FmToPysat):
            logger.warning("Flamapy not available; skipping DIMACS export for %s", uvl_path)
            return b""

    def _csv_to_tsv_bytes(csv_path: str) -> bytes:
        import csv as _csv
        from io import StringIO

        enc, _ = _detect_header(csv_path)
        output = StringIO()
        writer = _csv.writer(output, delimiter="\t", lineterminator="\n")
        with open(csv_path, "r", encoding=enc, newline="") as f:
            reader = _csv.reader(f)
            for row in reader:
                writer.writerow(row)
        return output.getvalue().encode("utf-8")

    def _csv_to_yaml_bytes(csv_path: str) -> bytes:
        import csv as _csv
        import yaml  # PyYAML is in requirements

        enc, has_header = _detect_header(csv_path)
        with open(csv_path, "r", encoding=enc, newline="") as f:
            if has_header:
                reader = _csv.DictReader(f)
                data = list(reader)
            else:
                reader = _csv.reader(f)
                data = list(reader)
        # Dump YAML with unicode preserved and stable key order
        return yaml.safe_dump(data, allow_unicode=True, sort_keys=False).encode("utf-8")

    def _csv_to_txt_bytes(csv_path: str) -> bytes:
        # Provide a plain-text copy of the original CSV contents
        # preserving original encoding best-effort.
        enc, _ = _detect_header(csv_path)
        with open(csv_path, "r", encoding=enc, errors="replace") as f:
            return f.read().encode("utf-8")
        try:
            # Create a temporary file to use the writer API, then read bytes back
            tmp = tempfile.NamedTemporaryFile(suffix=".cnf", delete=False)
            tmp.close()
            fm = UVLReader(uvl_path).transform()
            sat = FmToPysat(fm).transform()
            DimacsWriter(tmp.name, sat).transform()
            with open(tmp.name, "rb") as f:
                data = f.read()
            os.remove(tmp.name)
            return data
        except Exception as exc:
            logger.exception("Failed to convert UVL to DIMACS: %s", exc)
            return b""

    with ZipFile(zip_path, "w") as zipf:
        # Iterate dataset files via DB and resolve absolute paths via service
        for fm in getattr(dataset, "feature_models", []) or []:
            for hubfile in getattr(fm, "files", []) or []:
                try:
                    full_path = HubfileService().get_path_by_hubfile(hubfile)
                except Exception:
                    full_path = None
                if not full_path or not os.path.isfile(full_path):
                    continue

                orig_filename = os.path.basename(hubfile.name or os.path.basename(full_path))
                file_base, ext = os.path.splitext(orig_filename)
                ext = ext.lower()

                # Include original CSVs under csv/
                if ext == ".csv":
                    arc_csv = os.path.join(base_name, "csv", orig_filename)
                    try:
                        zipf.write(full_path, arcname=arc_csv)
                    except Exception as exc:
                        logger.exception("Failed to add CSV to zip: %s", exc)

                    # JSON
                    try:
                        json_bytes = _csv_to_json_bytes(full_path)
                        zipf.writestr(os.path.join(base_name, "json", f"{file_base}.json"), json_bytes)
                    except Exception as exc:
                        logger.exception("CSV->JSON export failed for %s: %s", orig_filename, exc)

                    # XML
                    try:
                        xml_bytes = _csv_to_xml_bytes(full_path)
                        zipf.writestr(os.path.join(base_name, "xml", f"{file_base}.xml"), xml_bytes)
                    except Exception as exc:
                        logger.exception("CSV->XML export failed for %s: %s", orig_filename, exc)

                    # XLSX
                    try:
                        xlsx_bytes = _csv_to_xlsx_bytes(full_path)
                        if xlsx_bytes:
                            zipf.writestr(os.path.join(base_name, "xlsx", f"{file_base}.xlsx"), xlsx_bytes)
                    except Exception as exc:
                        logger.exception("CSV->XLSX export failed for %s: %s", orig_filename, exc)

                    # TSV
                    try:
                        tsv_bytes = _csv_to_tsv_bytes(full_path)
                        zipf.writestr(os.path.join(base_name, "tsv", f"{file_base}.tsv"), tsv_bytes)
                    except Exception as exc:
                        logger.exception("CSV->TSV export failed for %s: %s", orig_filename, exc)

                    # YAML
                    try:
                        yaml_bytes = _csv_to_yaml_bytes(full_path)
                        zipf.writestr(os.path.join(base_name, "yaml", f"{file_base}.yaml"), yaml_bytes)
                    except Exception as exc:
                        logger.exception("CSV->YAML export failed for %s: %s", orig_filename, exc)

                    # TXT (plain-text view of CSV)
                    try:
                        txt_bytes = _csv_to_txt_bytes(full_path)
                        zipf.writestr(os.path.join(base_name, "txt", f"{file_base}.txt"), txt_bytes)
                    except Exception as exc:
                        logger.exception("CSV->TXT export failed for %s: %s", orig_filename, exc)

                # Feature model UVL -> DIMACS
                elif ext == ".uvl":
                    try:
                        dimacs_bytes = _uvl_to_dimacs_bytes(full_path)
                        if dimacs_bytes:
                            zipf.writestr(os.path.join(base_name, "dimacs", f"{file_base}.cnf"), dimacs_bytes)
                            # Also provide .dimacs extension for convenience
                            zipf.writestr(os.path.join(base_name, "dimacs", f"{file_base}.dimacs"), dimacs_bytes)
                    except Exception as exc:
                        logger.exception("UVL->DIMACS export failed for %s: %s", orig_filename, exc)
                else:
                    # Copy other files as-is under original/
                    rel_name = orig_filename
                    arc_other = os.path.join(base_name, "original", rel_name)
                    try:
                        zipf.write(full_path, arcname=arc_other)
                    except Exception as exc:
                        logger.exception("Failed to add file to zip: %s", exc)

    # Manage download cookie and record
    user_cookie = request.cookies.get("download_cookie")
    if not user_cookie:
        user_cookie = str(uuid.uuid4())

    # Record the download in the database (always, for each download action)
    logger.info(f"Recording export download for dataset_id={dataset_id}, user_id={current_user.id if current_user.is_authenticated else None}, cookie={user_cookie}")
    download_record = DSDownloadRecordService().create(
        user_id=current_user.id if current_user.is_authenticated else None,
        dataset_id=dataset_id,
        download_date=datetime.now(timezone.utc),
        download_cookie=user_cookie,
    )
    logger.info(f"Export download record created: {download_record}")

    # Send the file
    resp = make_response(
        send_from_directory(
            temp_dir, f"{base_name}_different-formats.zip", as_attachment=True, mimetype="application/zip"
        )
    )
    
    # Save/update the cookie in the user's browser
    resp.set_cookie("download_cookie", user_cookie)

    return resp


@dataset_bp.route("/doi/<path:doi>/", methods=["GET"])
def subdomain_index(doi):

    # Check if the DOI is an old DOI
    new_doi = doi_mapping_service.get_new_doi(doi)
    if new_doi:
        # Redirect to the same path with the new DOI
        return redirect(url_for("dataset.subdomain_index", doi=new_doi), code=302)

    # Try to search the dataset by the provided DOI (which should already be the new one)
    ds_meta_data = dsmetadata_service.filter_by_doi(doi)

    if not ds_meta_data:
        abort(404)

    # Get dataset
    dataset = ds_meta_data.data_set

    # Prepare CSV preview rows (if any CSV file exists in the dataset)
    csv_preview_rows = []
    try:
        found = False
        for fm in dataset.feature_models:
            for file in fm.files:
                if file.name.lower().endswith(".csv"):
                    csv_path = os.path.join("uploads", f"user_{dataset.user_id}", f"dataset_{dataset.id}", file.name)
                    if os.path.exists(csv_path):
                        tab = TabularDataset(dataset)
                        csv_preview_rows = tab.preview(csv_path, rows=5)
                    found = True
                    break
            if found:
                break
    except Exception as exc:
        logger.exception(f"Exception while preparing CSV preview: {exc}")

    # Save the cookie to the user's browser
    user_cookie = ds_view_record_service.create_cookie(dataset=dataset)
    resp = make_response(
        render_template("dataset/view_dataset.html", dataset=dataset, csv_preview_rows=csv_preview_rows)
    )
    resp.set_cookie("view_cookie", user_cookie)

    return resp


@dataset_bp.route("/dataset/unsynchronized/<int:dataset_id>/", methods=["GET"])
@login_required
def get_unsynchronized_dataset(dataset_id):

    # Get dataset
    dataset = dataset_service.get_unsynchronized_dataset(current_user.id, dataset_id)

    if not dataset:
        abort(404)

    # Try to prepare CSV preview for unsynchronized dataset as well
    csv_preview_rows = []
    try:
        found = False
        for fm in dataset.feature_models:
            for file in fm.files:
                if file.name.lower().endswith(".csv"):
                    csv_path = os.path.join("uploads", f"user_{dataset.user_id}", f"dataset_{dataset.id}", file.name)
                    if os.path.exists(csv_path):
                        tab = TabularDataset(dataset)
                        csv_preview_rows = tab.preview(csv_path, rows=5)
                    found = True
                    break
            if found:
                break
    except Exception as exc:
        logger.exception(f"Exception while preparing CSV preview: {exc}")

    return render_template("dataset/view_dataset.html", dataset=dataset, csv_preview_rows=csv_preview_rows)


@dataset_bp.route("/dataset/unsynchronized/<int:dataset_id>/sync", methods=["POST"]) 
@login_required
def sync_unsynchronized_dataset(dataset_id):
    """Synchronize a previously saved (unsynchronized) dataset with Zenodo/fakenodo and publish it.

    If the dataset was created with the anonymous flag, publishing will expose the real authors (user action).
    """
    dataset = dataset_service.get_unsynchronized_dataset(current_user.id, dataset_id)
    if not dataset:
        abort(404)

    # Check connection to Zenodo (or fakenodo) first
    try:
        ok = zenodo_service.test_connection()
    except Exception:
        ok = False

    if not ok:
        logger.error(
            "Zenodo/fakenodo API not reachable at %s",
            getattr(zenodo_service, 'ZENODO_API_URL', 'unknown'),
        )
        flash(f"Zenodo/fakenodo API not reachable at {zenodo_service.ZENODO_API_URL}", "danger")
        return redirect(url_for("dataset.list_dataset"))

    # If dataset was marked anonymous previously, make it non-anonymous now (user chose to publish)
    if getattr(dataset.ds_meta_data, "anonymous", False):
        # Persist the change in the DB
        dataset_service.update_dsmetadata(dataset.ds_meta_data_id, anonymous=False)
        # Re-load the ds_meta_data from DB to guarantee authors and current state are present
        try:
            refreshed = dataset_service.dsmetadata_repository.get_by_id(dataset.ds_meta_data_id)
            if refreshed:
                dataset.ds_meta_data = refreshed
        except Exception:
            # Fallback: try to set the flag in-memory if reload fails
            try:
                dataset.ds_meta_data.anonymous = False
            except Exception:
                pass

    # Create deposition
    try:
        zenodo_response_json = zenodo_service.create_new_deposition(dataset)
        data = zenodo_response_json
    except Exception as exc:
        logger.exception(f"Exception while creating deposition in Zenodo: {exc}")
        flash(f"Failed to create deposition. Error details: {str(exc)}", "danger")
        return redirect(url_for("dataset.list_dataset"))

    # Accept deposition creation when either `conceptrecid` or `id` is present.
    if data.get("conceptrecid") or data.get("id"):
        deposition_id = data.get("id")
        dataset_service.update_dsmetadata(dataset.ds_meta_data_id, deposition_id=deposition_id)
        try:
            for feature_model in dataset.feature_models:
                zenodo_service.upload_file(dataset, deposition_id, feature_model)
            zenodo_service.publish_deposition(deposition_id)
            deposition_doi = zenodo_service.get_doi(deposition_id)
            # Persist DOI in DB so dataset appears as synchronized
            dataset_service.update_dsmetadata(dataset.ds_meta_data_id, dataset_doi=deposition_doi)
            logger.info("Dataset %s published with DOI %s", dataset.id, deposition_doi)
            flash(f"Dataset published successfully. DOI: {deposition_doi}", "success")
        except Exception as exc:
            logger.exception(f"Exception while uploading/publishing files: {exc}")
            flash(f"Failed to upload or publish files: {str(exc)}", "danger")
            return redirect(url_for("dataset.list_dataset"))

    # If we didn't receive a conceptrecid or id, log the response for debugging.
    logger.debug("Zenodo response during sync: %s", data)

    return redirect(url_for("dataset.list_dataset"))
