#conv.py
#Arnav Ghosh
#30th Aug. 2016

import json
import re
import requests
from watson_developer_cloud import DocumentConversionV1, AlchemyLanguageV1, RetrieveAndRankV1
from collections import OrderedDict

#CONSTANTS

#Rank and Retrieve
USERNAME_RR = "fefebdc9-3d8a-431a-8963-34a3f812d6c9"
PASSWORD_RR = "n4AYOjnzAzmx"
CLUSTER_ID = "sc799aebd4_acd4_4df0_884f_bc1aa9eb8cb2"
CLUSTER_CONFIGURATION_NAME = 'master' #ENSURE CONFIGURATION EXISTS
COLLECTION_NAME = 'test_collection' #MAKE SURE THIS IS ALTERED WHEN A NEW COLLECTION IS MADE
RANKER_ID  = None #IMPLEMENT CORRECT ID AFTER RANKING, None if not trained
MAIN_URL = "https://gateway.watsonplatform.net/retrieve-and-rank/api/v1"

#Document Conversion
USERNAME = "7a7c4cdc-adc7-4a76-85a7-9d7bd91170c5"
PASSWORD = "jRZi5BGvIDvV"
VERSION = "2015-12-15"
TITLES_IGNORE = ["no-title"] #these titles don't usually have relevant answers.

#Alchemy API
API_KEY = "4e0c227f98c57761752ae03bfecd1a73ddece3ca"
#suggested scores, need to be changed after proper use
REL_ENT = 0.85
TAX_SCORE = 0.60
REL_KEY = 0.85
REL_CON = 0.85


def convertInput(to_convert, config):
    """ Returns a JSON file, converted from to_convert using IBM Watson's Document Conversion API.
    Uses the configurations provided in config.
    
    Parameters: to_convert must be the path to a HTML, PDF or WORD document (as a string)
                   config must be a .json file following the custom configuration
                   guidelines given in the Document Conversion documentation.
    """
    document_conversion = DocumentConversionV1(username=USERNAME,password=PASSWORD,version=VERSION)

    with open(to_convert, 'rb') as document:
        open_config = open(config)
        read_str = open_config.read()
        config = json.loads(read_str)
        converted = document_conversion.convert_document(document=document, config=config).json()
        return converted

def recoverAnswers(json_file):
    """Returns a dictionary containing the title (key) and answer (value) from the results of
    an IBM Watson Document Conversion API call.
    
    Parameter: json_file must be a .json file. Must also be the output of a document
                   conversion call with answer_units as the targeted conversion.
    """
    opened = open(json_file)
    read_str = opened.read()
    #have to use a dictionary not a string
    read_json = json.loads(read_str)
    
    answers = read_json["answer_units"]
    recovered = OrderedDict()
    for ans in answers:
        key = ans["title"]
        if key not in TITLES_IGNORE:
            value = ans["content"][0]["text"]
            recovered[key] = value
        
    return recovered

#FIX --> add to a single collection, therefore id numbers have to be fixed
def solrAdd(answer_file, doc_name):
    """Adds the contents of a finalized title-answer file as documents to a collection of a solr cluster.
    The collection is named doc_name and is configured according to the default collection schema.
    
    Parameters: answer_file is a string specifying a valid path to the title-answer file
                   doc_name is a string specifying the intended collection name.
                   Must not be the name of an existing collection
    """
    documents = alchemyAnswers(answer_file)
    with open(doc_name + '.json', "w") as json_file:
        json_file.write("{\n")
        for data in documents:
            json_file.write('"add":{{"doc":{} }},\n'.format(json.dumps(data)))
        json_file.write('"commit":{ }')
        json_file.write("}")
    

    url = MAIN_URL + "/solr_clusters/" + CLUSTER_ID +"/solr/" + COLLECTION_NAME + "/update"
    payload = open(doc_name + '.json', 'rb').read()

    requests.post(url,
                  auth = (USERNAME_RR,PASSWORD_RR),
                  data = payload,
                  headers = {'Content-Type':'application/json'})
    
def chatAnswers(query):
    """Returns, if a Ranker is configured, the answer of highest confidence from a solr cluster in
    response to a query.
    
    Parameter: query is a string of alphanumeric characters
    """
    adjusted_query = re.sub(r"\s+", '%20', query)
    if RANKER_ID == None:
        url = MAIN_URL + "/solr_clusters/" + CLUSTER_ID + "/solr/" + COLLECTION_NAME + "/select" \
            + "?q=" + adjusted_query + "&wt=json&fl=id,title,answer&df=title"
            #df=title added because solconfig has default as text(no such field exists)
    else:
        url = MAIN_URL + "/solr_clusters/" + CLUSTER_ID + "/solr/" + COLLECTION_NAME + "/fcselect" \
            + "?ranker_id=" + RANKER_ID + "&q=" + adjusted_query + "&wt=json&fl=id,title,answer,ranker.confidence"
    resp = requests.get(url, auth = (USERNAME_RR,PASSWORD_RR))
    json_resp = resp.json()
    return json_resp["response"]["docs"][0] #first answer cause that has the highest confidence

    #perhaps when the service is in further use, use tags to refine answers, instead of only ranker confidence
        
def alchemyAnswers(answer_file):
    """Returns a list of 'docs', a dictionary in which each key corresponds to a solr cluster field
    and it's value represents the data to be used for that field.
    
    Parameter: answer_file is a string representing the path to the json file containing titles
                  and their corresponding answers.
                  
    Note: Current Fields are id, title, answer, entities, taxonomy, keywords.
    """
    opened = open(answer_file)
    read_str = opened.read()
    #have to use a dictionary not a string
    read_json = json.loads(read_str)
    solr_data = []
    field_id = 1 #hard-coded id causes issues
    for ans_tuple in read_json.items():
        add_dict = {}
        tags = alchemyMain(ans_tuple)
        add_dict["title"] = ans_tuple[0]
        add_dict["answer"] = ans_tuple[1]
        add_dict['id'] = field_id
        for name in tags.keys():
            #name is multivalued in the solr schema allowing it to contain an array of tags
            add_dict[name] = tags[name]
        solr_data.append(add_dict)
        field_id = field_id + 1
    return solr_data 

def alchemyMain(answer_tuple):
    """Returns a dictionary of a list of tags procured using IBM's alchemy language API
    on a tuple of the form (title,answer).
    
    Parameter: answer_tuple must be a tuple of strings and of the form (title,answer) 
    """
    alchemy_language = AlchemyLanguageV1(api_key=API_KEY)
    send_text = re.sub(r"\s+", ' ', answer_tuple[0]) + re.sub(r"\s+", ' ', answer_tuple[1])
    results = alchemy_language.combined(text=send_text,
                                        extract=["entity", "taxonomy", "concept", "keyword"])
    
    entities = alchemyExtraction(results["entities"], "relevance", "text", REL_ENT)
    taxonomy = alchemyExtraction(results["taxonomy"], "score", "label", TAX_SCORE)            
    key = alchemyExtraction(results["keywords"], "relevance", "text", REL_KEY)
    concepts = alchemyExtraction(results["concepts"], "relevance", "text", REL_CON)
   
    #key names must be names of solr cluster fields
    return {'entities':entities, 'taxonomy':taxonomy,'keywords':key+concepts}

#Abstracting the extraction of each aspect
def alchemyExtraction(results_aspect, res_rel, res_text, benchmark):
    """ Returns a list of tags pertaining to a certain aspect of the Document Analysis
    by IBM's alchemy API.
    
    Parameters: results_aspect is a list containing dictionaries, each of which captures a
               different aspects of the text. In a wider context, results_aspect is the result
               of using a particular analysis service on text, eg: entity identification, as in
               the example below. 
               
               results_aspect example:
                [
                    {
                      "relevance": "0.89066",
                      "sentiment": {
                        "type": "positive",
                        "score": "0.234428"
                      },
                      "text": "Elliot Turner"
                    }
                ]
                
                res_rel refers to the key whose value is the score/confidence of a returned tag.
                In the example above, res_rel is 'relevance'. A single-word string of english
                alphabets. 
                
                res_text refers to the key that contains the analyzed aspect of text. In the above
                example, res_text is 'text', whose tag is 'Elliot Turner'.
                
                benchmark refers to the score/confidence above which res_tex's value should be deemed
                a tag for the analyzed document. For example, if the benchmark were 0.90, then the tag
                in the above example would be rejected. float between 0.0 and 1.0.
    """
    
    result_tags = []
    for asp in results_aspect:
        if float(asp[res_rel].encode()) > benchmark:
            #should attempt to encode here but, it gives errors
            result_tags.append(asp[res_text])
    return result_tags
