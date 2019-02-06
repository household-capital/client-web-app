# client-web-app


# Background - Django Structure
Django follows a Model:View:Controller design with a slight twist - it is more accurately Model:Template:View.  

In Django you have:
- *the Model* (Database which is abstracted through an ORM (Object-Relational Mapping) which means you call functions and methods on the object rather than passing SQL (it creates the SQL at a lower level);

- *the View*, which is the controller, it receives requests via URLs and responds to them by bringing together the Model (if applicable), forms (if applicable) and passes any required information (called context) to the template engine;

- *the Template* - the template engine renders an HTML template (which can be comprised of multiple HTML files), with corresponding CSS or Javascript, filling the template variables with information that is passed from the View in the context.

