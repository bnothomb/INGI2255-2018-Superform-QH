import os
import tempfile

import pytest

from superform import app, db
from superform.models import Channel
from superform.plugins import facebook


def clear_data(session):
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        session.execute(table.delete())
    session.commit()

@pytest.fixture
def client():
    app.app_context().push()

    db_fd, database = tempfile.mkstemp()
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///"+database+".db"
    app.config['TESTING'] = True
    client = app.test_client()

    with app.app_context():
        db.create_all()

    yield client

    clear_data(db.session)
    os.close(db_fd)
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///superform.db"


def login(client, login):
    with client as c:
        with c.session_transaction() as sess:
            if login is not "myself":
                sess["admin"] = True
            else:
                sess["admin"] = False

            sess["logged_in"] = True
            sess["first_name"] = "gen_login"
            sess["name"] = "myname_gen"
            sess["email"] = "hello@genemail.com"
            sess['user_id'] = login

def prefill_db(client, name, module):
    chan = Channel(name=name, id=-1, module=module, config='')
    db.session.add(chan)
    db.session.commit()
    return chan


def test_valid_module(client):
    try:
        from superform.plugins.facebook import run
    except ImportError:
        assert False

    assert 'FIELDS_UNAVAILABLE' in dir(facebook)
    assert 'CONFIG_FIELDS' in dir(facebook)


def test_valid_facebook_configuration(client):
    assert "FACEBOOK_APP_ID" in client.application.config
    assert "FACEBOOK_APP_SECRET" in client.application.config

def test_callback_no_param(client):
    """ No parameters given on callback -> redirected to channels """
    login(client, "admin")
    rv = client.get('/callback_fb', follow_redirects=True)
    rv2 = client.get('/channels', follow_redirects=True)
    assert rv.status_code == 200
    assert rv2.status_code == 200
    assert rv.data == rv2.data

def test_callback_wrong_state(client):
    """ Wrong channel id given on callback -> redirected to channels """
    login(client, "admin")
    rv = client.get('/callback_fb?state=wrong&code=42', follow_redirects=True)
    rv1 = client.get('/callback_fb?state=1000000&code=42', follow_redirects=True)
    rv2 = client.get('/channels', follow_redirects=True)
    assert rv.status_code == 200
    assert rv1.status_code == 200
    assert rv2.status_code == 200
    assert rv1.data == rv2.data
    assert rv.data == rv2.data

def test_callback_state_not_fb(client):
    """ Received channel id is not a facebook channel -> redirected to channels """
    login(client, "admin")
    chan = prefill_db(client, 'test_fb_mail', 'superform.plugins.mail')

    rv = client.get('/callback_fb?state=' + str(chan.id) + '&code=42', follow_redirects=True)
    rv2 = client.get('/channels', follow_redirects=True)
    assert rv.status_code == 200
    assert rv2.status_code == 200
    assert rv.data == rv2.data


def test_callback_state_ok_wrong_code(client):
    """ Received channel id is a facebook channel but invalid code -> redirected to channel's config page """
    login(client, "admin")
    chan = prefill_db(client, 'test_fb', 'superform.plugins.facebook')

    rv = client.get('/callback_fb?state='+str(chan.id)+'&code=42', follow_redirects=True)
    channel_conf = Channel.query.get(chan.id).config
    assert 'Unable to generate access_token' in channel_conf
