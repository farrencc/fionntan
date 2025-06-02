#!/usr/bin/env python
import os
from app import create_app, celery

# Create Flask app context
app = create_app(os.getenv('FLASK_ENV', 'development'))
app.app_context().push()

# The celery app is now configured with Flask's config
if __name__ == '__main__':
    celery.start()
