from werkzeug.exceptions import HTTPException
from flask import redirect, Response
from flask_admin import Admin
from flask_admin.contrib import sqla
from flask_basicauth import BasicAuth
import json
from app import db
from app.models import (
    User, 
    Post, 
    Comment, 
    CommunityVisibility, 
    Community, 
    CommunityMember,
    CommunityRole,
    CommunityPost
)


def init_admin(app):
    basic_auth = BasicAuth(app)

    class AuthException(HTTPException):
        def __init__(self, message):
            super().__init__(message, Response(
                message, 401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'}
            ))

    class ModelView(sqla.ModelView):
        def is_accessible(self):
            if not basic_auth.authenticate():
                raise AuthException('Not authenticated. Refresh the page.')
            else:
                return True

        def inaccessible_callback(self, name, **kwargs):
            return redirect(basic_auth.challenge())

    admin = Admin(app)
    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(Post, db.session))
    admin.add_view(ModelView(Comment, db.session))
    admin.add_view(ModelView(Community, db.session))
    admin.add_view(ModelView(CommunityVisibility, db.session))
    admin.add_view(ModelView(CommunityMember, db.session))
    admin.add_view(ModelView(CommunityRole, db.session))
    admin.add_view(ModelView(CommunityPost, db.session))
