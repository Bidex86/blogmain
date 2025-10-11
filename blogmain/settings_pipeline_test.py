from .settings import *

# Override Pipeline settings for testing
PIPELINE['PIPELINE_ENABLED'] = True
STATICFILES_STORAGE = 'pipeline.storage.PipelineStorage'