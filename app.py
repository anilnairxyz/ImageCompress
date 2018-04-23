# -*- coding: utf-8 -*-
"""
A flask web service API that:
    - Uses the ImageStore API to read the raw image using the identifier
    - Mocks compressions of an image file
    - Uses the ImageStore API to write the compressed file to Storage
"""
import logging
import requests
import os
import copy
from flask import Flask, request, jsonify, make_response
from logging.handlers import TimedRotatingFileHandler

app = Flask(__name__)


# Image fetch service config
app.config['IMAGE LOAD URL'] = os.environ['STORE_URL']


def _compress_image(raw_image):
    """
    Mocking a compression task
    """
    try:
        compressed_image = copy.deepcopy(raw_image)
        compressed_image['transform'] = 'compress'
        image_url = app.config['IMAGE LOAD URL']+'/upload'
        post_response = requests.post(image_url,
                                      json=compressed_image)
        if post_response.status_code != 200:
            raise Exception
        return True
    except Exception:
        return False


@app.route('/compress/<image_id>', methods=['GET'])
def compress(image_id):
    """
    Return an accepted response - 202
    """
    try:
        image_type = request.args.get('type')
        if not image_type:
            raise TypeError
        params = (('type', image_type),)
        image_url = '{u}{e}{i}'.format(u=app.config['IMAGE LOAD URL'],
                                       e='/download/',
                                       i=image_id)
        raw_image_response = requests.get(image_url, params=params)
        if raw_image_response.status_code != 200:
            raise ValueError
        raw_image = (raw_image_response.json())['image']
        if not _compress_image(raw_image):
            raise Exception
        response = {'status': 'OK',
                    'message': 'Compression completed'}
        return make_response(jsonify(response), 200)
    except TypeError as e:
        response = {'status': 'Error',
                    'message': 'Image type not specified'}
        return make_response(jsonify(response), 415)
    except ValueError:
        response = {'status': 'Error',
                    'message': 'Image not found'}
        return make_response(jsonify(response), 404)
    except Exception:
        response = {'status': 'Error',
                    'message': 'Failed to compress image'}
        return make_response(jsonify(response), 500)


@app.errorhandler(404)
def url_not_found(error):
    """
    Custom JSON error handler for 404 response
    """
    response = {'status': 'Error', 'message': 'URL not found'}
    return make_response(jsonify(response), 404)


@app.errorhandler(405)
def method_not_allowed(error):
    """
    Custom JSON error handler for 405 response
    """
    response = {'status': 'Error', 'message': 'Method not allowed'}
    return make_response(jsonify(response), 405)


@app.route("/healthcheck", methods=['GET'])
def healthcheck():
    """
    Basic healthcheck
    """
    response = {'status': 200, 'message': 'Connection fine'}
    return make_response(jsonify(response), 200)


if __name__ == '__main__':
    logfile = 'log/compress.log'
    handler = TimedRotatingFileHandler(logfile, when='midnight', interval=1)
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s %(message)s',
                                  datefmt='%d-%m-%Y %H:%M:%S')
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    app.logger.addHandler(handler)
    app.run(host='0.0.0.0', port=9000)
