from django.conf.urls import url
from . import views

urlpatterns = [
    
    url(r'^home/$', views.index, name='index'),
    
    url(r'^upload_config/$', views.upload_config, name = "Config Upload"),
    
    url(r'^upload_doc/$', views.upload_multdoc, name = "Doc Upload"),
    
    url(r'^convert/(?P<param_id>[0-9]+)/$', views.showAnswers, name = "Answers"),
    
    url(r'^convert/(?P<param_id>[PDF$|WORD$|HTML$]{3,4})/$', views.doConversion, name = "Convert"),
    
    url(r'^convert/multanswers/$', views.multAnswers, name = "Multiple Answers"),
    
    url(r'^api/v1/(?P<model>[docs$|configs$]{4,7})/$', views.model_everything, name='api_models'),
    
    url(r'^api/v1/(?P<model>[configs$]{7})/(?P<aspect>[name$]{4})/(?P<text>[\w{}]{1,200})$',
        views.model_everything, name='api_name_configs'),
    
    url(r'^api/v1/(?P<model>[configs$]{7})/(?P<aspect>[input_type$]{10})/(?P<text>[PDF$|WORD$|HTML$]{3,4})/$',
        views.model_everything, name='api_type_configs'),
    
    url(r'^api/v1/(?P<model>[configs$]{7})/(?P<given_id>[0-9]+)/$',
        views.model_id, name='api_id_configs'),
    
    url(r'^api/v1/(?P<model>[docs$]{4})/(?P<aspect>[name$]{4})/(?P<text>[\w{}]{1,200})$',
        views.model_everything, name='api_name_docs'),
    
    url(r'^api/v1/(?P<model>[docs$]{4})/(?P<aspect>[extension$]{9})/(?P<text>[PDF$|WORD$|HTML$]{3,4})/$',
        views.model_everything, name='api_ext_docs'),
    
    url(r'^api/v1/(?P<model>[docs$]{4})/(?P<given_id>[0-9]+)/$',
        views.model_id, name='api_id_docs'),
    
    url(r'^api/v1/convert/existing/$', views.convert_existing, name='convert_existing'),
    
    url(r'^api/v1/convert/new/$', views.ConvertNewView.as_view(), name='convert_new'),
    
    url(r'^api/v1/upload/doc/$', views.UploadDocView.as_view(), name='upload_doc'),
    
    url(r'^api/v1/answer/$', views.get_answers, name='get_answers')
    
    ] 