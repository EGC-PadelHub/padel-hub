from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required
import logging

from app import db
from app.modules.auth.services import AuthenticationService
from app.modules.dataset.models import DSDownloadRecord, DataSet, DSMetaData
from app.modules.profile import profile_bp
from app.modules.profile.forms import UserProfileForm
from app.modules.profile.services import UserProfileService
from app.modules.dataset.services import DataSetService
from app.modules.dataset.models import DSDownloadRecord, DSViewRecord, DataSet, DSMetaData
from sqlalchemy import func

logger = logging.getLogger(__name__)


@profile_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    auth_service = AuthenticationService()
    profile = auth_service.get_authenticated_user_profile()
    if not profile:
        return redirect(url_for("public.index"))

    form = UserProfileForm()
    if request.method == "POST":
        service = UserProfileService()
        result, errors = service.update_profile(profile.id, form)
        return service.handle_service_response(
            result, errors, "profile.edit_profile", "Profile updated successfully", "profile/edit.html", form
        )

    return render_template("profile/edit.html", form=form)


@profile_bp.route("/profile/summary")
@login_required
def my_profile():
    page = request.args.get("page", 1, type=int)
    per_page = 5

    user_datasets_pagination = (
        db.session.query(DataSet)
        .filter(DataSet.user_id == current_user.id)
        .order_by(DataSet.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    total_datasets_count = db.session.query(DataSet).filter(DataSet.user_id == current_user.id).count()

    print(user_datasets_pagination.items)

    return render_template(
        "profile/summary.html",
        user_profile=current_user.profile,
        user=current_user,
        datasets=user_datasets_pagination.items,
        pagination=user_datasets_pagination,
        total_datasets=total_datasets_count,
    )


@profile_bp.route("/profile/metrics")
@login_required
def metrics_dashboard():
    """Personal metric dashboard for the logged in user.

    Metrics included:
    - Uploaded datasets: total datasets created by the user.
    - Downloads of my datasets: number of download records for datasets owned by this user.
    - Downloads I made: number of downloads performed by this user.
    - Views of my datasets: number of view records for datasets owned by this user.
    - Synchronizations: number of this user's datasets that have a DOI (considered synchronized).
    """
    logger.info(f"Loading metrics dashboard for user_id={current_user.id}")
    
    # Uploaded datasets
    uploaded_datasets = db.session.query(func.count(DataSet.id)).filter(DataSet.user_id == current_user.id).scalar()
    logger.info(f"Uploaded datasets: {uploaded_datasets}")

    # Downloads of datasets owned by the current user (downloads of MY datasets by anyone)
    downloads_of_my_datasets = (
        db.session.query(func.count(DSDownloadRecord.id))
        .join(DataSet, DSDownloadRecord.dataset_id == DataSet.id)
        .filter(DataSet.user_id == current_user.id)
        .scalar()
    )
    logger.info(f"Downloads of my datasets: {downloads_of_my_datasets}")

    # Downloads made by the current user (datasets I downloaded from anyone)
    downloads_i_made = (
        db.session.query(func.count(DSDownloadRecord.id))
        .filter(DSDownloadRecord.user_id == current_user.id)
        .scalar()
    )
    logger.info(f"Downloads I made: {downloads_i_made}")

    # Views of datasets owned by the current user
    views = (
        db.session.query(func.count(DSViewRecord.id))
        .join(DataSet, DSViewRecord.dataset_id == DataSet.id)
        .filter(DataSet.user_id == current_user.id)
        .scalar()
    )
    logger.info(f"Views of my datasets: {views}")

    # Synchronizations: datasets with a non-null dataset_doi
    synchronizations = (
        db.session.query(func.count(DataSet.id))
        .join(DSMetaData, DataSet.ds_meta_data_id == DSMetaData.id)
        .filter(DataSet.user_id == current_user.id, DSMetaData.dataset_doi.isnot(None))
        .scalar()
    )
    logger.info(f"Synchronizations count: {synchronizations}")

    return render_template(
        "profile/metrics_dashboard.html",
        uploaded_datasets=uploaded_datasets,
        downloads_of_my_datasets=downloads_of_my_datasets,
        downloads_i_made=downloads_i_made,
        views=views,
        synchronizations=synchronizations,
    )
