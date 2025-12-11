from flask_wtf import FlaskForm
from wtforms import FieldList, FormField, SelectField, StringField, SubmitField, TextAreaField
from wtforms import RadioField
from wtforms.validators import URL, DataRequired, Optional

from app.modules.dataset.models import TournamentType


class AuthorForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    affiliation = StringField("Affiliation")
    orcid = StringField("ORCID")
    gnd = StringField("GND")

    class Meta:
        csrf = False  # disable CSRF because is subform

    def get_author(self):
        return {
            "name": self.name.data,
            "affiliation": self.affiliation.data,
            "orcid": self.orcid.data,
        }


class DataSetForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    desc = TextAreaField("Description", validators=[DataRequired()])
    tournament_type = SelectField(
        "Padel Tournament Type",
        choices=[
            ("", "--"),
            ("master_final", "Master Final"),
            ("master", "Master"),
            ("open", "Open"),
            ("qualifying", "Qualifying"),
            ("national_tours", "National Tours"),
            ("other", "Other"),
        ],
        default="",
        validators=[DataRequired(message="Tournament Type is required")],
    )
    publication_doi = StringField("Publication DOI", validators=[Optional(), URL()])
    dataset_doi = StringField("Dataset DOI", validators=[Optional(), URL()])
    tags = StringField("Tags (separated by commas)")
    
    # Padel-specific metadata fields
    tournament_name = StringField("Tournament Name", validators=[Optional()])
    tournament_year = StringField("Tournament Year", validators=[Optional()])
    tournament_category = SelectField(
        "Tournament Category",
        choices=[
            ("", "Not specified"),
            ("masculino", "Masculino"),
            ("femenino", "Femenino"),
            ("mixed", "Mixed")
        ],
        validators=[Optional()]
    )
    match_count = StringField("Number of Matches", validators=[Optional()])
    
    authors = FieldList(FormField(AuthorForm))
    upload_type = RadioField(
        "Upload type",
        choices=[
            ("public", "Public dataset (published and visible to all)"),
            ("anonymous", "Anonymous public dataset"),
            ("draft", "Draft (not published)")
        ],
        default="public",
    )

    submit = SubmitField("Submit")

    def get_dsmetadata(self):

        tournament_type_converted = self.convert_tournament_type(self.tournament_type.data)

        return {
            "title": self.title.data,
            "description": self.desc.data,
            "tournament_type": tournament_type_converted,
            "publication_doi": self.publication_doi.data,
            "dataset_doi": self.dataset_doi.data,
            "tags": self.tags.data,
            # store whether this dataset should be uploaded anonymized
            "anonymous": True if getattr(self, 'upload_type', None) and self.upload_type.data == 'anonymous' else False,
        }

    def convert_tournament_type(self, value):
        """Convert form value to TournamentType enum name."""
        # Handle empty string or None as NONE
        if not value or value == "":
            return "NONE"
        for pt in TournamentType:
            if pt.value == value:
                return pt.name
        return "NONE"

    def get_authors(self):
        return [author.get_author() for author in self.authors]
