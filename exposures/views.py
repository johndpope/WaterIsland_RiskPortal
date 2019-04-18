from django.shortcuts import render
from . import exposure_utils

# Create your views here.


def get_exposures_snapshot(request):
    as_of = None
    if 'as_of' in request.GET:
        as_of = request.GET['as_of']

    exposures, _as_of, min_date, max_date = exposure_utils.get_exposure_dataframe(as_of)
    error = False
    if exposures == 'DateError':
        error = "Function not supported for the given date!"
    if exposures == 'No Data Found':
        error = "No Data Found!. Please ensure weekends/holidays are not selected."

    return render(request, 'exposures_snapshot.html', context={'exposures': exposures, 'as_of': _as_of,
                                                               'error': error,
                                                               'min_date': min_date,
                                                               'max_date': max_date})

