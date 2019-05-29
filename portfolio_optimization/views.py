import datetime

from django.shortcuts import render

from portfolio_optimization import tasks


def get_portfolio_optimization(request):
    df_hard, df_soft, as_of_date = tasks.calculate_portfolio_optimization()
    as_of_date = as_of_date.strftime('%B %d, %Y')
    return render(request, 'portfolio_optimization.html', context={'df_hard': df_hard.to_json(orient='records'),
                                                                   'df_soft': df_soft.to_json(orient='records'),
                                                                   'as_of_date': as_of_date})
