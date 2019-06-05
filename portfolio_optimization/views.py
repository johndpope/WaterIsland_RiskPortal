from django.shortcuts import render
from .models import *
from django.http import HttpResponse

def ess_target_configs(request):
    # Render a response to View the current ESS configs.
    deal_type_parameters = EssDealTypearameters.objects.all()
    normalized_sizing = NormalizedSizingByRiskAdjProb.objects.all()
    soft_catalyst_sizing = SoftCatalystNormalizedRiskSizing.objects.all()

    return render(request, 'ess_targets_configs.html', {'deal_type_paramters': deal_type_parameters,
                                                        'normalized_sizing': normalized_sizing,
                                                        'soft_catalyst_sizing': soft_catalyst_sizing
                                                        }
                  )


def update_soft_catalyst_risk_sizing(request):
    response = 'Failed'
    if request.method == 'POST':
        try:
            tier = request.POST['tier']
            win_probability = request.POST['win_probability']
            loss_probability = request.POST['loss_probability']
            max_risk = request.POST['max_risk']
            avg_position = request.POST['avg_position']

            SoftCatalystNormalizedRiskSizing.objects.filter(tier__contains=tier).delete()
            SoftCatalystNormalizedRiskSizing(tier=tier, win_probability=win_probability,
                                             loss_probability=loss_probability, max_risk=max_risk,
                                             avg_position=avg_position).save()
            response = 'Success'
        except Exception as e:
            print(e)

    return HttpResponse(response)


def update_normlized_sizing_by_risk_adj_prob(request):
    response = 'Failed'
    if request.method == 'POST':
        try:
            win_probability = request.POST['win_prob']
            loss_probability = request.POST['loss_prob']
            arb_max_risk = request.POST['arb_max_risk']
            risk_adj_loss = request.POST['risk_adj_loss']
            NormalizedSizingByRiskAdjProb.objects.all().delete()
            NormalizedSizingByRiskAdjProb(win_probability=win_probability, loss_probability=loss_probability,
                                          arb_max_risk=arb_max_risk, risk_adj_loss=risk_adj_loss).save()
            response = 'Success'
        except Exception as e:
            print(e)

    return HttpResponse(response)


def ess_potential_long_shorts(request):
    all_deals = EssPotentialLongShorts.objects.all()
    return render(request, 'ess_potential_long_shorts.html', {'all_deals': all_deals})