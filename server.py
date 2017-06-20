from datetime import datetime
import json
import os
from flask import Flask, render_template, request, session

app = Flask(__name__)
appdir = os.path.dirname(os.path.realpath(__file__))
stat_dir = os.path.join(appdir, 'static')
tmpl_dir = os.path.join(appdir, 'templates')
upload_scheme_dir = os.path.join(appdir, 'upload')

@app.route('/')
def hello_world():
  return 'Hello from Flask!'

@app.route('/<view>')
def show(view):
  tmpl_name = '%s.html' % view
  tmpl_file = os.path.join(tmpl_dir, tmpl_name)
  if os.path.isfile(tmpl_file):
    return render_template(tmpl_name)
  else:
    return render_template('error.html', reason="Invalid page %s" % view), 404

@app.route('/upload/<name>', methods=['GET', 'POST'])
@app.route('/upload/<name>/<path:id>', methods=['GET', 'POST'])
def upload(name, id=None):
  scheme_file = os.path.join(upload_scheme_dir, name + '.json')
  if os.path.isfile(scheme_file):
    # use scheme file to process upload
    with open(scheme_file) as json_file:
      try:
        scheme = json.load(json_file)
      except ValueError:
        scheme = {}
      upload_type = scheme.get('type', 'form')
      upload_dir  = scheme.get('path', os.path.join(upload_scheme_dir, name))
      upload_test = scheme.get('require', None)
      
      # check base upload directory exists (else not valid upload)
      if not os.path.isdir(upload_dir):
        return render_template('error.html', reason="Missing upload directory %s" % upload_dir), 404
      
      # create id if necessary
      if id is None:
        if upload_test is None:
          id = datetime.now().strftime('%Y%m%d%H%M%S%f') + '.' + upload_type
        else: # this is not valid then as we need an id
          return render_template('error.html', reason="Invalid upload for %s" % name), 404
      
      # select non-existing file
      upload_file = os.path.join(upload_dir, id)
      i = 1
      while os.path.isfile(upload_file):
        upload_file = '%s_%d' % (os.path.join(upload_dir, id), i)
        i = i + 1
      
      # if upload has a test, we need to check that the target exists
      if upload_test is not None:
        path_dir  = os.path.relpath(os.path.dirname(upload_file), upload_dir)
        path_file = os.path.basename(upload_file).split('.')[0:-1]
        test_file = os.path.join(stat_dir, upload_test % os.path.join(path_dir, path_file))
        if not os.path.isfile(test_file):
          return render_template('error.html', reason="Invalid upload for %s@%id" % (name, id)), 404
      
      # potentially create upload subdir
      upload_dir = os.path.dirname(upload_file)
      if not os.path.isdir(upload_dir):
        try:
          os.makedirs(upload_dir)
        except OSError:
          return render_template('error.html', reason="Invalid upload for %s@%s" % (name, id)), 404
      
      # write format depends on type
      if upload_type is 'json':
        # json => dump content of form[$key] where $key is 'data' by default
        key = scheme.get('key', 'data')
        with open(upload_file, 'w') as f:
          f.write(request.form.get(key, '{}'))
        #
      elif upload_type is 'file':
        # file => save single file as result
        file = request.files['file']
        file.save(upload_file)
        #
      elif upload_type is 'form':
        # form => save all form data + query arguments in json format
        data = { 'args': {} }
        for k,v in request.form.iteritems():
          data[k] = v
        for k,v in request.args.iteritems():
          data['args'][k] = v
        with open(upload_file, 'w') as f:
          json.dump(data, f)
        #
      else: # unsupported type
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
