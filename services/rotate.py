from nameko.rpc import rpc
from PIL import Image

from core.utils import in_memory_image


class RotateService:
    name = 'rotate_service'

    @rpc
    def rotate(self, deg, data):
        """
        Rotates image.

        :param deg: positive or negative float in degrees
        :param data: binary data
    
        :returns binary data
        """
        deg = float(deg)
        with in_memory_image(data) as (image, output):
            rotated_image = image.rotate(deg)
            rotated_image.save(output, format=image.format)

        return output.read()

