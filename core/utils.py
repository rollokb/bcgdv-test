import io

from functools import reduce
from contextlib import contextmanager
from PIL import Image


def compose(*funcs):
    """
    Utility function to pipeline functions
    """
    return lambda x: reduce(lambda f, g: g(f), list(funcs), x)


@contextmanager
def in_memory_image(data):
    """
    Context manager to stop me from repeating
    boring IO shim operations.
    """
    input = io.BytesIO(data)
    output = io.BytesIO()

    image = Image.open(input)

    try:
        yield image, output
    finally:
        output.seek(0)
