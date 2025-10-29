from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, SubmitField, BooleanField
from wtforms.validators import NumberRange, Optional


class TabularDatasetForm(FlaskForm):
    """CSV / Tabular-specific form options.

    The file upload itself is handled by the same dropzone/endpoint used by the
    platform. This form contains metadata specific to tabular datasets.
    """
    delimiter = SelectField(
        "Delimiter",
        choices=[(',', 'Comma (,)'), (';', 'Semicolon (;)'), ('\t', 'Tab (\t)')],
        validators=[Optional()],
    )
    has_header = BooleanField("Header row", default=True)
    preview_rows = IntegerField("Preview rows", default=5, validators=[Optional(), NumberRange(min=1, max=50)])
    submit = SubmitField("Submit")
