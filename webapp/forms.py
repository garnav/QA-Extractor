#forms.py
#Arnav Ghosh
#10 Sept. 2016

from django import forms
from doccon2.models import Configurations, toConvert
from django.forms import ModelForm
from material import Layout, Row, Span3

class ConfigurationsForm(ModelForm):
    """ Provides a form to allow users to easily input configuartions for the conversion.
    Specifically, allows the input of a name, a configuration file, it's target conversion
    type and a description of what it does. 
    """
    class Meta:
        model = Configurations
        fields = ['name', 'config_file', 'input_type', 'description']
        help_texts = {
            'config_file': ('JSON file, along the guidelines given \
                      in Document Conversion\'s documentation.'),
            'input type':('Specifies the type of file that may be used with this configuration.'),
            'description':('Keep a note of what the configuration is designed to do. \
                           Perhaps describe the type of content the configuration helps sift through. \
                           For example: For one optimized for HTML pages, write down the content \
                           it explicity excludes (tables, lists etc.). For PDFs or Word Documents, \
                           write down how it separates text into different headings.')
        }
        widgets = {
            'description': forms.Textarea 
        }
        labels = {
            'config_file': 'File',
            'name':'Name'
        }
        
        layour = Layout('name',
                        Row('config_file', 'input_type'),
                        Span3('description'))

class DocumentsForm(forms.Form):
    """ Provides a form to allow users to easily input documents to be converted.
    Specifically, allows the input of a document file and an organization tag.
    Names and extensions are handled elsewhere. 
    """
    doc_file = forms.FileField(label = 'Document',
                               help_text = 'A PDF, WORD or HTML document.')
    organization = forms.CharField(max_length = 200,
                                   label = 'Organization')
    
class DoConversionForm(forms.Form):
    """Provides a form to allow users to select documents and configurations for conversion.
    Organizes documents and configurations available before creating the form. Fields are optional
    to allow this form to be used with other ones, ie: supremeConfigForm. Allows users to:

    - Choose documents and associate each with a configuration.
    """
    select_config = forms.ModelChoiceField(queryset = Configurations.objects.all(),
                                           help_text ='Choose a configuration. Ensure it\'s input_type \
                                                       matches the selected document\'s extension',
                                           label = "Configuration:", required = False)
    select_doc = forms.ModelChoiceField(queryset = toConvert.objects.all(),
                                        help_text = 'Choose a document to convert. It\'s extension must \
                                                     match the selected configuration\'s input_type.',
                                        widget = forms.RadioSelect, required = False)
    doc_file = forms.FileField(label = 'Document',
                               help_text = 'A PDF, WORD or HTML document.',
                               required = False)
    organization = forms.CharField(max_length = 200,
                                   label = 'Organization',
                                   required = False)

    def __init__(self, *args, **kwargs):
        check_type = kwargs.pop("input_type")
        super(DoConversionForm,self).__init__(*args, **kwargs)
        self.fields['select_config'].queryset = Configurations.objects.all().filter(input_type = check_type)
        self.fields['select_doc'].queryset = toConvert.objects.all().filter(extension = check_type)

class ExcludeSubmitForm(forms.Form):
    exclusions = forms.MultipleChoiceField(widget = forms.CheckboxSelectMultiple)
    
    def __init__(self, *args, **kwargs):
        choice_list = kwargs.pop("choice_list")
        super(ExcludeSubmitForm,self).__init__(*args, **kwargs)
        self.fields['exclusions'].choices = createTuple(choice_list)
        
class directSaveForm(forms.Form):
    to_extract = forms.MultipleChoiceField(widget = forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        choice_list = kwargs.pop("choice_list")
        super(directSaveForm,self).__init__(*args, **kwargs)
        self.fields['to_extract'].choices = createTuple(choice_list)
        
class supremeConfigForm(forms.Form):
    """ Supplements DoConversionForm by creating a form that allows one configuration to
    be applied to all chosen documents.
    """
    configuration = forms.ModelChoiceField(queryset = Configurations.objects.all(),
                                           help_text ='Only select if you plan to use one \
                                                       configuration for all documents.',
                                           label = "Supreme Configuration:", required=False)
    
    def __init__(self, *args, **kwargs):
        check_type = kwargs.pop("input_type")
        super(supremeConfigForm,self).__init__(*args, **kwargs)
        self.fields['configuration'].queryset = Configurations.objects.all().filter(input_type = check_type)

#Helpers       
def createTuple(to_list):
    final_list = []
    for ele in to_list:
        tup = (ele,to_list.index(ele))
        final_list.append(tup)
        
    return tuple(final_list)