import  os
import shutil
from flask import render_template, redirect, request, url_for, flash, send_from_directory
from flask_login import login_user, logout_user, login_required, \
    current_user
from . import log_analyzer
# , processLogcat, Unzip_JoinLog
from .. import db
from ..models import *
# from ..email import send_email
from .forms import *
from ..FtpHelper import ftp_dl
# from tasks import , unzip_join_log
import time
from .. import celery
from config import Config
from ..common_func import *
from ..processLogcat import processLogcat

# # renjz: 

@log_analyzer.route('/kw_show', methods=['GET', 'POST'])
@login_required
def kw_show():
    kw_form = EditKeyForm()
    bugtype_form = BugTypeForm()

    if kw_form.validate_on_submit():
        bt_item = BugType.query.get_or_404(kw_form.bug_type.data)
        kw_item = Keyword.query.filter_by(kw_regex=kw_form.kw_regex.data).first()
        if kw_item:
            kw_item.kw_regex=kw_form.kw_regex.data
            kw_item.description=kw_form.description.data
            kw_item.test_flag=kw_form.test_flag.data
            kw_item.bug_type=bt_item
        else:
            kw_item = Keyword(kw_regex=kw_form.kw_regex.data,
                    description=kw_form.description.data,
                    test_flag=kw_form.test_flag.data,
                    bug_type=bt_item,
                    author=current_user._get_current_object())
        db.session.add(kw_item)
        return redirect(url_for('log_analyzer.kw_show'))

    if bugtype_form.validate_on_submit():
        bt_item = BugType.query.filter_by(name=bugtype_form.name.data).first()
        if bt_item:
            bt_item.name=bugtype_form.name.data
            bt_item.description=bugtype_form.description.data
        else:
            bt_item = BugType(name=bugtype_form.name.data,
                        description=bugtype_form.description.data,
                        author=current_user._get_current_object())
        db.session.add(bt_item)
        return redirect(url_for('log_analyzer.kw_show'))

    kw_id = request.args.get('kw_id', 0, type=int)
    if kw_id:
        kw = Keyword.query.get_or_404(kw_id)
        kw_form.kw_regex.data = kw.kw_regex
        kw_form.description.data = kw.description

    bt_id = request.args.get('bt_id', 0, type=int)
    if bt_id:
        bt = BugType.query.get_or_404(bt_id)
        bugtype_form.name.data = bt.name
        bugtype_form.description.data = bt.description

    kw_items = Keyword.query.order_by(Keyword.timestamp.desc())
    bt_items = BugType.query.order_by(BugType.timestamp.desc())
    # posts = pagination.items
    return render_template('log_analyzer/kw_show.html', kw_form=kw_form, bugtype_form=bugtype_form, 
            kw_items=kw_items, bt_items=bt_items)


@log_analyzer.route('/del_bt/<int:id>', methods=['GET', 'POST'])
@login_required
def del_bt(id):
    bt = BugType.query.get_or_404(id)
    db.session.delete(bt)
    flash_str = "'" + bt.name + "' have been deleted!"
    flash(flash_str)
    return redirect(url_for('log_analyzer.kw_show'))


@log_analyzer.route('/del_kw/<int:id>', methods=['GET', 'POST'])
@login_required
def del_kw(id):
    kw = Keyword.query.get_or_404(id)
    db.session.delete(kw)
    flash_str = "'" + kw.kw_regex + "' have been deleted!"
    flash(flash_str)
    return redirect(url_for('log_analyzer.kw_show'))


@log_analyzer.route('/analyzer_show', methods=['GET', 'POST'])
@login_required
def analyzer_show():
    form = AnalyzerForm()
    if form.validate_on_submit():
        ftp_url=form.ftp_url.data
        if ftp_url[-1] == '/':
            ftp_url = ftp_url[0:-1]

        print("URL is:" + ftp_url)
        ftp = ftp_dl.delay(ftp_url)
        bug_item = LogAnalyzer(ftp_url=ftp_url,
                    # title=form.title.data,
                    description=form.description.data,
                    # bug_id=form.bug_id.data,
                    # moc_id=form.moc_id.data,
                    author=current_user._get_current_object(),
                    task_id=ftp.id)
        db.session.add(bug_item)
        # try:
        #     db.session.commit()
        # except:
        #     db.session.rollback()
        flash("Add Success!")
        return redirect(url_for('log_analyzer.analyzer_show'))

    log_status = {}
    page = request.args.get('page', 1, type=int)
    pagination = LogAnalyzer.query.order_by(LogAnalyzer.timestamp.desc()).paginate(
                page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
                error_out=False)
    posts = pagination.items
    for post in posts:
        log_status[post.id] = {}
        
        log_status_file = os.path.join(get_dst_dir_from_url(post.ftp_url), 'log_join/files')
        # print(log_status_file)
        log_status[post.id]["status"] = os.path.exists(log_status_file)
        log_status[post.id]["log_dir"] = get_dir_from_url(post.ftp_url)
    return render_template('log_analyzer/analyzer_show.html', form=form, posts=posts,
                           pagination=pagination, log_status=log_status)


@log_analyzer.route('/del_ana/<int:id>', methods=['GET', 'POST'])
@login_required
def del_ana(id):
    ana = LogAnalyzer.query.get_or_404(id)
    db.session.delete(ana)
    # Delete log files.
    log_dir = get_dst_dir_from_url(ana.ftp_url)
    if os.path.exists(log_dir):
        shutil.rmtree(log_dir)
        print("remove '" + log_dir + "' Success.")

    flash_str = "'" + ana.ftp_url + "' have been deleted!"
    flash(flash_str)
    return redirect(url_for('log_analyzer.analyzer_show'))


@log_analyzer.route('/analyzer_res/<int:id>', methods=['GET', 'POST'])
@login_required
def analyzer_res(id):
    ref_html = ''
    kw_list = []

    sk_form = SelectKeywordsForm()

    ana = LogAnalyzer.query.get_or_404(id)
    log_dir = get_dst_dir_from_url(ana.ftp_url)
    log_status_file = os.path.join(log_dir, 'log_join', 'files')
    if os.path.exists(log_status_file):
        kwywords = Keyword.query.order_by(Keyword.timestamp.desc())
        for kw in kwywords:
            kw_list.append(kw.kw_regex)

    ana_res = processLogcat(src_file=os.path.join(log_dir, 'log_join', 'logcat.log.all')).process_file()

    # keywords list for log process.
    kw_format = {}
    kw_items = Keyword.query.order_by(Keyword.bugtype_id.desc())
    for kw in kw_items:
        if kw.bugtype_id not in kw_format:
            kw_format[kw.bugtype_id] = {"bt": kw.bug_type, "kw": []}
        kw_format[kw.bugtype_id]["kw"].append(kw)
    print(kw_format)

    # get log file list
    log_files = []
    for path, dirs, files in os.walk(log_dir):
        # print("path:", path, ".dirs: ", dirs)
        for file in files:
            log_abs_path = os.path.join(path, file)
            log_path = log_abs_path[len(Config.UPLOAD_FOLDER)+1: ]
            log_path_dis = log_abs_path[len(log_dir): ]
            # print('RJZ: file=' + log_path)
            log_files.append((log_path, log_path_dis))

    return render_template('log_analyzer/analyzer_res.html', sk_form=sk_form, url=ana.ftp_url,
            ana_res=ana_res, kw_format=kw_format, log_files=log_files)


@log_analyzer.route('/downloads/<path:filename>', methods=['GET', 'POST'])
@login_required
def downloads_file(filename):
    print(filename)
    # redirect(url_for('log_analyzer.analyzer_show'))
    return send_from_directory(Config.UPLOAD_FOLDER, filename, as_attachment=False)


@log_analyzer.route('/analyzer', methods=['GET', 'POST'])
# @login_required
def analyzer():
    form = AnalyzerForm()
    if form.validate_on_submit():
        ftp_url=form.ftp_url.data
        if ftp_url[-1] == '/':
            ftp_url = ftp_url[0:-1]

        print("URL is:" + ftp_url)
        ftp = ftp_dl.delay(ftp_url)
        bug_item = LogAnalyzer(ftp_url=form.ftp_url.data,
                    title=form.title.data,
                    description=form.description.data,
                    bug_id=form.bug_id.data,
                    moc_id=form.moc_id.data,
                    author=current_user._get_current_object(),
                    task_id=ftp.id)
        db.session.add(bug_item)
        # flash("Add Success!")
        # return render_template('log_analyzer/add_form.html', form=form, task_id=ftp.id)
    else:
        return render_template('log_analyzer/add_form.html', form=form)


@log_analyzer.route('/status/<task_id>')
def taskstatus(task_id):
    task = ftp_dl.AsyncResult(task_id)
    return task.state

