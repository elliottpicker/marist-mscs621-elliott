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
from flask import Flask, jsonify, request, url_for, make_response, abort
from models import Data, DataValidationError

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

######################################################################
# LIST ALL DATA
######################################################################
@app.route('/data', methods=['GET'])
def list_data():
    """ Returns all of the Datas """
    datas = []
    category = request.args.get('category')
    name = request.args.get('name')
    available = request.args.get('available')
    if category:
        datas = Data.find_by_category(category)
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
            'category': request.form['category'],
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
    data = Data(0, payload['name'], payload['category'])
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
