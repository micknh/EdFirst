from flask.ext.wtf import Form
from wtforms import StringField, TextAreaField, BooleanField, SelectField,\
    SubmitField, IntegerField
from wtforms.validators import Required, Length, Email, Regexp
from wtforms import ValidationError
from flask.ext.pagedown.fields import PageDownField
from ..models import Role, User


class NameForm(Form):
    name = StringField('What is your name?', validators=[Required()])
    submit = SubmitField('Submit')


class EditProfileForm(Form):
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')


class EditProfileAdminForm(Form):
    email = StringField('Email', validators=[Required(), Length(1, 64),
                                             Email()])
    username = StringField('Username', validators=[
        Required(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                          'Usernames must have only letters, '
                                          'numbers, dots or underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')


class PostForm(Form):
    body = PageDownField("What's on your mind?", validators=[Required()])
    submit = SubmitField('Submit')

class ContactForm(Form):
    fn = StringField('First Name', validators=[Length(0, 20)])
    ln = StringField('Surname', validators=[Length(0,30)])
    countryID = SelectField('Country', coerce=int)
    contactTypeID = SelectField('contactType', coerce=int)
    contact = SelectField('Contact', validators=[Length(0,45)])

class States(Form):  # pylint: disable-msg=R0903
    """
    Holds State names for the database to load during the registration page.

    SQLalchemy ORM table object which is used to load, and push, data from the
    server memory scope to, and from, the database scope.
    """
    __tablename__ = "States"

    state_id = IntegerField("state_id")
    state_name = StringField("state_name")

    def __init__(self, state_name):
        """
        Used to create a State object in the python server scope
        """
        self.state_name = state_name

class AddLanguageForm(Form):
    language = StringField('New Language', validators=[Required(), Length(1,25)])
    # def validate_language(self,field):
    #     if languages.filter_by(language=field.data).first():
    #         raise ValidationError('Language already in database.')

class AddRelationTypeForm(Form):
    relationType = StringField('New Relation Type', validators=[Required(), Length(1,25)])
    # def validate_language(self,field):
    #     if languages.filter_by(language=field.data).first():
    #         raise ValidationError('Language already in database.')