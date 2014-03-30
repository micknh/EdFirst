from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask.ext.login import login_required, current_user
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm
from ..models import Permission, Role, User, Post
from ..decorators import admin_required, permission_required

# def populate_blogform_choices(blog_form):
#     blog_form.authorid_select_field.choices = [(g.id, g.name) for g in users.query.order_by('id')]
#     blog_form.languageid_select_field.choices = [(g.languageid, g.language) for g in languages.query.order_by('languageid')]

# @main.route('/relations')
# def rel():
#     return render_template("relationships.html")

@main.route('/ehome')
def ehome():
    return render_template('home.html')

@main.route('/about')
def about():
    return render_template("AboutUs.html")

@main.route('/pil')
def pil():
    return render_template("ParentInformationLetter.html")

@main.route('/approach')
def approach():
    return render_template("OurApproach.html")

@main.route('/adenviro')
def adenviro():
    return render_template("TodaysAdmissionEnvironment.html")

@main.route('/placement')
def placement():
    return render_template("PlacementServices.html")

@main.route('/testimonial')
def testimonial():
    return render_template("Testimonials.html")

@main.route('/contact')
def contact():
    return render_template("ContactUs.html")

@main.route('/gameplan')
def gameplan():
    return render_template("GamePlan.html")

@main.route('/secretstuff')
def secretstuff():
    return render_template("SecretStuff.html")

@main.route('/blogentry')
def blogentry():
    return render_template("BlogEntry.html")






# @main.route('/brdg')
# def aboutUs():
#     return render_template('brdg.html')

@main.route('/info')
def info():
    return render_template('RequestInformation.html')

@main.route('/cinfo')
def cinfo():
    return render_template('Chinese/cRequestInformation.html')

@main.route('/chineseAboutUs')
def aboutUsC():
    return render_template('Chinese/aboutUs.html')    

@main.route('/chinese')
def brdgC():
    return render_template('Chinese/brdg.html')  

@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():
        post = Post(body=form.body.data,
                    author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    show_followed = False
    if current_user.is_authenticated():
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts,
                           show_followed=show_followed, pagination=pagination)


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts,
                           pagination=pagination)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/post/<int:id>')
def post(id):
    post = Post.query.get_or_404(id)
    return render_template('post.html', posts=[post])

@main.route('/post/new')
def newpost():
    return render_template('post.html', posts=[post])


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash('The post has been updated.')
        return redirect(url_for('.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('You are now following %s.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('You are not following this user.')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash('You are not following %s anymore.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followers of",
                           endpoint='.followers', pagination=pagination,
                           follows=follows)


@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)


@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp


# @main.route('/contact')
# @login_required
# def show_ContactForm():
#     contact = ContactForm()
#     return render_template('contact.html', contact=contact)

# @main.route('/add-language', methods=['GET', 'POST'])
# @login_required
# def add_language():
#     form = AddLanguageForm()
#     if form.validate_on_submit():
#         db.session.add(language)
#         db.session.commit()
#         flash('The language has been added.')
#         return redirect(url_for('main.index'))
#         flash('Language Inserted')
#     else:
#         flash('Insert my Language.')
#         return render_template("language.html", form=form)
#     return redirect(url_for('index'))

# @main.route('/add-relationType', methods=['GET', 'POST'])
# @login_required
# def add_relationType():
#     form = AddRelationTypeForm()
#     if form.validate_on_submit():
#         db.session.add(relationType)
#         db.session.commit()
#         flash('The relationType has been added.')
#         return redirect(url_for('main.index'))
#         flash('relationType Inserted')
#     else:
#         flash('Insert my relationType.')
#         return render_template("relationType.html", form=form)
#     return redirect(url_for('index'))

# @main.route('/blog', methods=['GET', 'POST'])
# def postBlog():
#     id = None
#     blog_form = BlogForm()
#     # populate_blogform_choices(blog_form)
#     #This means that if we're not sending a post request then this if statement
#     #will always fail. So then we just move on to render the template normally.
#     if request.method == 'POST' and blog_form.validate():
#         #If we're making a post request and we passed all the validators then
#         #create a registered user model and push that model to the database.
#         flash('author_select_field')
#         blog_post = Posts(
#             title=blog_form.data['title_field'],
#             post=blog_form.data['post_field'],
#             authorid=blog_form.data['author_select_field'],
#             languageid=blog_form.data['language_select_field'],
#             # translate= blog_form.data['translate_field']
#             # translator = blog_form.data['translator_field']
#             trandate=blog_form.data['trandate_field'],
#             active=blog_form.data['active_field'])
#         db.session.add(blog_post)
#         db.session.commit()
#         return render_template(
#             template_name_or_list='successpost.html',
#             blog_form=blog_form)
#     return render_template(
#             template_name_or_list='blogpost.html',
#             blog_form=blog_form)    
