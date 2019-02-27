from nameko.rpc import rpc
from PIL import Image


class ResizeService:
    name = 'resize_service'

    @rpc
    def resize(self, dimensions, data):
        """
        Resizes image.

        :param dimensions: string formated like so 123x456
        :param data: binary data
    
        :returns binary data
        """
        dimensions = tuple(int(d) for d in dimensions.split('x'))

        with in_memory_image(data) as (image, output):
            resized_image = image.resize(dimensions, Image.ANTIALIAS)
            resized_image.save(output, format=image.format)

        return output.read()
