from app import ma
from app.models import (
	Post, 
	User, 
	Comment, 
	Community, 
	CommunityMember, 
	CommunityRole,
	CommunityVisibility
)


class UserSchema(ma.SQLAlchemySchema):
	class Meta:
		model = User

	id = ma.auto_field()
	email = ma.auto_field()
	full_name = ma.auto_field()
	avatar = ma.Function(lambda user: user.avatar(25))


class PostSchema(ma.SQLAlchemySchema):
	class Meta:
		model = Post

	id = ma.auto_field()
	title = ma.auto_field()
	date_posted = ma.auto_field()
	author = ma.Nested(UserSchema())
	comment_count = ma.Function(lambda post: len(post.comments))


class CommentSchema(ma.SQLAlchemySchema):
	class Meta:
		model = Comment

	id = ma.auto_field()
	content = ma.auto_field()
	date_posted = ma.auto_field()
	user = ma.Nested(UserSchema())


class CommunityVisibilitySchema(ma.SQLAlchemySchema):
	class Meta:
		model = CommunityVisibility

	id = ma.auto_field()
	name = ma.auto_field()


class CommunityRoleSchema(ma.SQLAlchemySchema):
	class Meta:
		model = CommunityRole

	id = ma.auto_field()
	name = ma.auto_field()


class CommunitySchema(ma.SQLAlchemySchema):
	class Meta:
		model = Community

	id = ma.auto_field()
	name = ma.auto_field()
	description = ma.auto_field()
	visibility = ma.Nested(CommunityVisibilitySchema())
	restrict_posting = ma.auto_field()


class CommunityMemberSchema(ma.SQLAlchemySchema):
	class Meta:
		model = CommunityMember

	user = ma.Nested(UserSchema())
	role = ma.Nested(CommunityRoleSchema())
	community = ma.Nested(CommunitySchema())
	accepted = ma.auto_field()
	invited = ma.auto_field()
