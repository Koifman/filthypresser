from flask import Flask, render_template, request, url_for, redirect, g
from flask_bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import or_, and_
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from wtforms import StringField, SubmitField
from flask_wtf import Form
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
Bootstrap(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)


@manager.command
def run():
    app.run(debug=True)


def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.String(32), unique=True)
    permalink = db.Column(db.String(1024))
    url = db.Column(db.String(1024))
    score = db.Column(db.Integer)
    title = db.Column(db.String(1024))
    author_username = db.Column(db.String(1024))
    author_flair_text = db.Column(db.String(1024))
    selftext = db.Column(db.Text())
    created_utc = db.Column(db.DateTime())


class SearchForm(Form):
    query = StringField("Regex")
    search_button = SubmitField('Search!')


@app.before_request
def create_search_form():
    g.search_form = SearchForm()


@app.route("/all_submissions/<int:page>")
@app.route("/all_submissions", defaults={'page': 1})
def all_submissions(page):
    submissions = Submission.query.order_by(Submission.id).paginate(page=page, per_page=20)
    return render_template("submissions.html", submissions_count=Submission.query.count(), submissions=submissions)


@app.route("/filthy_pressers/<int:page>")
@app.route("/filthy_pressers", defaults={'page': 1})
def filthy_pressers(page):
    regex = '(filth(y)?[ ]*presser)|(follow(er)?[ ]*(of)?[ ]*(the)?[ ]*shade)|(non-?[ ]*presser[*]forever)|(gr[ea]y[ ]*forever)'
    submissions = Submission.query.filter(and_(Submission.author_flair_text != 'non presser',
                                               Submission.author_flair_text != "can't press",
                                               Submission.author_flair_text != None))\
                                  .filter(or_(Submission.selftext.op("~")(regex),
                                              Submission.title.op("~")(regex)))\
                                  .order_by(Submission.id.desc())\
                                  .paginate(page=page, per_page=20)  # NOQA

    return render_template("submissions.html",
                           submissions_count=Submission.query.count(),
                           submissions=submissions,
                           heading="Find false greys")


@app.route("/non_pressers/<int:page>")
@app.route("/non_pressers", defaults={'page': 1})
def non_pressers(page):
    submissions = Submission.query.filter_by(author_flair_text='non presser').order_by(Submission.id.desc()).paginate(per_page=20, page=page)
    return render_template("submissions.html",
                           submissions_count=Submission.query.count(),
                           submissions=submissions,
                           heading="Convert non-pressers")


@app.route('/search', methods=['GET', 'POST'])
def search():
    if g.search_form.validate_on_submit():
        return redirect(url_for("search_results", query=g.search_form.query.data))
    else:
        return "Invalid request :("


@app.route('/search_results/<query>/<int:page>')
@app.route('/search_results/<query>', defaults={"page": 1})
def search_results(query, page):
    submissions = Submission.query.filter(Submission.selftext.op("~")(query)).order_by(Submission.id.desc()).paginate(per_page=20, page=page)

    return render_template("submissions.html", submissions_count=Submission.query.count(), submissions=submissions, heading="Search results for query [{}]".format(query))


@app.route("/")
def index():
    return redirect(url_for("filthy_pressers"))

if __name__ == "__main__":
    manager.run()
