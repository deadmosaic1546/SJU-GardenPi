# SJU-GardenPi

## Installing Dependencies

Before running install **Python**, **Python Venv (Virtual Environment)**, and **Python Pip**

On **Linux** and **Mac**:

~~~~~~~~
chmod +x INSTALL.sh
./INSTALL.sh
~~~~~~~~

On **Windows**:

~~~~~~~~
.\INSTALL.bat
~~~~~~~~

This will install all of the required python libraries

## Running the Project

After installation run

On **Linux** and **Mac**:

~~~~~~~~~~~~~~~~~~
source .venv/bin/activate
flask --app flaskr run --debug
~~~~~~~~~~~~~~~~~~

On **Windows**:

~~~~~~~~~~~~~~~~~~
.venv\Scripts\activate.bat
flask --app flaskr run --debug
~~~~~~~~~~~~~~~~~~

## Development

Add a new python library (**Mac** + **Linux**)

~~~~
$ pip freeze > requirements.txt
~~~~