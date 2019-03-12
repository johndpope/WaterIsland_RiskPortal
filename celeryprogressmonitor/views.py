import json
from django.http import HttpResponse
from celery_progress.backend import Progress
import decimal


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError


def get_celery_task_progress(request):
    task_id = str(request.GET['task_id'])
    progress = Progress(task_id)
    return HttpResponse(json.dumps(progress.get_info(), default=decimal_default), content_type='application/json')
