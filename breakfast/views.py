from django.http import HttpResponse
from .models import BreakfastOrder
import datetime
# Create your views here.
def submit_breakfast_order(request):
    #Check Time. Order should be placed before 8.30
    #todo Put a try catch block and send a response in catch. Else Modal won't close
    if request.method == 'POST':
        now = datetime.datetime.time(datetime.datetime.now())
        today_8am = now.replace(hour=8,minute=30,second=0,microsecond=0)
        order = request.POST['order']
        user = request.user
        if now > today_8am:
            #Send a Warning Message
            BreakfastOrder(date=datetime.datetime.now().strftime("%Y-%m-%d %T"), order=order, user=user,status='late').save()
            response = 'Late'
        else:
            BreakfastOrder(date=datetime.datetime.now().strftime("%Y-%m-%d %T"), order=order, user=user, status='confirmed').save()
            response = 'done'


    return HttpResponse(response)