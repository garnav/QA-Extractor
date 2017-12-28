# QA Extractor
Part of a pilot project for **Inayo**, this is a web application that uses **IBM Watson** APIs to automatically extract question-answer pairs from company manuals and FAQ pages.

The application was designed to support a Chat-Bot that would connect customers to Inayo's medical partners. Consequently, users would then be able to ask questions about insurance policies, medicine usage and disease monitoring. Conventionally, data for such a Chat-Bot would be acquired by manually sifting through documents to create question-answer pairs. However, with this application, existing manuals and FAQ pages can simply be uploaded and these pairs will be automatically produced.

## Getting Started
The application uses Django 1.9, python 2.7 and a PostgreSQL database.

## Usage

### Uploading a Configuration
In most manuals and FAQ pages, potential questions or question topics can be differentiated from the rest of the text by their different formatting; either through bolded text or using text size or colour. Thus, constructing the right configuration for IBM Watson's Document Conversion API is important because it allows this app to correctly differentiate questions and their answers.

This repository contains a few sample configurations that generally work well for HTML, PDF and word documents.

#### Sample Configuration (PDF)
```
{   "conversion_target":"answer_units",
    "pdf": {
    		"heading": {
    		"fonts": [
                {"level": 1, "min_size": 24},
                {"level": 2, "min_size": 18, "max_size": 23},
                {"level": 3, "min_size": 13.5, "max_size": 17},
                {"level": 4, "min_size": 12, "max_size": 13}
            	]
        	}
    },
    "normalized_html":{  
    	"exclude_tags_completely":["script", "sup"],
    	"exclude_tags_keep_content":["font", "em", "span", "li"]
     },
    "answer_units": {
    	"selector_tags": ["h1","h2","h3"]
	}
}
```

Two parts of the configuration are particularly important:
* **Heading**: Allows you to use text sizes to differentiate between questions and answers. The above sizes have been tuned by experimenting with over 20 sample documents.
* **Normalized HTML**: Allows you to specify how specially formatted text should be treated. For example, the above configuration considers information contained in lists to be the answer to the most recent question.

The above configuration has been created using specifications from [here](https://console.bluemix.net/docs/services/document-conversion/customizing.html#advanced-customization-options). 

### Obtaining QA Pairs
Documents can then be converted using any of the uploaded configurations.

#### Conversion Interface
<img src="https://github.com/garnav/ChatDoc-2016/blob/master/images/convert.JPG" width="800">

#### Actual FAQ Page
<img src="https://github.com/garnav/ChatDoc-2016/blob/master/images/actual_page.PNG" width="800">

#### Retrieved QA
<img src="https://github.com/garnav/ChatDoc-2016/blob/master/images/answer.JPG" width="800">

## Contributors
* Arnav Ghosh (ag983)
