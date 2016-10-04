from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseRedirect, HttpResponse, JsonResponse, HttpResponseServerError
from django.core.urlresolvers import reverse
from django.views import generic
from django.utils import timezone
from .models import *
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from helpers import *
import json, collections
from django.core import serializers
from django.contrib.auth.mixins import LoginRequiredMixin
from utils import *


class IndexView(generic.ListView):
    template_name = 'manati_ui/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
		"""
		Return the last five published questions (not including those set to be
		published in the future).
		"""
		return ''

class AnalysisSessionNewView(generic.DetailView):
    model = AnalysisSession
    template_name = 'manati_ui/analysis_session/new.html'

@login_required(login_url="/")
def new_analysis_session_view(request):
    # lastest_question_list = Question.objects.order_by('-pub_date')[:5]
    # output = ', '.join([q.question_text for q in lastest_question_list])
    context = {}
    return render(request, 'manati_ui/analysis_session/new.html', context)

#ajax connexions
@login_required(login_url="/")
@csrf_exempt
def create_analysis_session(request):
    analysis_session_id = -1
    # try:
    if request.method == 'POST':
        current_user = request.user
        filename = str(request.POST.get('filename', ''))
        u_data_list = json.loads(request.POST.get('data[]',''))
        u_key_list = json.loads(request.POST.get('keys[]',''))
        analysis_session = AnalysisSession.objects.create(filename, u_key_list, u_data_list,current_user)

        if not analysis_session :
            # messages.error(request, 'Analysis Session wasn\'t created .')
            return HttpResponseServerError("Error saving the data")
        else:
            # messages.success(request, 'Analysis Session was created .')
            analysis_session_id = analysis_session.id
            return JsonResponse(dict(data={'analysis_session_id': analysis_session_id}, msg='Analysis Session was created .' ))

    else:
        messages.error(request, 'Only POST request')
        return HttpResponseServerError("Only POST request")
    # except Exception as e:
    #     messages.error(request, 'Error Happened')
    #     data = {'dd': 'something', 'safe': True}
    #     # return JsonResponse({"nothing to see": "this isn't happening"})
    #     return render_to_json(request, data)


def update_analysis_session(request):
    return JsonResponse({'foo': 'bar'})

def convert(data):
    if isinstance(data, basestring):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data

@login_required(login_url="/")
@csrf_exempt
def sync_db(request):
    try:
        if request.method == 'POST':
            received_json_data = json.loads(request.body)
            analysis_session_id = received_json_data['analysis_session_id']
            data = convert(received_json_data['data'])

            wb_query_set = AnalysisSession.objects.sync_weblogs(analysis_session_id, data)
            return JsonResponse(dict(data=serializers.serialize("json", wb_query_set), msg='Sync DONE'))
        else:
            messages.error(request, 'Only POST request')
            return HttpResponseServerError("Only POST request")
    except Exception as e:
        print_exception()
        return HttpResponseServerError("There was a error in the Server")

@login_required(login_url="/")
@csrf_exempt
def sync_metrics(request):
    try:
        if request.method == 'POST':
            current_user = request.user
            u_measurements = json.loads(request.POST.get('measurements[]', ''))
            u_keys = json.loads(request.POST.get('keys[]', ''))
            Metric.objects.create_bulk_by_user(u_measurements, current_user)
            json_data = json.dumps({'msg': 'Sync Metrics DONE',
                                    'measurements_length': len(u_measurements), 'keys': u_keys})
            return HttpResponse(json_data, content_type="application/json")
        else:
            return HttpResponseServerError("Only POST request")
    except Exception as e:
        print_exception()
        return HttpResponseServerError("There was a error in the Server")

@login_required(login_url="/")
@csrf_exempt
def get_weblogs(request):
    try:
        if request.method == 'GET':
            analysis_session_id = request.GET.get('analysis_session_id', '')
            analysis_session = AnalysisSession.objects.get(id=analysis_session_id)
            return JsonResponse(dict(weblogs=serializers.serialize("json", analysis_session.weblog_set.all()), analysissessionid=analysis_session_id, name=analysis_session.name))
        else:
            messages.error(request, 'Only GET request')
            return HttpResponseServerError("Only GET request")
    except Exception as e:
        print_exception()
        return HttpResponseServerError("There was a error in the Server")



class IndexAnalysisSession(LoginRequiredMixin,generic.ListView):
    login_url = '/'
    redirect_field_name = 'redirect_to'
    model = AnalysisSession
    template_name = 'manati_ui/analysis_session/index.html'
    context_object_name = 'analysis_sessions'

    def get_queryset(self):
        #Get the analysis session created by the admin (old website) and the current user
        user = self.request.user
        return AnalysisSession.objects.filter(users__in=[1, user.id])


class EditAnalysisSession(LoginRequiredMixin, generic.DetailView):
    login_url = '/'
    redirect_field_name = 'redirect_to'
    model = AnalysisSession
    template_name = 'manati_ui/analysis_session/edit.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(EditAnalysisSession, self).get_context_data(**kwargs)
        object = super(EditAnalysisSession, self).get_object()
        # Add in a QuerySet of all the books
        # context['weblogs'] = serializers.serialize("json",object.weblog_set.all())
        context['analysis_session_id'] = object.id
        return context



