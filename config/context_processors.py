import os 

def export_env(request):
    return {
        'ENV': os.getenv('ENV')
    }