#views.py
#Arnav Ghosh
#31st July 2016

import conv
import json
import os

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse

from .models import Configurations, Converted, toConvert, extractedAnswers

from .forms import ConfigurationsForm, DocumentsForm, DoConversionForm, ExcludeSubmitForm, directSaveForm, supremeConfigForm
from django.forms import formset_factory
from django.views.generic.edit import FormView

from django.core.files import File

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import FileUploadParser, FormParser, MultiPartParser

from .serializers import ConfigurationsSerializer, toConvertSerializer, chatAnswerSerializer

from django.conf import settings

#CONSTANTS
EXT = {
    ".doc":"WORD",
    ".docx":"WORD",
    ".pdf":"PDF",
    ".html":"HTML"
    }
FORMS_PER_PAGE = 5

##############################################################################################
##############################################################################################
#                                        MAIN VIEWS
##############################################################################################
##############################################################################################

def index(request):
    """Returns a HTML template containing the app home page. """
    return render(request, 'Digest/index.html')

def upload_config(request):
    """Returns a HTML template containing an empty configuration upload form. Additionally,
    given POST as the request method, adds a new configuration to the Configurations Model.
    """
    if request.method == 'POST':
        form = ConfigurationsForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            new_form = ConfigurationsForm()
            return render(request,
                          'Digest/upload_config.html',
                          {'form': form, 'message':"Upload Successful"})
    else:
        form = ConfigurationsForm()
    return render(request,
                  'Digest/upload_config.html',
                  {'form': form, 'message':""})

def upload_multdoc(request):
    """Returns a HTML template containing FORMS_PER_PAGE empty document upload forms.
    Additionally, given POST as the request method, adds new documents to the toConvert model.
    """
    DocumentsFormSet = formset_factory(DocumentsForm, extra = FORMS_PER_PAGE, can_delete = True)
    if request.method == 'POST':
        formset = DocumentsFormSet(request.POST, request.FILES)
        if formset.is_valid():
            cleaned = formset.cleaned_data
            for each_form in cleaned:
                if len(each_form.keys()) !=0:
                    if each_form['DELETE'] == False:
                        saveDoc(each_form['doc_file'],each_form['organization'])
            formset = DocumentsFormSet()
            return render(request,
                          'doccon2/upload_doc.html',
                          {'formset':formset, 'message' : "Upload Successful"})
    else:
        formset = DocumentsFormSet()
    return render(request,
                  'doccon2/upload_doc.html',
                  {'formset':formset})

def doConversion(request, param_id):
    """Returns a HTML template containing FORMS_PER_PAGE empty conversion forms.
    Additionally, given POST as the request method, converts selected documents
    with the selected configurations, writes the result to a file, stores it in the Converted model.
    Parameters: param_id must be unicode object representing only one of the
                following 'WORD', 'HTML', 'PDF'.
    """
    ConversionFormSet = formset_factory(DoConversionForm, extra = FORMS_PER_PAGE, can_delete = True)
    if request.method == 'POST' and ('separate' in request.POST or 'supreme' in request.POST):
        formset = ConversionFormSet(request.POST, request.FILES, form_kwargs = {"input_type" : param_id})
        if formset.is_valid():
            saved_ids = []
            
            for each_form in formset.cleaned_data:
                if len(each_form.keys()) !=0 and each_form['DELETE'] == False:
                    if 'supreme' in request.POST:
                        supremeform = supremeConfigForm(request.POST, input_type = param_id)
                        if supremeform.is_valid():
                            convert_done = prepareConvert(each_form, supremeform.cleaned_data['configuration'])
                            saved_ids.append(convert_done.id)
                    elif 'separate' in request.POST:
                        #raise exception if config not chosen
                        convert_done = prepareConvert(each_form, each_form['select_config'])
                        saved_ids.append(convert_done.id)
                        
    else:
        formset = ConversionFormSet(form_kwargs = {"input_type" : param_id})
        supremeform = supremeConfigForm(request.POST, input_type = param_id)
        model_table = Configurations.objects.all().filter(input_type = param_id)
        paths = getPaths(toConvert.objects.all().filter(extension = param_id))
        return render(request,
                      'doccon2/convert.html',
                      {'formset':formset, 'supremeform':supremeform, 'model_table':model_table, 'docs':paths})
    
    if len(saved_ids) == 1:
        return HttpResponseRedirect(reverse("Answers", args=[saved_ids[0]]))
    elif len(saved_ids) > 1:
        return HttpResponseRedirect(reverse("Multiple Answers")) 
    
def showAnswers(request, param_id):
    """Returns a HTML template of a table detailing the title and answers in
    a given converted document in the Converted model. Also shows an empty
    form allowing allowing for the exclusions of certain answers before being
    written to an extractedAnswers file.
    
    Parameters: param_must be unicode object representing a integer greater than 0,
                which must be a valid id of an Converted instance.
    """
    converted = Converted.objects.get(id=param_id)
    specific_converted = converted.readied.path
    recovered_ans = conv.recoverAnswers(specific_converted)
    list_keys = recovered_ans.keys()
    
    if request.method == 'POST':
        form = ExcludeSubmitForm(request.POST, choice_list = list_keys)
        if form.is_valid():
            exclusions = form.cleaned_data['exclusions']
            for i in exclusions:
                recovered_ans.pop(i, None)
            saved_ans = writeFile("Answers_" + converted.converted_from.name, recovered_ans)
            #create and save new extracted answers
            ans_db = extractedAnswers(extracted_from = converted, extracted_file = File(open(saved_ans)))
            ans_db.save()
            #indicate that answers have been extracted for a conversion
            converted.extracted.add(ans_db)
            converted.save()
            conv.solrAdd(ans_db.extracted_file.file.name, "solr" + ans_db.extracted_from.converted_from.name)
            ans_db.solr_added = True
            return HttpResponse("Added to Solr Cluster") #must take it somwhere else though
    else:
        form = ExcludeSubmitForm(choice_list = list_keys)
    return render(request, 'doccon2/answers.html', {'recovered': recovered_ans, 'form':form})

def multAnswers(request):
    remain_extract = list(Converted.objects.all().filter(extracted = None))
    ordered_remain = remain_extract # no ordering just yet
    #add the ids in a list
    if request.method == 'POST':
        form = directSaveForm(request.POST, choice_list = remain_extract)
        if form.is_valid():
            obj_extract = form.cleaned_form['to_extract']
            for converted in obj_extract:
                ans_db = directEA(converted)
                conv.solrAdd(ans_db.extracted_file.file.name, "solr" + ans_db.extracted_from.name)
                ans_db.solr_added = True
            return HttpResponse("Success")
    else:
        form = directSaveForm(choice_list = remain_extract)
    return render(request, 'doccon2/multanswers.html', {'remaining':ordered_remain, 'form':form})

##############################################################################################
##############################################################################################
#                                        API VIEWS
##############################################################################################
##############################################################################################

@api_view(['GET'])
def model_everything(request, model, aspect='', text=''):
    """Returns, as JSON, 
    """
    if request.method == 'GET':
        if model == 'docs':
            all_objects = toConvert.objects.all()
            if aspect != '' and text != '':
                all_objects = all_objects.filter(**{aspect:text})
            serializer = toConvertSerializer(all_objects, many=True)
        elif model == 'configs':
            all_objects = Configurations.objects.all()
            if aspect != '' and text != '':
                all_objects = all_objects.filter(**{aspect:text})
            serializer = ConfigurationsSerializer(all_objects, many=True)  
        return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
def model_id(request, model, given_id):
    given_id = int(given_id)
    if request.method == 'GET':
        if model == 'docs':
            all_objects = toConvert.objects.get(id=given_id)
            serializer = toConvertSerializer(all_objects)
        elif model == 'configs':
            all_objects = Configurations.objects.get(id=given_id)
            serializer = ConfigurationsSerializer(all_objects)  
        return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
def convert_existing(request):
    if request.method == 'POST':
        doc_id = int(request.data.get('doc_id'))
        config_id = int(request.data.get('config_id'))
        doc = toConvert.objects.all().get(id=doc_id)
        config = Configurations.objects.all().get(id=config_id)
        converted = createConvert(doc, config)
        ans_db = directEA(converted)
        conv.solrAdd(ans_db.extracted_file.file.name, "solr" + \
                     ans_db.extracted_from.converted_from.name)
        ans_db.solr_added = True
        return Response(status=status.HTTP_201_CREATED)
    return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def get_answers(request):
    if request.method == 'POST':
        query = request.data.get('query')
        try:
            answer = conv.chatAnswers(query)
            serializer = chatAnswerSerializer(answer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
class ConvertNewView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request, format=None):
        """Performs an IBM Document Conversion on a document not in the database based on the
        given configuration. In the process creates a database entry for the document, the
        converted file and extracted answers. Also adds the final title-answer document to the
        solr collection. 
        """
        file_obj = request.data.get('file')
        organization = request.data.get('org')
        config_id = int(request.data.get('config_id'))
        
        #save instance of document in toConvert
        doc = saveDoc(file_obj, 'test')
        config = Configurations.objects.all().get(id=config_id)
        
        converted = createConvert(doc, config)
        ans_db = directEA(converted)
        conv.solrAdd(ans_db.extracted_file.file.name, "solr_" + ans_db.extracted_from.name)
        ans_db.solr_added = True
        return Response(status=status.HTTP_201_CREATED)

class UploadDocView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request, format=None):
        file_obj = request.data.get('file')
        organization = request.data.get('org')
        
        #save instance of document in toConvert
        doc = saveDoc(file_obj, 'test')
        return Response(status=status.HTTP_201_CREATED)
    
##############################################################################################
##############################################################################################
#                                        FILE MANAGING HELPERS
##############################################################################################
##############################################################################################

def writeFile(name, to_write):
    """Returns the name of the JSON file to which the data to_write is written.
    Preconditions: name is a string without "." or intended extension.
                   to_write is a  .dictionary"""
    with open(name + ".json", 'w') as fp:
        #saves to a file with the json formatting still intact
        json.dump(to_write, fp, indent = 2)
    return name + ".json"

#fix
def getPaths(obj_list):
    """Returns the storage paths relative to the MEDIA URL of the objects given in obj_list
    Preconditions: obj_list is a list of model instances, in which 'candidate' is a reference to the file.
    """
    paths = []
    for doc in obj_list:
        new_path = doc.candidate.path[doc.candidate.path.index("store")+6:] # have to replace this with MEDIA URL
        print doc.candidate.path[doc.candidate.path.index("store"):]
        print settings.MEDIA_URL
        paths.append(new_path)
    return paths

##############################################################################################
##############################################################################################
#                                        MODEL HELPERS
##############################################################################################
##############################################################################################

def prepareConvert(each_form, configuration):
    """ Returns an object of Converted from a document reference from each form converted
        with configuration.
    
    Parameters: each_form is a validated DoConversionForm
                configuration is a reference to a configuration from the Configurations model
                returned in a form.
    """
    
    convert_done = None
    if each_form['select_doc'] != None and len(each_form['organization']) == 0 and each_form['doc_file'] == None:
        #normal conversion (with existing doc)
        convert_done = createConvert(each_form['select_doc'], supremeform.cleaned_data['configuration'])
    elif each_form['doc_file'] != None and len(each_form['organization']) != 0 and each_form['select_doc'] == None:
        #doc upload stuff
        doc = saveDoc(each_form['doc_file'],each_form['organization'])
        convert_done = createConvert(doc, supremeform.cleaned_data['configuration'])
        
    return convert_done

def createConvert(doc_chosen,config_chosen):
    """Returns an instance of the converted model reprsenting a given conversion performed with the
    given document and configuration. 
    Parameters: doc_chosen is a instance of the toConvert model.
                   config_chosen is a instance of the Configurations model."""
    converted = conv.convertInput(doc_chosen.candidate.path, config_chosen.config_file.path)
    saved_name = writeFile("Converted_" + doc_chosen.name, converted)
    convert_done = Converted(converted_from = doc_chosen, readied = File(open(saved_name)),
                                config_used = config_chosen)
    convert_done.save()
    return convert_done

def saveDoc(form_doc,org):
    """Returns an instance of the toConvert model representing an uploaded document.
    Parameters: form_doc is an uploaded document object. 
                org is a string representing the organization the document belongs too
    """
    doc_name = form_doc.name
    file_extension = EXT[os.path.splitext(doc_name)[1]]
    to_name = os.path.splitext(doc_name)[0]
    new_toconvert = toConvert(name = to_name, candidate = form_doc,
                                    extension = file_extension, organization = org)
    new_toconvert.save()
    return new_toconvert

def directEA(converted):
    """Returns an extractedAnswer object created directly from the reference Converted object,
    ie: without any modifications to the title-answers. In the process, saves the extractedAnswer object,
    ensures that the Converted object points to it and saves the Converted object.
    """
    ans_db = extractedAnswers(extracted_from = converted, extracted_file = converted.readied)
    ans_db.save()
    converted.extracted.add(ans_db)
    converted.save()
    return ans_db