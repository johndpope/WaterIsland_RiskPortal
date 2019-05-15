"""WicPortal_Django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls import include
from django.urls import path
from django.conf.urls import url
from portal import views
from django.conf import settings
import risk_reporting
handler404 = views.handler404
handler500 = views.handler500
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    url('^index$', views.index_view,name='index'),
    url('weather/', include('weather.urls')),
    url('news/', include('wic_news.urls')),
    url('^$', views.index_view,name='index'),
    url('tweets/', include('tweets.urls')),
    url('breakfast/', include('breakfast.urls')),
    url('risk/', include('risk.urls')),
    url('portal/', include('portal.urls')),
    url('statpro/', include('statpro.urls')),
    url('notes/', include('notes.urls')),
    url('equity_fixedincome_risk_reward/', include('equity_fixedincome_risk_reward.urls')),
    url('risk_reporting/', include('risk_reporting.urls')),
    url('portfolio_analytics/', include('portfolio_analytics.urls')),
    url('realtime_pnl_impacts/', include('realtime_pnl_impacts.urls')),
    url('securities/', include('securities.urls')),
    url('exposures/', include('exposures.urls')),
    url('position_stats/', include('position_stats.urls')),
    url(r'^celeryprogressmonitor/', include('celeryprogressmonitor.urls')),
    url(r'^risk_drawdown/', include('risk_drawdown.urls')),
]


if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]


