import logging
import re
import io
import uuid
import requests

from functools import partial
from PIL import Image

from botocore.errorfactory import ClientError

from nameko.rpc import rpc, RpcProxy

from core.http import http, InvalidArgumentsError, jsonify
from core.dependencies import S3Bucket
from core.utils import compose, in_memory_image


logger = logging.getLogger(__name__)


class ImageService:
    """
    Root service. Takes image files and pipelines them.
    """
    name = 'image_service'
    """
    Name of service. Nameko uses the name of a service
    to determine what it's AMQP queues and exchange names
    are.
    """
    # Block commenting instance variables after their declaration
    # as Sphinx-doc won't accept anything else.
    image_service = RpcProxy("image_service")
    """
    proxy for a microservice to call itself
    this is useful because you can self referencial
    calls to your own service. This can be really useful
    when scaling things across multiple machines.
    """
    conversion_service = RpcProxy("conversion_service")
    rotate_service = RpcProxy("rotate_service")
    resize_service = RpcProxy("resize_service")

    bucket = S3Bucket()
    """
    S3 Bucket dependency
    """

    def _upload_file(self, file_, filename):
        try:
            image = Image.open(file_)
            image.verify()
            content_type = image.get_format_mimetype()
        except:
            raise InvalidArgumentsError('Image is malformed')
        finally:
            # resets the file
            file_.seek(0)

        key = str(uuid.uuid4())

        self.bucket.upload_file(
            key,
            file_,
            content_type,
            filename,
        )

        return key


    def _make_image_response(self, key):
        header = self.bucket.get_head(key)

        try:
            filename = header['Metadata']['filename']
        except KeyError:
            filename = None

        return {
            'id': key,
            'url': self.bucket.get_url(key),
            'content_type': header['ContentType'],
            'content_length': header['ContentLength'],
            'etag': header['ETag'],
            'filename': filename 
        }


    @http('POST', '/image/link/')
    def accept_link(self, request):
        if 'file_url' not in request.form:
            raise InvalidArgumentsError('No file')

        try:
            response = requests.get(request.form['file_url'])
            response.raise_for_status()
        except requests.exceptions.RequestException:
            raise InvalidArgumentsError('Unable to get image')

        try:
            filename = request.url.split('/')[-1]
        except IndexError:
            filename = None

        image_file = io.BytesIO(response.content)

        key = self._upload_file(image_file, filename)
        response = jsonify(self._make_image_response(key))
        response.headers['Location'] = '/image/{}/'.format(key)
        return response

    @http('POST', '/image/upload/')
    def accept_upload(self, request):
        if 'file' not in request.files:
            raise InvalidArgumentsError('No file')

        image_file = request.files['file']

        if not image_file.mimetype.startswith('image'):
            raise InvalidArgumentsError('Not an image')


        key = self._upload_file(image_file.stream, image_file.filename)
        image_file.close()
        response = jsonify(self._make_image_response(key))
        response.headers['Location'] = '/image/{}/'.format(key)
        return response


    def _create_new_image(self, request, key, operation_args):
        operations = []
        # Create partials with the arguments bound for later use
        # by the pipeline.
        operation_mapping = {
            'rotate': lambda arg: partial(
                self.rotate_service.rotate, arg
            ),
            # resize takes two args.
            'resize': lambda arg: partial(
                self.resize_service.resize, arg
            ),
            'convert': lambda arg: partial(
                self.conversion_service.convert, arg
            )
        }
        
        # Matches arguments in the form of function:arg
        lexer = re.compile('^(?P<func>[a-z]+):(?P<arg>(.*))$')
        for operation in operation_args.split('|'):
            match = lexer.match(operation)
            if match:
                group_dict = match.groupdict()
                func = group_dict['func']
                if func in operation_mapping:
                    operation = operation_mapping[func]
                    operations.append(
                        # Create and add an operation to the
                        # image pipeline
                        operation(group_dict['arg'])
                    )

        # Grab the binary data from S3
        s3_object = self.bucket.get_object(key)
        object_content = s3_object['Body'].read()

        # XXX This chains the operations. This is a non-blocking
        # eventlet call between different RPC services.
        pipeline = compose(*operations)
        transformed_image = io.BytesIO(
            # Run pipeline. Returns bytes.
            pipeline(object_content)
        )

        content_type = Image.open(transformed_image).get_format_mimetype()
        # Have to seek as we used PIL to get the mimetype from the file
        # header
        transformed_image.seek(0)
        composite_key = '{}/{}'.format(key, operation_args)

        try:
            filename = s3_object['Metadata']['filename']
        except KeyError:
            filename = None

        self.bucket.upload_file(
            composite_key,
            transformed_image,
            content_type,
            filename
        )

        return jsonify(
            self._make_image_response(composite_key), status=201
        )


    @http('GET', '/image/<string:key>/')
    @http('GET', '/image/<string:key>/<string:operation_args>/')
    def process_image(self, request, key, operation_args=None):
        try:
            if operation_args:
                composite_key = '{}/{}'.format(key, operation_args)
            else:
                composite_key = key

            return jsonify(
                self._make_image_response(composite_key), status=201
            )
        except ClientError: 
            logging.info('Could not find %s', composite_key)

        try:
            self.bucket.get_head(key)
            return self._create_new_image(request, key, operation_args)
        except ClientError:
            return jsonify({
                'error': 'file does not exist',
            }, status=404)

        return jsonify({
            'error': 'service error',
        }, status=400)
