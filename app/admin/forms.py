"""
WTForms definitions for the Admin CMS.
Includes validation for photos, videos, literature, and settings.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    BooleanField,
    DateField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, EqualTo, Length, Optional


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")


class PhotoForm(FlaskForm):
    photo_file = FileField(
        "Photo File",
        validators=[
            FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only (JPG, PNG, WebP)"),
        ],
    )
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    category = StringField("Category", default="Training Sessions")
    tags = StringField("Tags (comma separated)", default="training, corporate")
    caption = TextAreaField("Caption", validators=[Optional()])
    alt_text = StringField("Alt Text (Descriptive & Natural)", validators=[Optional()])
    description = TextAreaField("Description", validators=[Optional()])
    date = StringField("Date / Year", default="2026")
    location = StringField("Location", default="West Bengal, India")
    featured = BooleanField("Featured on Homepage", default=True)
    primary_profile = BooleanField("Primary Profile Image (Site-wide Hero & Schema)", default=False)
    published = BooleanField("Published (Live on Public Site)", default=True)
    submit = SubmitField("Save Photo")


class VideoForm(FlaskForm):
    video_file = FileField(
        "Video File (MP4/WebM)",
        validators=[
            FileAllowed(["mp4", "webm", "mov", "m4v"], "Videos only (MP4, WebM, MOV)"),
        ],
    )
    poster_file = FileField(
        "Poster / Thumbnail Image",
        validators=[
            FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only (JPG, PNG, WebP)"),
        ],
    )
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    category = StringField("Category", default="Technical Presentations")
    tags = StringField("Tags (comma separated)", default="video, presentation")
    description = TextAreaField("Description", validators=[Optional()])
    date = StringField("Date / Year", default="2026")
    transcript = TextAreaField("Transcript (Optional)", validators=[Optional()])
    featured = BooleanField("Featured on Homepage", default=True)
    published = BooleanField("Published (Live on Public Site)", default=True)
    submit = SubmitField("Save Video")


class LiteratureForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    content_type = SelectField(
        "Content Type",
        choices=[
            ("Essay", "Essay"),
            ("Thought", "Thought"),
            ("Poetry", "Poetry"),
            ("Prose", "Prose"),
            ("Short Story", "Short Story"),
            ("Article", "Article"),
            ("Other", "Other"),
        ],
        default="Essay",
    )
    short_description = TextAreaField("Short Description / Excerpt", validators=[DataRequired()])
    body = TextAreaField("Body (Markdown Supported)", validators=[DataRequired()])
    tags = StringField("Tags (comma separated)", default="literature, perspective")
    publication_date = StringField("Publication Date (YYYY-MM-DD)", default="2026-01-01")
    featured = BooleanField("Featured on Homepage", default=True)
    published = BooleanField("Published (Live on Public Site)", default=True)
    submit = SubmitField("Save Literature")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            Length(min=10, message="Password must be at least 10 characters long."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(),
            EqualTo("new_password", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Update Password")
