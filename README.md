# BCG-DV Test

This is a solution to the image microservice test.
I appreciate this is over engineered by anyone's standards,
but I do so many of these tests and they're all quite similar.

So I decided to do something different, attempting to demonstrate
how Python microservices can be designed without relying on HTTP,
Flask or Django.

I appreciate I have not focused on what is normally most important
in these tests, but instead focused more on the 'at a stretch' items.

# Setup.

        docker-compose up

This will have a server running on your localhost:8000

# API docs


## Upload Image

       POST /image/upload/

Accepts formdata and a file field

        curl -X POST \
          http://localhost:8000/image/upload/ \
          -H 'Content-Type: application/x-www-form-urlencoded' \
          -H 'Content-Type: multipart/form-data; boundary=----WebKitFormBoundarygW' \
          -F file=@/home/r/Desktop/obama.jpg

Example response

        {
            "id": "b2637530-4b0b-4a1a-9ed8-1b83b0e0aac1",
            "url": "<signed aws url>"
            "content_type": "image/jpeg",
            "content_length": 47638,
            "etag": "\"a4c28a1d32459b8cb5fbed1df32e5c00\"",
            "filename": "obama.jpg"
        }

## Upload Image (with link)

        POST /image/link/

Takes a URL via form field 'file_url'

        curl -X POST \
          http://localhost:8000/image/link/ \
          -H 'Content-Type: application/x-www-form-urlencoded' \
          -F 'file_url=https://example.com/image.jpg'


Similar example response as above.


## Get Image

        GET /image/<id>/

ID is provided in the JSON response when you create an image.


## Transform Image

        GET /image/<id>/rotate:10|convert:png|scale:200x100/

This is the more complex bit of the API. There are three image operators
that you can use, rotate, convert and scale. You can use them as many
times as you need in any order. This will pipeline the image between workers.

The ID of the image will have it's transform operations appended to it's ID.
You can add more operations to transform further.


## Testing

I haven't written many due to time constraints. But I hope I've demonstrated
I at least know how.

        pip install -r requirements_test.txt
        python -m pytest tests

# Retrospective

This is more of a demo of how to build microservices using an RPC first
framework. I appreciate how it's done is not ideal.

Given more time, I would:

* either create shared memory so that each stage of the pipeline isn't passing
binary all over the place.
* implement streaming between the workers.
* implement direct transfer between workers

I would also have liked to have created a better API that handles input errors
in a more graceful manner.
