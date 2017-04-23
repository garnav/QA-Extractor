#models.py
#Arnav Ghosh
#31st July 2016

from __future__ import unicode_literals

from django.db import models

#CONSTANTS
CHOICES = (('PDF', 'PDF'), ('WORD', 'WORD'), ('HTML', 'HTML'))

# Create your models here.
class Configurations(models.Model):
    """Table enables the storage of Document Conversion configurations, specifically designed to
       convert certain types of files. Each configuration consists of a:
    
    - Name (with a required version number)
    - Configuration File (as a JSON File, conforming to IBM Document Conversion Guidelines)
    - Input Type: Extension expected of the documents to convert.
    - Description: A brief explanation of the elements that help break up the input document.
      For example: For one optimized for HTML, the content it excludes may be mentioned (tables, lists etc.).
                   For PDFs or Word Documents, write down how it separates text into different headings.
                   Further Information in IBM's Document Conversion Guidelines.
    - Date Created: The date and time this Configuration row was added to the database.
    """
    name = models.CharField("Configuration Name", max_length = 200)
    config_file = models.FileField("Configuration File", upload_to = "configs") #validation:json file
    input_type = models.CharField("Expected Extension", max_length = 4, choices = CHOICES)
    description = models.CharField('Description', max_length = 400)
    created = models.DateTimeField('Date Added', auto_now_add=True) #validation: made when model created
    
    def __str__(self):
        return self.name

class toConvert(models.Model):
    """Table enables the storage of documents that will be used in IBM's Document Conversion service.
    Each toConvert consists of a:
    
    - Name
    - Document File (either a PDF,  WORD or HTML document)
    - Extension: The extension of the given document.
    - Organizataion: Notes the author of the given document.
    - Date Created: The date and time this toConvert row was added to the database.
    """
    name = models.CharField("Document Name", max_length = 200) #make this unique?
    candidate = models.FileField("Document", upload_to = "ready_convert") #validation: extension matches
    extension = models.CharField(max_length = 4, choices = CHOICES)
    organization = models.CharField(max_length = 200) #maybe change it to be of some options
    created = models.DateTimeField('Date Added', auto_now_add=True) #validation: made when model created
    
    def __str__(self):
        return self.name
   
class Converted(models.Model):
    """Table enables the storage of converted documents as procured right after conversion.
    Each converted element consists of a:
    
    - Converted From: A reference to the document it was converted from(key: toConvert)
    - Configuration Used: A reference to the configuration that was used for conversion (key: Configurations)
    - Converted File (a JSON File, as a response from IBM's Document Conversion Service)
    - Extracted: A reference to all of the title-answer documents (extractedAnswers) created from this document. 
    - Date Created: The date and time this Converted row was added to the database. 
    """
    converted_from = models.ForeignKey(toConvert) 
    config_used = models.ForeignKey(Configurations) 
    readied = models.FileField("Converted File", upload_to = "converted") #validation: json file
    extracted = models.ManyToManyField(to = 'extractedAnswers', blank=True, default = None)
    created = models.DateTimeField('Date Added', auto_now_add=True) #validation: constant
    
    
    def __init__(self,  *args, **kwargs):
        super(Converted, self).__init__(*args, **kwargs)
        self._meta.get_field_by_name('config_used')[0]._choices = configNames()
        
    def __str__(self):
        return "Converted From: " + self.converted_from.name + \
               ", Using Configuration: " + self.config_used.name + \
               ", Dated: " + str(self.created)
    
class extractedAnswers(models.Model):
    """Table enables the storage of extracted title and answers post a document conversion.
    Each extraction consists of a:
    
    - Extracted From: reference to the document answers were extracted from (key: Converted).
    - Extracted File (a JSON file of the title-answers)
    - Solr Added Yet: A boolean field that tracks whether this document has been added to the
                      solr cluster associated with IBM's Rank and Retrieve Service.
                      True indicates that is has been, False the opposite.
    - Date Created: Date and time this extractedAnswers row was added to the database. 
    """
    extracted_from = models.ForeignKey(Converted) 
    extracted_file = models.FileField("Extracted File", upload_to = "answers") #validation: json file
    solr_added = models.BooleanField(default = False)
    created = models.DateTimeField('Date Added', auto_now_add=True) #validation: constant
    
    def __str__(self):
        return "Extracted From: " + self.extracted_from + \
               ", Added to Solr: " + self.solr_added + \
               ", Dated: " + str(self.created)

#Helpers
def configNames():
    """Returns a tuple of tuples, wherein each tuple is of the form: (config_name, config_name)."""
    config_obj = Configurations.objects.all()
    choices = []
    for config in config_obj:
        choices.append((config.name, config.name))
    return tuple(choices)