from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, HiddenField, TextAreaField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from flask_pagedown.fields import PageDownField
from ..models import *
from .. import db

# class SelectKeywordsForm(Form):
#     bugID = HiddenField()
#     bug_type = SelectField('BugType', coerce=int)
#     submit = SubmitField('Submit')

class EditKeyForm(Form):
    kw_ID = HiddenField()
    kw_regex = StringField('Keyword(Regex):', validators=[Required(), Length(0, 64)])
    description = StringField('Description:', validators=[Length(0, 128)])
    comment = StringField('Comment:', validators=[Length(0, 512)])
    # test_flag = StringField('For Test?(1/0)', validators=[Length(0, 64)])
    bug_type = SelectField('BugType', coerce=int)
    # test_flag = BooleanField('Just for test?')
    submit = SubmitField('Submit')

    # def validate_kw_regex(self, field):
    #     if Keyword.query.filter_by(kw_regex=field.data).first():
    #         raise ValidationError('Keyword already Added.')


class BugTypeForm(Form):
    bt_ID = HiddenField()
    name = StringField('BugType:', validators=[Required(), Length(0, 64)])
    description = StringField('Description:', validators=[Length(0, 64)])
    submit = SubmitField('Submit')

    # def validate_name(self, field):
    #     if BugType.query.filter_by(name=field.data).first():
    #         raise ValidationError('BugType already Added.')


class AnalyzerShowForm(Form):
    search = StringField('search:', validators=[Length(0, 64)])
    # title = StringField('title:', validators=[Length(0, 64)])
    # description = StringField('Description:', validators=[Length(0, 64)])
    # bug_id = StringField('bug_id:', validators=[Length(0, 12)])
    # moc_id = StringField('moc_id:', validators=[Length(0, 12)])
    # test_flag = BooleanField('Just for test?')
    submit = SubmitField('Submit')

class AnalyzerForm(Form):
    ftp_url = StringField('ftp url:', validators=[Required(), Length(0, 140)])
    # title = StringField('title:', validators=[Length(0, 64)])
    description = StringField('Description:', validators=[Length(0, 64)])
    # bug_id = StringField('bug_id:', validators=[Length(0, 12)])
    # moc_id = StringField('moc_id:', validators=[Length(0, 12)])
    # test_flag = BooleanField('Just for test?')
    submit = SubmitField('Submit')

    def validate_ftp_url(self, field):
        url = field.data
        if url[-1] == '/':
            url = url[0:-1]
            
        if LogAnalyzer.query.filter_by(ftp_url=url).first():
            raise ValidationError('FTP url already Added.')

