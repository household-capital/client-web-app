# client-web-app


# Background - Django Structure
Django follows a Model:View:Controller design with a slight twist - it is more accurately Model:Template:View.  

In Django you have:
- ###the Model### (Database which is abstracted through an ORM (Object-Relational Mapping) which means you call functions and methods on the object rather than passing SQL (it creates the SQL at a lower level);

- ### the View ###, which is the controller, it receives requests via URLs and responds to them by bringing together the Model (if applicable), forms (if applicable) and passes any required information (called context) to the template engine;

- ###the Template### - the template engine renders an HTML template (which can be comprised of multiple HTML files), with corresponding CSS or Javascript, filling the template variables with information that is passed from the View in the context.

So the basic request-response cycle is:
+ an http request is received (e.g., from a browser) and routed based on URL pattern to a view
+ the view gathers required data from the model, presents a form (GET) or receives form information (POST) and performs required calculations or actions
+ the view may redirect to another page or render a page via template.  It will pass required 'context' to a template
+ the template engine will build the required HTML using the context and associated form, css, javascript etc
+ an http response will be delivered back to the browser

# Background - Django File Structure
Based on the above - the file structure becomes a little clearer:






