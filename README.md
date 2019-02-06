# client-web-app


## Background - Django Structure
Django follows a Model:View:Controller design with a slight twist - it is more accurately Model:Template:View.  

In Django you have:
#### The Model
- Database which is abstracted through an ORM (Object-Relational Mapping) which means you call functions and methods on the object rather than passing SQL (it creates the SQL at a lower level);

#### The View
- which is the controller, it receives requests via URLs and responds to them by bringing together the Model (if applicable), forms (if applicable) and passes any required information (called context) to the template engine;

#### The Template
- the template engine renders an HTML template (which can be comprised of multiple HTML files), with corresponding CSS or Javascript, filling the template variables with information that is passed from the View in the context.

So the basic request-response cycle is:
+ an http request is received (e.g., from a browser) and routed based on URL pattern to a view
+ the view gathers required data from the model, presents a form (GET) or receives form information (POST) and performs required calculations or actions
+ the view may redirect to another page or render a page via template.  It will pass required 'context' to a template
+ the template engine will build the required HTML using the context and associated form, css, javascript etc
+ an http response will be delivered back to the browser

## Background - Django File Structure
Based on the above - the file structure becomes clearer:
#### Apps 
Applications can be as narrow or as broader as appropriate, but with a conventional approach to be smaller and specific - do one thing well, rather than sprawling.  Each app has the same substructure:
- urls.py  - mapping of urls to views
- views.py - contains all of the views which control the content/response - typically will point to a template
- forms.py - contains the definition information for forms to be rendered on a page (called from the view)
- models.py - has the database definitions and procedures to retrieve/save data (called from the view)

#### Templates 
HTML templates are saved here (referenced by views).  This is straight HTML but include template references {{establishmentFee}} and logic {% if template != 0 %} {% endif %} etc.

#### Static
Static files - css, images, javascript are stored here.  Typically referenced by a template.

#### Config
The main Django configuration / settings files are located in this directory.

#### Manage.py
This simple file is at the top of the structure and is used to start the application (e.g., python manage.py runserver)

## Client App Example
A request to https://householdcapital.app/client/live1 will:
- be routed from urls.py to a view ```path('live1', views.Live1.as_view(), name='live1')```

