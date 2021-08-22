from flask import request
from flask_wtf import FlaskForm
from flask_ckeditor import CKEditorField
from wtforms import (
	StringField, 
	DateField, 
	SubmitField, 
	ValidationError, 
	TextAreaField, 
	BooleanField,
	RadioField,
	SelectField
)
from wtforms.validators import DataRequired, Length, Email


class PostForm(FlaskForm):
	title = StringField("Title", validators=[DataRequired(), Length(min=1, max=100)], render_kw={"placeholder": "Title"})
	content = CKEditorField("Content", validators=[DataRequired()])
	turn_off_commenting = BooleanField("Turn off commenting")
	submit = SubmitField("Post")


class EditProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    date_of_birth = DateField("Date Of Birth", format="%Y-%m-%d", render_kw={"placeholder": "yyyy-mm-dd"})
    submit = SubmitField('Save')


class CommentForm(FlaskForm):
	comment = TextAreaField("Comment", validators=[DataRequired()])
	submit = SubmitField("Send")


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class CommunityForm(FlaskForm):
	name = StringField("Name", validators=[DataRequired(), Length(min=1, max=100)])
	description = TextAreaField("Description")
	visibility = RadioField(
		"Visibility", 
		choices=[
			("public", "Public - Anyone can find and view this community, and any user can join."), 
			("private", "Private - Users can find this community, admins approve all new members."), 
			("secret", "Secret - Only users invited by an admin can find, view, and join this community.")
		],
		validators=[DataRequired()]
	)
	restrict_posting = BooleanField("Restrict Posting")
	submit = SubmitField("Create")


class InviteForm(FlaskForm):
	email = StringField("Email", validators=[DataRequired(), Email()], render_kw={"placeholder": "Email"})
	role = SelectField("Role", choices=[("admin", "Admin"), ("member", "Member")], validators=[DataRequired()])
	submit = SubmitField("Invite")
