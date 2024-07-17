# Map-Action PDF table extraction tool
This repository contains the code for the Map-Action PDF table extraction tool.

## Introduction
This project aims to create a data extraction tool. It can take one or several pdf files as input. Additionally, it requires parameters such as country name, administrative divisions, list of indicators, and keywords. The output is one or several csv's . They contain relevant indicators per administrative division. Furthermore, it includes metadata such as page number and format. The tool should support English, French, and Spanish.

The code has been developed by a cooperation of ABW & Pipple.

## Description of the application
Here you can write:
  * What the application does
  * Why the application is created
  * For whom the application is created
  
## Usage of the application

### How to install the project
Clone the project.

The Python version used is 3.12.1

The requirements.txt file provides all the necessary python packages for this project. They can be installed using a virtual environment and following these steps:

* Open command prompt (cmd) or a terminal in your IDE of choice and provide the following commands:
     - `pip install virtualenv`
    - cd folder/path/you/want/venv/in 
    - `py -3.112.1 -m venv venv`
    - cd venv/Scripts
    - `activate`
    - cd folder/path/to/requirements/file

To perform the following step, it's essential that you already cloned the repo.
    - `pip install -r requirements.txt`

### How to run the project
Make sure to put the PDF you want tables to be extracted from in the 'input_pdf' folder of the repository.

Then there are 2 scripts you can run.

#### extract_tables_using_tabula-py.py
This file uses [tabula-py](https://pypi.org/project/tabula-py/#description) as the extraction method. 

In the main function, the variable pdf_name should be altered to the name of the pdf you want to be used for the extraction.