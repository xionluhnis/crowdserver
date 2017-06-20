from datetime import datetime
import json
import os
from flask import Flask, render_template, request, session

app = Flask(__name__)
appdir = os.path.dirname(os.path.realpath(__file__))
tmpl_dir = os.path.join(appdir, 'templates')
upload_scheme_dir = os.path.join(appdir, 'upload')

@app.route('/')
def hello_world():
  return 'Hello from Flask!'

@app.route('/<view>')
def show(view):
  tmpl_file = os.path.join(tmpl_dir, '%s.html' % view)
  if os.path.isfile(tmpl_file):
    return render_template(tmpl_file)
  else:
    return render_template('error.html', reason="Invalid page %s" % view), 404

@app.route('/upload/<name>', methods=['GET', 'POST'])
@app.route('/upload/<name>/<id>', methods=['GET', 'POST'])
def upload(name, id=None):
  scheme_file = os.path.join(upload_scheme_dir, name + '.json')
  if os.path.isfile(scheme_file):
    # use scheme file to process upload
    with open(scheme_file) as json_file:
      try:
        scheme = json.load(json_file)
      except ValueError:
        scheme = Dict()
      upload_type = scheme.get('type', 'json')
      upload_dir  = scheme.get('path', os.path.join(upload_scheme_dir, name))
      if not os.path.isdir(upload_dir):
        return render_template('error.html', reason="Missing upload directory %s" % upload_dir), 404
      # create id if necessary
      if id is None:
        id = datetime.now().strftime('%Y%m%d%H%M%S%f') + '.' + upload_type
      # select non-existing file
      upload_file = os.path.join(upload_dir, id)
      i = 1
      while os.path.isfile(upload_file):
        upload_file = '%s_%d' % (os.path.join(upload_dir, id), i)
        i = i + 1
      # special treatment depending on type
      if upload_type is 'json':
        with open(upload_file, 'w') as f:
          f.write(request.form.get('data', '{}'))
      elif upload_type is 'file':
        file = request.files['file']
        file.save(upload_file)
      else:
        return render_template('error.html', reason='Insupported upload type %s' % upload_type), 404
      # if it went fine, we just output the filename
      return os.path.basename(upload_file)
  else:
    return render_template("error.html", reason="Invalid upload scheme %s" % name), 404

@app.route('/<str>/edit')
def edit(str):
  return render_template("edit.html", str=str)

if __name__ == '__main__':
  app.run()

# vim: ts=2 sw=2 et
