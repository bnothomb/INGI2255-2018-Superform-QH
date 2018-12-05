import requests
import json
from flask import url_for, current_app, render_template,redirect

FIELDS_UNAVAILABLE = ['Publication Date', 'Publication Until', 'Title']

CONFIG_FIELDS = ["access_token","Page Id"]

def render_specific_config_page(c, config_fields):
    """Render a specific template to configure a LinkedIn channel"""
    return render_template("channel_configure_linkedIn.html", channel=c, config_fields=config_fields,
                           url_token=createRequestCodeLinkedIn(current_app.config["LINKEDIN_API_KEY"],str(c.id)))

def run(publishing, channel_config):
    json_data = json.loads(channel_config)
    if 'Page Id' not in json_data:
        print("Invalid page id")
        # TODO should add log here
        return
    page_id = json_data['Page Id']
    if 'access_token' not in json_data:
        print("Invalid acces_token.")
        # TODO should add log here
        return
    access_token = json_data['access_token']
    headers = {'Authorization': 'Bearer ' + access_token, 'Host': 'api.linkedin.com', 'Connection': 'Keep-Alive',
               'x-li-format': 'json', "Content-Type": "application/json"}

    if publishing.link_url == "" and publishing.image_url == "":
        data = {"comment": publishing.description, "visibility": {"code": "anyone"}}
    else:
        data = {"comment": publishing.description, "content": {"title": "",
                "description": "",
                "submitted-url": publishing.link_url,
                "submitted-image-url": publishing.image_url},
                "visibility": {"code": "anyone"}}

    data = json.dumps(data)
    # response = requests.post("https://api.linkedin.com/v1/people/~/shares/?format=json",headers=headers,data=data)
    response = requests.post("https://api.linkedin.com/v1/companies/"+page_id+"/shares/?format=json", headers=headers,
                             data=data)
    if response.status_code != 201:
        print("Linked In publish failed")
    return response

def createRequestCodeLinkedIn(app_key,state):
    canvas_url = url_for('linkedin_callback.callback_In', _external=True)
    returnUrl = "https://www.linkedin.com/uas/oauth2/authorization?response_type=code&scope=rw_company_admin&client_id="+app_key+"&state="+state+"&redirect_uri="+canvas_url
    return returnUrl

def check_validity(channel_config):
    """ Test validity of the channel. Return an error message if any. """
    json_data = json.loads(channel_config)
    if 'access_token' not in json_data:
        print("Invalid acces_token.")
        # TODO should add log here
        return "Error : Invalid Access-Token."
    access_token = json_data['access_token']
    headers = {'Authorization': 'Bearer ' + access_token, 'Host': 'api.linkedin.com', 'Connection': 'Keep-Alive',
               'x-li-format': 'json', "Content-Type": "application/json"}
    response = requests.get("https://api.linkedin.com/v1/people/~",headers=headers)
    if response.status_code == 401:
        jd=json.loads(response.text)
        if jd['message']=='Invalid access token.':
            print("Invalid access token.")
            #TODO invalid token
            return "Error : Invalid Access-Token."
        return "Error : 401."