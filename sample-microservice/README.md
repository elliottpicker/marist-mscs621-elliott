# Elliottchat
Elliott chat is a message board service where users can post messages for other viewers to see and respond to. Chat offers features such as language detection, language translation, text to speech, and watson analyze.

This repository is based on assignment for the *Marist Cloud Computing* class for Fall 2018, available at https://github.com/jinho10/marist-mscs621.git. Portions of this project are borrowed heavily from that project.

The code uses [Flask microframework](http://flask.pocoo.org/) for web requests, [Redis](https://redis.io) as a database for storing JSON objects, and [IBM Watson Developer Cloud](https://www.ibm.com/watson/developercloud/) for its various services.

The code can be deployed in any host with docker engine using docker command or docker-compose command. 



Follow the steps below to manually deploy the Elliottchat server.


## Get the code

```bash
    $ git clone https://github.com/elliottpicker/marist-mscs621-elliott.git
    $ cd marist-mscs621/unit-4
    $ docker-compose build
    $ docker-compose up -d
```
This will run the sample code as containers.

You should be able to login to elliottchat at http://localhost:5000/ from your browser 


When you are done, you can use the following command to remmove the containers:
```bash
    $ docker-compose kill
    $ docker-compose rm
```


## Structure of application

**requirements.txt** - Contains the external python packages that are required by the application. These will be downloaded from the [python package index](https://pypi.python.org/pypi/) and installed via the python package installer (pip) during the buildpack's compile stage when you execute the cf push command. In this sample case we wish to download the [Flask package](https://pypi.python.org/pypi/Flask) at version 0.12, [Redis package](https://pypi.python.org/pypi/Redis) at version greater than or equal to 2.10 and watson-developer-cloud at a version greater than or equal to 2.4.1.

**runtime.txt** - Controls which python runtime to use. In this case we want to use 2.7.9.

**README.md** - this readme.

**manifest.yml** - Controls how the app will be deployed in Bluemix and specifies memory and other services like Redis that are needed to be bound to it.

**server.py** - the python application script. This is implemented as a simple [Flask](http://flask.pocoo.org/) application. The routes are defined in the application using the @app.route() calls. This application has a `/` route that iniates the initial login. From there multiple routes provide various services to make the elliottchat service possible.
```

