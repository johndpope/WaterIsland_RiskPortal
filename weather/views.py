from pyowm import OWM
from django.http import JsonResponse
# Create your views here.
#Todo: Initialize only Once. Do not initialize api on every request
def get_nyc_weather(request):

   api_key = 'd8e747361f1eee5489ec3c9644868ae5'
   owm = OWM(api_key)
   observation = owm.weather_at_place('New York,US')
   weather = observation.get_weather()
   weather_dict = {}
   weather_dict['temperature'] = weather.get_temperature(unit='fahrenheit')
   weather_dict['sunset_time'] = weather.get_sunset_time()
   weather_dict['humidity'] = weather.get_humidity()
   weather_dict['status'] = weather.get_detailed_status()
   weather_dict['rain'] = weather.get_rain()
   weather_dict['snow'] = weather.get_snow()


   return JsonResponse(weather_dict)

