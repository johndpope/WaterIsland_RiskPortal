import datetime

from django.shortcuts import render

from . import exposure_utils


def get_exposures_snapshot(request):
    as_of = None
    if 'as_of' in request.GET:
        as_of = request.GET['as_of']

    exposures, _as_of, min_date, max_date = exposure_utils.get_exposure_dataframe(as_of)
    error = False
    # if not request.GET.get('as_of') and _as_of != datetime.date.today().strftime("%Y-%m-%d"):
    #     error = "<mark class='bg-danger text-white'>The following data is outdated. It is as of {as_of}</mark>".format(as_of=_as_of)
    if exposures == 'DateError':
        error = "<mark class='bg-danger text-white'>Function not supported for the given date!</mark>"
    if exposures == 'No Data Found':
        error = "<mark class='bg-danger text-white'>No Data Found!. Please ensure weekends/holidays are not selected.</mark>"

    return render(request, 'exposures_snapshot.html', context={'exposures': exposures, 'as_of': _as_of,
                                                               'error': error,
                                                               'min_date': min_date,
                                                               'max_date': max_date})
