import io

from unittest.mock import create_autospec, MagicMock
from werkzeug.wrappers import BaseRequest
from werkzeug.datastructures import FileStorage

from nameko.testing.services import worker_factory
from services.image import ImageService


def test_image_upload():
    image_service = worker_factory(ImageService)
    _make_image_response_mock = MagicMock(return_value={})
    image_service._make_image_response = _make_image_response_mock
    request = create_autospec(BaseRequest)

    # This is a 1x1 1bit png file
    with open('tests/test.png', 'rb') as f:
        image_stream = io.BytesIO(f.read())

    request.files = {
        'file': FileStorage(image_stream, 'test.png')
    }

    image_service.accept_upload(request)
    # Nameko autospecs dependencies
    assert image_service.bucket.upload_file.called
