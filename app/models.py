from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import current_app
from hashlib import md5
from time import time
from datetime import datetime
from time import time
import jwt
from app import db, login


peer_requests = db.Table(
    "peer_requests",
    db.Column("peer_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("peered_id", db.Integer, db.ForeignKey("user.id"), primary_key=True)
)


peers = db.Table(
    "peers",
    db.Column("peer1_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("peer2_id", db.Integer, db.ForeignKey("user.id"), primary_key=True)
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), index=True, unique=True, nullable=False)
    password = db.Column(db.String(128))
    full_name = db.Column(db.String(25), index=True, nullable=False)
    about_me = db.Column(db.String(140))
    date_of_birth = db.Column(db.Date)
    email_confirmed = db.Column(db.Boolean, nullable=False, default=False)

    posts = db.relationship("Post", backref="author", lazy="dynamic")

    peered = db.relationship(
        "User",
        secondary=peers,
        primaryjoin=(peers.c.peer1_id == id),
        secondaryjoin=(peers.c.peer2_id == id),
        backref=db.backref("peers", lazy="dynamic"),
        lazy="dynamic"
    )
    peer_requested = db.relationship(
        "User",
        secondary=peer_requests,
        primaryjoin=(peer_requests.c.peer_id == id),
        secondaryjoin=(peer_requests.c.peered_id == id),
        backref=db.backref("peer_requests", lazy="dynamic"),
        lazy="dynamic"
    )

    def __repr__(self):
        return f"<User (email={self.email}, full_name={self.full_name})>"

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def peer_request(self, user):
        if not self.is_peer_requesting(user) and not self.have_peer_request_from(user):
            self.peer_requested.append(user)

    def cancel_peer_request(self, user):
        if self.is_peer_requesting(user):
            self.peer_requested.remove(user)

    def accept_peer_request(self, user):
        if self.have_peer_request_from(user):
            self.peered.append(user)
            user.peered.append(self)
            user.peer_requested.remove(self)

    def disconnect(self, user):
        if self.is_connected(user):
            self.peered.remove(user)
            user.peered.remove(self)

    def have_peer_request_from(self, user):
        return user.peer_requested.filter(peer_requests.c.peered_id == self.id).count() > 0

    def is_peer_requesting(self, user):
        return self.peer_requested.filter(peer_requests.c.peered_id == user.id).count() > 0

    def is_connected(self, user):
        return self.peered.filter(peers.c.peer2_id == user.id).count() > 0

    def peered_posts(self):
        peered = Post.query.join(peers, (peers.c.peer2_id == Post.user_id)).filter(peers.c.peer1_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return peered.union(own).order_by(Post.date_posted.desc())

    def joined(self, community):
        return CommunityMember.query.filter_by(user_id=self.id).filter_by(community_id=community.id).filter_by(accepted=True).first()

    def join_requested(self, community):
        return CommunityMember.query\
                        .filter_by(user_id=self.id)\
                        .filter_by(community_id=community.id)\
                        .filter_by(accepted=False)\
                        .filter_by(invited=False)\
                        .first()

    def join_invited(self, community):
        return CommunityMember.query\
                        .filter_by(user_id=self.id)\
                        .filter_by(community_id=community.id)\
                        .filter_by(accepted=False)\
                        .filter_by(invited=True)\
                        .first()

    def is_admin_of(self, community):
        member = CommunityMember.query.filter_by(user_id=self.id).filter_by(community_id=community.id).first()
        return member is not None and (member.role.name == "admin" or member.role.name == "creator")

    def is_creator_of(self, community):
        member = CommunityMember.query.filter_by(user_id=self.id).filter_by(community_id=community.id).first()
        return member is not None and member.role.name == "creator"

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {"reset_password": self.id, "exp": time() + expires_in},
            current_app.config["SECRET_KEY"],
            algorithm="HS256"
        ).encode("utf-8")

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])["reset_password"]
        except Exception as e:
            print(e)
            return
        return User.query.get(id)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    turn_off_commenting = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Post (title='{self.title}', date_posted='{self.date_posted}')>"


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    user = db.relationship("User", uselist=False)
    post = db.relationship("Post", backref="comments")

    def __repr__(self):
        return f"<Comment (content='{self.content}')>"


class Community(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), index=True, nullable=False)
    description = db.Column(db.String(1000))
    visibility_id = db.Column(db.Integer, db.ForeignKey("community_visibility.id"))
    restrict_posting = db.Column(db.Boolean, default=True)

    visibility = db.relationship("CommunityVisibility", uselist=False)
    members = db.relationship("CommunityMember", cascade="all,delete", backref="community")
    posts = db.relationship("CommunityPost", cascade="all,delete", backref="community")

    def member_count(self):
        return CommunityMember.query.filter_by(community_id=self.id).filter_by(accepted=True).count()

    def __repr__(self):
        return f"<Community (name={self.name})>"


class CommunityPost(db.Model):
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), primary_key=True)
    community_id = db.Column(db.Integer, db.ForeignKey("community.id"), primary_key=True)

    post = db.relationship(
        "Post", 
        backref=db.backref("belongs_to", cascade="all,delete", uselist=False)
    )

    def __repr__(self):
        return f"<CommunityPost (title={self.post.title})>"


class CommunityVisibility(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), nullable=False)

    def __repr__(self):
        return f"<CommunityVisibility (name={self.name}>"

    def __str__(self):
        return self.name


class CommunityRole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), nullable=False)

    def __repr__(self):
        return f"<CommunityRole (name={self.name})>"

    def __str__(self):
        return self.name


class CommunityMember(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    community_id = db.Column(db.Integer, db.ForeignKey("community.id"), primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey("community_role.id"))
    accepted = db.Column(db.Boolean, default=False, nullable=False)
    invited = db.Column(db.Boolean)

    user = db.relationship("User", uselist=False)
    role = db.relationship("CommunityRole", uselist=False)

    def __repr__(self):
        return f"<CommunityMember (full_name={self.user.full_name}, role={self.role.name}, community={self.community.name})>"
