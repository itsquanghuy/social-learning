from flask import (
    render_template, 
    request, 
    current_app, 
    redirect, 
    url_for, 
    flash,
    jsonify
)
from flask_login import login_required, current_user
import json
import random
from app import db
from app.models import (
    User, 
    Post, 
    Comment, 
    Community, 
    CommunityMember,
    CommunityVisibility,
    CommunityRole,
    CommunityMember,
    CommunityPost
)
from app.main import bp
from app.main.forms import (
    EmptyForm, 
    PostForm, 
    EditProfileForm, 
    CommentForm, 
    CommunityForm,
    InviteForm
)
from app.schemas import PostSchema, CommentSchema, CommunityMemberSchema


@bp.route("/")
@bp.route("/index")
@login_required
def index():
    return render_template("index.html", title="Home Page", form=PostForm())


@bp.route("/create_post", methods=["POST"])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data, 
            content=form.content.data, 
            turn_off_commenting=form.turn_off_commenting.data,
            author=current_user
        )
        community_id = request.args.get("community_id", None, type=int)
        if community_id is not None:
            community = Community.query.filter_by(id=community_id).first()
            if not current_user.joined(community):
                return jsonify({"msg": "You are not allowed to create a post"}), 401
            community_post = CommunityPost(post=post, community=community)
            db.session.add(community_post)
        db.session.add(post)
        db.session.commit()
        return jsonify(PostSchema().dump(post))
    else:
        return jsonify({"msg": "Cannot create post"}), 400


@bp.route("/get_posts")
@login_required
def get_posts():
    page = request.args.get("page", 1, type=int)
    community_id = request.args.get("community_id", None, type=int)
    if community_id is None:
        posts = current_user.peered_posts().paginate(page, current_app.config["POSTS_PER_PAGE"], False).items
        random.shuffle(posts)
    else:
        posts = Post.query\
                    .join(CommunityPost)\
                    .filter(CommunityPost.community_id==community_id)\
                    .paginate(page, current_app.config["POSTS_PER_PAGE"], False).items
    return jsonify(PostSchema(many=True).dump(posts))


@bp.route("/create_comment/<int:post_id>", methods=["POST"])
@login_required
def create_comment(post_id):
    post = Post.query.filter_by(id=post_id).first()
    if post is None:
        return jsonify({"msg": f"Post with id {post_id} not found"}), 404
    if post.turn_off_commenting:
        return jsonify({"msg": "You are not allowed to comment on this post"}), 401
    if post.belongs_to:
        if not current_user.joined(post.belongs_to.community):
            flash("You are not allowed to read this post")
            return redirect(url_for("main.index"))
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(content=form.comment.data, post=post, user=current_user)
        db.session.add(comment)
        db.session.commit()
        return jsonify(CommentSchema().dump(comment))
    else:
        return jsonify({"msg": "Cannot create comment"}), 400


@bp.route("/edit_comment/<int:comment_id>", methods=["PUT"])
@login_required
def edit_comment(comment_id):
    form = CommentForm()
    if request.method == "PUT":
        if form.validate_on_submit():
            comment = Comment.query.filter_by(id=comment_id).first()
            if comment is None:
                return jsonify(f"Comment with id {comment_id} not found"), 404
            if comment.user.id != current_user.id:
                return jsonify({"msg": "You are not allowed to remove this comment"}), 401
            comment.content = form.comment.data
            comment.date_posted = comment.date_posted
            db.session.add(comment)
            db.session.commit()
            return jsonify(CommentSchema().dump(comment))
        else:
            return jsonify({"msg": f"Cannot edit comment with id {comment_id}"}), 400
    else:
        return jsonify({"msg": "Invalid HTTP Method"}), 405


@bp.route("/remove_comment/<int:comment_id>", methods=["DELETE"])
@login_required
def remove_comment(comment_id):
    if request.method == "DELETE":
        comment = Comment.query.filter_by(id=comment_id).first()
        if comment is None:
            return jsonify({"msg": f"Comment with id {comment_id} not found"}), 404
        if comment.user.id != current_user.id:
            return jsonify({"msg": "You are not allowed to remove this comment"}), 401
        db.session.delete(comment)
        db.session.commit()
        return jsonify(CommentSchema().dump(comment))
    else:
        return jsonify({"msg": "Invalid HTTP Method"}), 405


@bp.route("/get_comments/<int:post_id>")
@login_required
def get_comments(post_id):
    post = Post.query.filter_by(id=post_id).first()
    if post is None:
        return jsonify({"msg": f"Post with id {post_id} not found"}), 404
    if post.belongs_to:
        if not current_user.joined(post.belongs_to.community):
            return jsonify({"msg": "You are not allowed to read this post's comments"}), 401
    return jsonify(CommentSchema(many=True).dump(post.comments))


@bp.route("/post_details/<int:post_id>", methods=["GET", "POST"])
@login_required
def post_details(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    post_form = PostForm()
    if post_form.validate_on_submit():
        if post.author.id != current_user.id:
            flash("You are not allowed to edit this post")
            return redirect(url_for("main.index"))
        post.title = post_form.title.data
        post.content = post_form.content.data
        post.turn_off_commenting = post_form.turn_off_commenting.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for("main.post_details", post_id=post.id))
    elif request.method == "GET":
        post_form = PostForm()
        post_form.title.data = post.title
        post_form.content.data = post.content
        post_form.turn_off_commenting.data = post.turn_off_commenting
    return render_template(
        "post_details.html", 
        title=post.title, 
        post=post, 
        comment_form=CommentForm(),
        post_form=post_form,
        after_delete_page=request.referrer
    )


@bp.route("/remove_post/<int:post_id>")
@login_required
def remove_post(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    if post.author.id != current_user.id:
        flash("You are not allowed to remove this post")
        return redirect(url_for("main.index"))
    db.session.delete(post)
    db.session.commit()
    flash(f"{post.title} has been removed")
    return redirect(request.args.get("next"))


@bp.route("/user/<int:user_id>")
@login_required
def user(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    if not user.email_confirmed:
        flash("User not found")
        return redirect(url_for("main.index"))
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.date_posted.desc()).all()
    connection_form = EmptyForm()
    edit_profile_form = EditProfileForm()
    edit_profile_form.full_name.data = current_user.full_name
    edit_profile_form.about_me.data = current_user.about_me
    edit_profile_form.date_of_birth.data = current_user.date_of_birth
    return render_template(
        'user.html', 
        title=user.full_name, 
        user=user, 
        posts=posts, 
        connection_form=connection_form,
        edit_profile_form=edit_profile_form
    )


@bp.route('/edit_profile', methods=['POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.about_me = form.about_me.data
        current_user.date_of_birth = form.date_of_birth.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for("main.user", user_id=current_user.id))
    else:
        flash("You changes have not been saved")
        return redirect(url_for("main.user", user_id=current_user.id))


@bp.route("/peer_request/<int:user_id>", methods=["POST"])
@login_required
def peer_request(user_id):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(id=user_id).first()
        if user is None or not user.email_confirmed:
            flash(f"User not found")
            return redirect(url_for("main.index"))
        if user == current_user:
            flash("You cannot connect to yourself")
            return redirect(url_for("main.user", user_id=user.id))
        current_user.peer_request(user)
        db.session.commit()
        flash(f"You have sent a peer request to {user.full_name}")
        return redirect(url_for("main.user", user_id=user.id))
    else:
        return redirect(url_for("main.index"))


@bp.route("/cancel_peer_request/<int:user_id>", methods=["POST"])
@login_required
def cancel_peer_request(user_id):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(id=user_id).first()
        if user is None or not user.email_confirmed:
            flash(f"User not found")
            return redirect(url_for("main.index"))
        if user == current_user:
            flash("You cannot cancel yourself")
            return redirect(url_for("main.user", user_id=user.id))
        current_user.cancel_peer_request(user)
        db.session.commit()
        flash(f"You have canceled your peer request to {user.full_name}")
        return redirect(url_for("main.user", user_id=user.id))
    else:
        return redirect(url_for("main.index"))


@bp.route("/accept_peer_request/<int:user_id>", methods=["POST"])
@login_required
def accept_peer_request(user_id):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(id=user_id).first()
        if user is None or not user.email_confirmed:
            flash(f"User not found")
            return redirect(url_for("main.index"))
        if user == current_user:
            flash("You cannot cancel yourself")
            return redirect(url_for("main.user", user_id=user.id))
        current_user.accept_peer_request(user)
        db.session.commit()
        flash(f"You have accept the peer request from {user.full_name}")
        return redirect(url_for("main.user", user_id=user.id))
    else:
        return redirect(url_for("main.index"))


@bp.route("/disconnect/<int:user_id>", methods=["POST"])
@login_required
def disconnect(user_id):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(id=user_id).first()
        if user is None or not user.email_confirmed:
            flash(f"User not found")
            return redirect(url_for("main.index"))
        if user == current_user:
            flash("You cannot disconnect to yourself")
            return redirect(url_for("main.user", user_id=user.id))
        current_user.disconnect(user)
        db.session.commit()
        flash(f"You are not connected to {user.full_name}")
        return redirect(url_for("main.user", user_id=user.id))
    else:
        return redirect(url_for("main.index"))


@bp.route("/communities")
@login_required
def communities():
    my_communities = Community.query\
                            .join(CommunityMember, Community.id == CommunityMember.community_id)\
                            .filter(CommunityMember.user_id == current_user.id)\
                            .filter(CommunityMember.accepted == True)
    invited_to_join = Community.query\
                            .join(CommunityMember, Community.id == CommunityMember.community_id)\
                            .filter(CommunityMember.user_id == current_user.id)\
                            .filter(CommunityMember.accepted == False)\
                            .filter(CommunityMember.invited == True)
    return render_template(
        "communities.html", 
        title="Communities", 
        my_communities=my_communities,
        invited_to_join=invited_to_join
    )


@bp.route("/communities/<int:community_id>")
@login_required
def community(community_id):
    community = Community.query.filter_by(id=community_id).first_or_404()
    post_form = PostForm()
    community_form = CommunityForm()
    invite_form = InviteForm()
    if current_user.join_invited(community):
        return render_template(
            "community.html", 
            title=community.name, 
            community=community,
            post_form=post_form,
            community_form=community_form,
            invite_form=invite_form
        )
    if not current_user.joined(community) and community.visibility.name == "secret":
        flash(f"You are not allowed to access {community.name} community")
        return redirect(url_for("main.index"))
    community_form.name.data = community.name
    community_form.description.data = community.description
    community_form.visibility.data = community.visibility.name
    community_form.restrict_posting.data = community.restrict_posting
    return render_template(
        "community.html", 
        title=community.name, 
        community=community,
        post_form=post_form,
        community_form=community_form,
        invite_form=invite_form
    )


@bp.route('/communities/<int:community_id>/edit_profile', methods=['POST'])
@login_required
def edit_community_profile(community_id):
    form = CommunityForm()
    if form.validate_on_submit():
        community = Community.query.filter_by(id=community_id).first_or_404()
        community.name = form.name.data
        community.description = form.description.data
        community.visibility = CommunityVisibility.query.filter_by(name=form.visibility.data).first()
        community.restrict_posting = form.restrict_posting.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for("main.community", community_id=community_id))
    else:
        flash("You changes have not been saved")
        return redirect(url_for("main.community", community_id=community_id))


@bp.route("/communities/post_details/<int:post_id>", methods=["GET", "POST"])
@login_required
def community_post_details(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    if post.belongs_to:
        if post.belongs_to.community.visibility.name != "public":
            if not current_user.joined(post.belongs_to.community):
                flash("You are not allowed to read this post")
                return redirect(url_for("main.community", community_id=post.belongs_to.community.id))
    post_form = PostForm()
    if post_form.validate_on_submit():
        post.title = post_form.title.data
        post.content = post_form.content.data
        post.turn_off_commenting = post_form.turn_off_commenting.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for("main.post_details", post_id=post.id))
    elif request.method == "GET":
        post_form = PostForm()
        post_form.title.data = post.title
        post_form.content.data = post.content
        post_form.turn_off_commenting.data = post.turn_off_commenting
    return render_template(
        "community_post_details.html", 
        title=post.title, 
        post=post, 
        comment_form=CommentForm(),
        post_form=post_form,
        community=(post.belongs_to and post.belongs_to.community),
        after_delete_page=request.referrer
    )


@bp.route("/create_community", methods=["GET", "POST"])
@login_required
def create_community():
    form = CommunityForm()
    if form.validate_on_submit():
        visibility = CommunityVisibility.query.filter_by(name=form.visibility.data).first()
        community = Community(
            name=form.name.data,
            description=form.description.data,
            visibility=visibility,
            restrict_posting=form.restrict_posting.data
        )
        role = CommunityRole.query.filter_by(name="creator").first()
        member = CommunityMember(user=current_user, community=community, role=role, accepted=True, invited=False)
        db.session.add(community)
        db.session.add(member)
        db.session.commit()
        flash("Community created")
        return redirect(url_for("main.communities"))
    return render_template("create_community.html", title="Create a Community", form=form)


@bp.route("/join_community/<int:community_id>")
@login_required
def join_community(community_id):
    community = Community.query.filter_by(id=community_id).first_or_404()
    role = CommunityRole.query.filter_by(name="member").first_or_404()
    if current_user.join_invited(community):
        flash("You have been invited to join this community")
        return redirect(url_for("main.community", community_id=community_id))
    if community.visibility.name == "public":
        new_member = CommunityMember(
            user=current_user, 
            community=community, 
            role=role, 
            accepted=True, 
            invited=False
        )
    elif community.visibility.name == "private":
        new_member = CommunityMember(
            user=current_user,
            community=community,
            role=role,
            accepted=False,
            invited=False
        )
    else:
        flash("You have to be invited to join this community")
        return redirect(url_for("main.index"))
    db.session.add(new_member)
    db.session.commit()
    return redirect(url_for("main.community", community_id=community_id))


@bp.route("/cancel_join_request/<int:community_id>")
@login_required
def cancel_join_request(community_id):
    community = Community.query.filter_by(id=community_id).first_or_404()
    requested_member = current_user.join_requested(community)
    if requested_member is None:
        flash("User has not requested to join this community")
        return redirect(url_for("main.index"))
    db.session.delete(requested_member)
    db.session.commit()
    return redirect(url_for("main.community", community_id=community_id))


@bp.route("/invite/<int:community_id>", methods=["POST"])
@login_required
def invite(community_id):
    form = InviteForm()
    if form.validate_on_submit():
        community = Community.query.filter_by(id=community_id).first_or_404()
        role = CommunityRole.query.filter_by(name=form.role.data).first_or_404()
        user = User.query.filter_by(email=form.email.data).first_or_404()
        invited_member = CommunityMember(user=user, community=community, role=role, invited=True)
        db.session.add(invited_member)
        db.session.commit()
        return jsonify(CommunityMemberSchema().dump(invited_member))
    else:
        return jsonify({"msg": "Cannot invite user"}), 400


@bp.route("/decline_join_invitation/<int:community_id>")
@login_required
def decline_join_invitation(community_id):
    community = Community.query.filter_by(id=community_id).first_or_404()
    invited_member = current_user.join_invited(community)
    if invited_member is None:
        flash("You are not invited to join this community")
        return redirect(url_for("main.index"))
    db.session.delete(invited_member)
    db.session.commit()
    return redirect(url_for("main.index"))


@bp.route("/accept_join_invitation/<int:community_id>")
@login_required
def accept_join_invitation(community_id):
    community = Community.query.filter_by(id=community_id).first_or_404()
    invited_member = current_user.join_invited(community)
    if invited_member is None:
        flash("You are not invited to join this community")
        return redirect(url_for("main.index"))
    invited_member.accepted = True
    db.session.add(invited_member)
    db.session.commit()
    return redirect(url_for("main.community", community_id=community_id))


@bp.route("/leave_community/<int:community_id>")
@login_required
def leave_community(community_id):
    member = CommunityMember.query\
                .filter_by(community_id=community_id)\
                .filter_by(user_id=current_user.id)\
                .first_or_404()
    db.session.delete(member)
    db.session.commit()
    return redirect(url_for("main.communities"))


@bp.route("/delete_community/<int:community_id>")
@login_required
def delete_community(community_id):
    community = Community.query.filter_by(id=community_id).first_or_404()
    if not current_user.is_creator_of(community):
        flash("You are not allowed to delete this community")
        return redirect(url_for("main.community", community_id=community_id))
    db.session.delete(community)
    db.session.commit()
    flash(f"{community.name} has been deleted")
    return redirect(url_for("main.communities"))


@bp.route("/communities/<int:community_id>/join_requests")
@login_required
def join_requests(community_id):
    requested_members = CommunityMember.query\
                            .filter_by(community_id=community_id)\
                            .filter_by(accepted=False)\
                            .filter_by(invited=False)\
                            .all()
    return jsonify(CommunityMemberSchema(many=True).dump(requested_members))


@bp.route("/communities/<int:community_id>/approve_request/<int:user_id>", methods=["PUT"])
@login_required
def approve_request(community_id, user_id):
    if request.method == "PUT":
        if current_user.is_admin_of(Community.query.filter_by(id=community_id).first_or_404()):
            requested_member = CommunityMember.query.filter_by(community_id=community_id).filter_by(user_id=user_id).first()
            if requested_member is None:
                return jsonify({"msg": "User not found"}), 404
            if requested_member.accepted:
                return jsonify({"msg": "User has been joined this community"}), 400
            requested_member.accepted = True
            db.session.add(requested_member)
            db.session.commit()
            return jsonify(CommunityMemberSchema().dump(requested_member))
        else:
            return jsonify({"msg": "You are not allowed to approve users"}), 401
    else:
        return jsonify({"msg": "Method not allowed"}), 405


@bp.route("/communities/<int:community_id>/decline_request/<int:user_id>", methods=["DELETE"])
@login_required
def decline_request(community_id, user_id):
    if request.method == "DELETE":
        if current_user.is_admin_of(Community.query.filter_by(id=community_id).first_or_404()):
            requested_member = CommunityMember.query.filter_by(community_id=community_id).filter_by(user_id=user_id).first()
            if requested_member is None:
                return jsonify({"msg": "User not found"}), 404
            if requested_member.accepted:
                return jsonify({"msg": "User has been joined this community"}), 400
            json_returned = CommunityMemberSchema().dump(requested_member)
            db.session.delete(requested_member)
            db.session.commit()
            return jsonify(json_returned)
        else:
            return jsonify({"msg": "You are not allowed to decline users"}), 401
    else:
        return jsonify({"msg": "Method not allowed"}), 405


@bp.route("/communities/<int:community_id>/get_members")
@login_required
def get_members(community_id):
    community = Community.query.filter_by(id=community_id).first_or_404()
    if not current_user.joined(community) and community.visibility.name != "public":
        return jsonify({"msg": "You have not joined this community"}), 400
    members = CommunityMember.query.filter_by(community_id=community_id).filter_by(accepted=True).all()
    return jsonify(CommunityMemberSchema(many=True).dump(members))


@bp.route("/communities/<int:community_id>/remove_member/<int:user_id>", methods=["DELETE"])
@login_required
def remove_member(community_id, user_id):
    if request.method == "DELETE":
        member = CommunityMember.query\
                        .filter_by(community_id=community_id)\
                        .filter_by(user_id=user_id)\
                        .filter_by(accepted=True)\
                        .first_or_404()
        community = Community.query.filter_by(id=community_id).first_or_404()
        if member.role.name == "creator":
            return jsonify({"msg": "You are not allowed to remove this user"}), 401
        elif member.role.name == "admin":
            if current_user.is_creator_of(community):
                json_returned = CommunityMemberSchema().dump(member)
                db.session.delete(member)
                db.session.commit()
                return jsonify(json_returned)
            else:
                return jsonify({"msg": "You are not allowed to remove this user"}), 401
        else:
            if current_user.is_admin_of(community):
                json_returned = CommunityMemberSchema().dump(member)
                db.session.delete(member)
                db.session.commit()
                return jsonify(json_returned)
            else:
                return jsonify({"msg": "You are not allowed to remove this user"}), 401
    else:
        return jsonify({"msg": "Method not allowed"}), 405
