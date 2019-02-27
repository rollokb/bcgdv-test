import boto3
import uuid


from nameko.extensions import DependencyProvider
from werkzeug.datastructures import FileStorage
from botocore.errorfactory import ClientError


ORIGINAL_DIR = 'original'
"""
Directory of original images
"""


class S3Wrapper:
    """
    This provides a nice wrapper around the functionality
    of the S3 Bucket.
    """
    def __init__(self, s3, bucket_name):
        self.bucket_name = bucket_name
        self.s3 = s3
    
    def upload_file(self, key, file, content_type, filename=None):
        """
        Upload a file from a Werkzurg file wrapper
        """
        return self.s3.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=file,
            ContentType=content_type,
            Metadata={
                'filename': filename
            }
        )

        return key

    def get_url(self, key):
        """
        Get a file by key.
        """
        return self.s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': self.bucket_name,
                'Key': key
            }
        )

    def get_object(self, key):
        return self.s3.get_object(Bucket=self.bucket_name, Key=key)

    def get_head(self, key):
        return self.s3.head_object(Bucket=self.bucket_name, Key=key)


class S3Bucket(DependencyProvider):
    """
    A dependency provider is the construct nameko encorages
    you to use when dealing with IO.

    It contains hooks to threading events, start, stop, kill,
    which you can use to clean up IO connections to things like
    databases and filesystems.

    The most important methods are setup and get_dependency. A rough
    overview of how they're triggered. Setup is called when the 
    Nameko service starts. 'get_dependency' is called each time a worker
    is instantiated (per request).

    What I've tried to demostrate here is setting up a session that
    should pool HTTP connections to S3 which will be shared by the
    eventlets. NOTE: this is assuming that boto3 works like Python's
    'requests' library.
    """

    def setup(self):
        self.session = boto3.session.Session(
            self.container.config['AWS_ACCESS_KEY_ID'], 
            self.container.config['AWS_ACCESS_SECRET_KEY'],
            region_name=self.container.config['AWS_REGION']
        )
            
    def get_dependency(self, worker_ctx):
        s3 = self.session.client('s3')
        bucket_name = self.container.config['AWS_BUCKET']
        return S3Wrapper(s3, bucket_name)
