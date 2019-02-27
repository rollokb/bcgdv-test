from nameko.rpc import rpc
from PIL import Image

from core.utils import in_memory_image


class ConversionService:
    name = 'conversion_service'

    @rpc
    def convert(self, format, data):
        """
        Format the image as a new type of file.

        :param format: image format type eg jpg
        :param data: binary data
    
        :returns binary data
        """
        with in_memory_image(data) as (image, output):
            image.save(output, format=format)

        return output.read()
