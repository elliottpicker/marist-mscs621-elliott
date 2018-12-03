# Copyright 2016, 2017 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Data API Controller

This modules provides a REST API for the Data Model

Paths:
-----
GET /data - Lists all of the Datas
GET /data/{id} - Retrieves a single Data with the specified id
POST /data - Creates a new Data 
PUT /data/{id} - Updates a single Data with the specified id
DELETE /data/{id} - Deletes a single Data with the specified id
POST /data/{id}/purchase - Action to purchase a Data
"""

import os
import sys
import logging
from os.path import join, dirname
import time
import json
import pkg_resources
from flask import Flask, jsonify, request, url_for, make_response, abort, render_template, send_file
from models import Data, DataValidationError
from watson_developer_cloud import LanguageTranslatorV3, TextToSpeechV1, ToneAnalyzerV3
from watson_developer_cloud.tone_analyzer_v3 import ToneInput

# Create Flask application
app = Flask(__name__)
app.config['LOGGING_LEVEL'] = logging.INFO

# Pull options from environment
DEBUG = (os.getenv('DEBUG', 'False') == 'True')
PORT = os.getenv('PORT', '5000')

# Status Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_404_NOT_FOUND = 404
HTTP_409_CONFLICT = 409

#connect to bluemix services
language_translator = LanguageTranslatorV3(version="2018-05-01",iam_apikey="zOCdlSPJlp95Mp5FuyRS9p8n71I38IuFh9rPHV2JeBN8")
ttsservice = TextToSpeechV1(iam_apikey='PyalNFzdVXqBtZhmuWKGc24FWDKy40s2ML2ViCcJD6MU')
toneservice = ToneAnalyzerV3(version='2017-09-21',iam_apikey='UKUNeYDmOJErX1Q93ry146WPLwh2i0Zep0__yvCdlI6a')


######################################################################
# Error Handlers
######################################################################
@app.errorhandler(DataValidationError)
def request_validation_error(error):
    """ Handles Value Errors from bad data """
    return bad_request(error)

@app.errorhandler(400)
def bad_request(error):
    """ Handles bad reuests with 400_BAD_REQUEST """
    message = error.message or str(error)
    app.logger.info(message)
    return jsonify(status=400, error='Bad Request', message=message), 400

@app.errorhandler(404)
def not_found(error):
    """ Handles resources not found with 404_NOT_FOUND """
    message = error.message or str(error)
    app.logger.info(message)
    return jsonify(status=404, error='Not Found', message=message), 404

@app.errorhandler(405)
def method_not_supported(error):
    """ Handles unsuppoted HTTP methods with 405_METHOD_NOT_SUPPORTED """
    message = error.message or str(error)
    app.logger.info(message)
    return jsonify(status=405, error='Method not Allowed', message=message), 405

@app.errorhandler(415)
def mediatype_not_supported(error):
    """ Handles unsuppoted media requests with 415_UNSUPPORTED_MEDIA_TYPE """
    message = error.message or str(error)
    app.logger.info(message)
    return jsonify(status=415, error='Unsupported media type', message=message), 415

@app.errorhandler(500)
def internal_server_error(error):
    """ Handles unexpected server error with 500_SERVER_ERROR """
    message = error.message or str(error)
    app.logger.info(message)
    return jsonify(status=500, error='Internal Server Error', message=message), 500


######################################################################
# GET INDEX
######################################################################
@app.route('/')
def index():
    """ Send back the home page """
    return app.send_static_file('index.html')
	
@app.route('/test')
def indextest():
    """ Send back the home page """
    return app.send_static_file('indextest.html')	
	
@app.route('/chat', methods=['POST'])
def chat():
    """ Send back the home page """
    chatuser=request.form['name']
    messages=sorted(json.loads(list_data().get_data().decode("utf-8")),reverse=True)
    return render_template('chat.html', **locals())

@app.route('/translate')
def translate():
    
    """get the text of the message with msgid """
    msgidn=request.args.get('msgid')
    msgtxt=json.loads(get_data(msgidn).get_data().decode("utf-8"))
    return render_template('translate.html', **locals())
    
@app.route('/detect')   
def detect():
    
    """get the text of the message with msgid """
    msgidn=request.args.get('msgid')
    msgtxt=json.loads(get_data(msgidn).get_data().decode("utf-8"))
    detin=(u' '+msgtxt.get("text")).encode('utf-8').strip()
    detresp=language_translator.identify(detin).get_result().get("languages")[0]
    dectlang=convlang(detresp.get("language"))
    dectconf=detresp.get("confidence")
    

    return render_template('detected.html', **locals())    
    
    
@app.route('/analysis')
def analysis():
    
    """get the text of the message with msgid """
    msgidn=request.args.get('msgid')
    msgtxt=json.loads(get_data(msgidn).get_data().decode("utf-8"))
    response=toneservice.tone(tone_input=(u' '+msgtxt.get("text")).encode('utf-8').strip(),content_type="text/plain").get_result(),                  
    return render_template('analysis.html', **locals())
    
@app.route('/translated')
def translated():
    
    """get the text of the message with msgid """
    msgidn=request.args.get('msgid')
    msgtxt=json.loads(get_data(msgidn).get_data().decode("utf-8"))
    langin=str(request.args.get('lfrom'))
    langout=str(request.args.get('lto'))
    # get the translated output
    trnsin=(u' '+msgtxt.get("text")).encode('utf-8').strip()
    translation = language_translator.translate(text=trnsin, model_id=langin+"-"+langout).get_result()
    trnsout=translation.get("translations").pop().get("translation")
    # convert languages from 2 letters to full language
    langin=convlang(langin)
    langout=convlang(langout)
    return render_template('translated.html', **locals())    

@app.route('/speak')
def speak():
    """get the text of the message with msgid """
    msgidn=request.args.get('msgid')
    msgtxt=json.loads(get_data(msgidn).get_data().decode("utf-8"))
    spchin=(u' '+msgtxt.get("text")).encode('utf-8').strip()
    dir_path=os.path.abspath("test.txt")
    wavfilename="output"+msgidn+".wav"
    with open(wavfilename,'wb') as audio_file:
        response = ttsservice.synthesize(
            spchin, accept='audio/wav',
            voice="en-US_LisaVoice").get_result()
        audio_file.write(response.content)
   
    
    return send_file(wavfilename,mimetype="audio/wav",as_attachment=True,attachment_filename=wavfilename)

# converts 2 letter abbreviations used by language translator services
def convlang(inlang):
    if inlang == "en":
        return "English"     
    if inlang == "ar":
        return "Arabic"
    if inlang == "cs":
        return "Czech"
    if inlang == "da":
        return "Danish"
    if inlang == "de":
        return "German"
    if inlang == "es":
        return "Spanish"
    if inlang == "fi":
        return "Finnish"
    if inlang == "fr":
        return "French"
    if inlang == "hi":
        return "Hindi"
    if inlang == "it":
        return "Italian"
    if inlang == "ja":
        return "Japanese"
    if inlang == "ko":
        return "Korean"
    if inlang == "nb":
        return "Norwegian Bokmal"
    if inlang == "nl":
        return "Dutch"
    if inlang == "pl":
        return "Polish"
    if inlang == "pt":
        return "Portuguese"
    if inlang == "ru":
        return "Russian"
    if inlang == "sv":
        return "Swedish"
    if inlang == "tr":
        return "Turkish"
    if inlang=="zh":
        return "Simplified Chinese"
    return "unknown language"

######################################################################
# LIST ALL DATA
######################################################################
@app.route('/data', methods=['GET'])
def list_data():
    """ Returns all of the Datas """
    datas = []
    text = request.args.get('text')
    name = request.args.get('name')
    available = request.args.get('available')
    if text:
        datas = Data.find_by_text(text)
    elif name:
        datas = Data.find_by_name(name)
    elif available:
        datas = Data.find_by_availability(available)
    else:
        datas = Data.all()

    results = [data.serialize() for data in datas]
    return make_response(jsonify(results), HTTP_200_OK)

######################################################################
# RETRIEVE A DATA
######################################################################
@app.route('/data/<int:data_id>', methods=['GET'])
def get_data(data_id):
    """
    Retrieve a single Data 

    This endpoint will return a Data based on it's id
    """
    data = Data.find(data_id)
    if not data:
        abort(HTTP_404_NOT_FOUND, "Data with id '{}' was not found.".format(data_id))
    return make_response(jsonify(data.serialize()), HTTP_200_OK)

######################################################################
# ADD A NEW DATA
######################################################################
@app.route('/data', methods=['POST']) 
def create_data():
    """
    Creates a Data

    This endpoint will create a Data based the data in the body that is posted
    or data that is sent via an html form post.
    """
    item = {}
    # Check for form submission data
    if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
        app.logger.info('Processing FORM data')
        item = {
            'name': request.form['name'],
            'text': request.form['text'],
            'available': request.form['available'].lower() in ['true', '1', 't']
        }
    else:
        app.logger.info('Processing JSON data')
        item = request.get_json()

    data = Data()
    data.deserialize(item)
    data.save()
    message = data.serialize()
    return make_response(jsonify(message), HTTP_201_CREATED,
                         {'Location': url_for('get_data', data_id=data.id, _external=True)})
						 
######################################################################
# ADD A NEW MEssage
######################################################################
@app.route('/message', methods=['POST'])
def create_message():
    """
    Creates a Data

    This endpoint will create a Data based the data in the body that is posted
    or data that is sent via an html form post.
    """
    item = {}
    # Check for form submission data
    if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
        app.logger.info('Processing FORM data')
        item = {
            'name': request.form['name'],
			'timestamp': time.time(),
            'text': request.form['text'],
            'available': request.form['available'].lower() in ['true', '1', 't']
        }
    else:
        app.logger.info('Processing JSON data')
        item = request.get_json()

    data = Data()
    data.deserialize(item)
    data.save()
    message = data.serialize()
    chatuser=request.form['name']
    messages=sorted(json.loads(list_data().get_data().decode("utf-8")),reverse=True)
    return render_template('chat.html', **locals())						 

######################################################################
# UPDATE AN EXISTING DATA
######################################################################
@app.route('/data/<int:data_id>', methods=['PUT'])
def update_data(data_id):
    """
    Update a Data

    This endpoint will update a Data based the body that is posted
    """
    data = Data.find(data_id)
    if not data:
        abort(HTTP_404_NOT_FOUND, "Data with id '{}' was not found.".format(data_id))
    data.deserialize(request.get_json())
    data.id = data_id
    data.save()
    return make_response(jsonify(data.serialize()), HTTP_200_OK)


######################################################################
# DELETE A DATA 
######################################################################
@app.route('/data/<int:data_id>', methods=['DELETE'])
def delete_data(data_id):
    """
    Delete a Data

    This endpoint will delete a Data based the id specified in the path
    """
    data = Data.find(data_id)
    if data:
        data.delete()
    return make_response('', HTTP_204_NO_CONTENT)

######################################################################
# PURCHASE A DATA 
######################################################################
@app.route('/data/<int:data_id>/purchase', methods=['PUT'])
def purchase_data(data_id):
    """ Purchase a Data """
    data = Data.find(data_id)
    if not data:
        abort(HTTP_404_NOT_FOUND, "Data with id '{}' was not found.".format(data_id))
    if not data.available:
        abort(HTTP_400_BAD_REQUEST, "Data with id '{}' is not available.".format(data_id))
    data.available = False
    data.save()
    return make_response(jsonify(data.serialize()), HTTP_200_OK)


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################

@app.before_first_request
def init_db(redis=None):
    """ Initlaize the model """
    Data.init_db(redis)

# load sample data
def data_load(payload):
    """ Loads a Data into the database """
    data = Data(0, payload['name'], payload['text'])
    data.save()

def data_reset():
    """ Removes all Datas from the database """
    Data.remove_all()

# @app.before_first_request
def initialize_logging(log_level):
    """ Initialized the default logging to STDOUT """
    if not app.debug:
        print 'Setting up logging...'
        # Set up default logging for submodules to use STDOUT
        # datefmt='%m/%d/%Y %I:%M:%S %p'
        fmt = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        logging.basicConfig(stream=sys.stdout, level=log_level, format=fmt)
        # Make a new log handler that uses STDOUT
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(fmt))
        handler.setLevel(log_level)
        # Remove the Flask default handlers and use our own
        handler_list = list(app.logger.handlers)
        for log_handler in handler_list:
            app.logger.removeHandler(log_handler)
        app.logger.addHandler(handler)
        app.logger.setLevel(log_level)
        app.logger.info('Logging handler established')


######################################################################
#   M A I N
######################################################################
if __name__ == "__main__":
    print "************************************************************"
    print "        P E T   R E S T   A P I   S E R V I C E "
    print "************************************************************"
    initialize_logging(app.config['LOGGING_LEVEL'])
    app.run(host='0.0.0.0', port=int(PORT), debug=DEBUG)
