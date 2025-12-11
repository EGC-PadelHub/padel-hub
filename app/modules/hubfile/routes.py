import os
import uuid
from datetime import datetime, timezone

from flask import current_app, jsonify, make_response, request, send_from_directory
from flask_login import current_user

from app import db
from app.modules.hubfile import hubfile_bp
from app.modules.hubfile.models import HubfileDownloadRecord, HubfileViewRecord
from app.modules.hubfile.services import HubfileDownloadRecordService, HubfileService


@hubfile_bp.route("/file/download/<int:file_id>", methods=["GET"])
def download_file(file_id):
    file = HubfileService().get_or_404(file_id)
    filename = file.name

    from app.modules.dataset.models import DataSet
    dataset = DataSet.query.get(file.dataset_id)
    directory_path = f"uploads/user_{dataset.user_id}/dataset_{file.dataset_id}/"
    parent_directory_path = os.path.dirname(current_app.root_path)
    file_path = os.path.join(parent_directory_path, directory_path)

    # Get the cookie from the request or generate a new one if it does not exist
    user_cookie = request.cookies.get("file_download_cookie")
    if not user_cookie:
        user_cookie = str(uuid.uuid4())

    # Check if the download record already exists for this cookie
    existing_record = HubfileDownloadRecord.query.filter_by(
        user_id=current_user.id if current_user.is_authenticated else None, file_id=file_id, download_cookie=user_cookie
    ).first()

    if not existing_record:
        # Record the download in your database
        HubfileDownloadRecordService().create(
            user_id=current_user.id if current_user.is_authenticated else None,
            file_id=file_id,
            download_date=datetime.now(timezone.utc),
            download_cookie=user_cookie,
        )

    # Save the cookie to the user's browser
    resp = make_response(send_from_directory(directory=file_path, path=filename, as_attachment=True))
    resp.set_cookie("file_download_cookie", user_cookie)

    return resp


@hubfile_bp.route("/file/view/<int:file_id>", methods=["GET"])
def view_file(file_id):
    file = HubfileService().get_or_404(file_id)
    try:
        # Resolve file path using service helper (handles WORKING_DIR and relationships)
        file_path = HubfileService().get_path_by_hubfile(file)

        if os.path.exists(file_path):
            # First check whether file is text (try to decode a small sample)
            # Try to detect text encoding by sampling the first bytes and attempting
            # several common encodings. If none succeed and file looks like a ZIP
            # (e.g. XLSX), treat as binary and ask the user to download instead.
            with open(file_path, "rb") as fb:
                sample = fb.read(8192)

            # If file begins with ZIP signature, it's not a plain CSV
            if sample.startswith(b"PK"):
                download_url = None
                try:
                    from flask import url_for

                    download_url = url_for("hubfile.download_file", file_id=file_id, _external=True)
                except Exception:
                    download_url = None

                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "File appears to be a binary archive (e.g. Excel .xlsx). Please download it.",
                            "download_url": download_url,
                        }
                    ),
                    400,
                )

            # List of encodings to try (utf-8 first, then common alternatives)
            encodings_to_try = ["utf-8", "utf-8-sig", "utf-16", "latin-1", "cp1252"]
            detected_encoding = None
            for enc in encodings_to_try:
                try:
                    sample.decode(enc)
                    detected_encoding = enc
                    break
                except Exception:
                    continue

            # Fallback: treat as latin-1 if nothing detected (will preserve bytes)
            if not detected_encoding:
                detected_encoding = "latin-1"

            # Read only a reasonable preview of the file to avoid huge responses
            max_preview_bytes = 200 * 1024  # 200 KB

            # Prepare view cookie early (we may return before the end)
            user_cookie = request.cookies.get("view_cookie")
            if not user_cookie:
                user_cookie = str(uuid.uuid4())

            # If this file looks like CSV (by extension or by heuristic) try to parse and return rows
            is_csv_by_ext = (
                getattr(file, "name", "").lower().endswith(".csv")
                if file and hasattr(file, "name")
                else False
            )

            # Also check heuristic: presence of commas or newlines in sample
            sample_text = None
            try:
                sample_text = sample.decode(detected_encoding, errors='replace')
            except Exception:
                sample_text = None

            looks_like_csv = False
            if sample_text:
                if ',' in sample_text or '\t' in sample_text:
                    looks_like_csv = True

            try:
                import csv
            except Exception:
                csv = None

            if csv and (is_csv_by_ext or looks_like_csv):
                rows = []
                headers = None
                max_rows = 50
                delimiter = ','
                # Attempt to sniff delimiter from sample
                try:
                    sniffer = csv.Sniffer()
                    dialect = sniffer.sniff(sample_text)
                    delimiter = dialect.delimiter
                except Exception:
                    # keep default
                    pass

                with open(file_path, 'r', encoding=detected_encoding, errors='replace') as f:
                    reader = csv.reader(f, delimiter=delimiter)
                    try:
                        for i, row in enumerate(reader):
                            if i == 0:
                                # treat first row as header if it contains non-numeric entries
                                headers = row
                            else:
                                rows.append(row)
                            if i >= max_rows:
                                break
                    except Exception:
                        # On parse errors fallback to plain text preview
                        f.seek(0)
                        text_content = f.read(max_preview_bytes)
                        if len(text_content) == max_preview_bytes:
                            text_content += (
                                "\n\n[Preview truncated: file is larger than shown, please download to see full "
                                "content]"
                            )
                        response = jsonify({"success": True, "type": "text", "content": text_content})
                        if not request.cookies.get("view_cookie"):
                            response = make_response(response)
                            response.set_cookie(
                                "view_cookie", user_cookie, max_age=60 * 60 * 24 * 365 * 2
                            )
                        return response

                # Prepare JSON response with rows (include headers separately)
                response_payload = {
                    "success": True,
                    "type": "csv",
                    "headers": headers,
                    "rows": rows,
                    "encoding": detected_encoding,
                }
                response = jsonify(response_payload)
                if not request.cookies.get("view_cookie"):
                    response = make_response(response)
                    response.set_cookie(
                        "view_cookie", user_cookie, max_age=60 * 60 * 24 * 365 * 2
                    )
                return response

            # Non-CSV fallback: read as text
            with open(file_path, "r", encoding=detected_encoding, errors="replace") as f:
                content = f.read(max_preview_bytes)
                # If file larger than preview, indicate truncated
                try:
                    f.seek(0, 2)
                    total_size = f.tell()
                except Exception:
                    total_size = None
            if total_size and total_size > len(content):
                content += "\n\n[Preview truncated: file is larger than shown, please download to see full content]"

            # Check if the view record already exists for this cookie
            existing_record = HubfileViewRecord.query.filter_by(
                user_id=current_user.id if current_user.is_authenticated else None,
                file_id=file_id,
                view_cookie=user_cookie,
            ).first()

            if not existing_record:
                # Register file view
                try:
                    new_view_record = HubfileViewRecord(
                        user_id=current_user.id if current_user.is_authenticated else None,
                        file_id=file_id,
                        view_date=datetime.now(timezone.utc),
                        view_cookie=user_cookie,
                    )
                    db.session.add(new_view_record)
                    db.session.commit()
                except Exception:
                    # Don't fail the whole request if recording the view fails
                    db.session.rollback()

            # Prepare response
            response = jsonify({"success": True, "content": content})
            if not request.cookies.get("view_cookie"):
                response = make_response(response)
                response.set_cookie("view_cookie", user_cookie, max_age=60 * 60 * 24 * 365 * 2)

            return response
        else:
            return jsonify({"success": False, "error": "File not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
