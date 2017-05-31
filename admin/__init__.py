# -*- coding: utf-8 -*-

### common imports
from flask import Blueprint, abort
from domogik.common.utils import get_packages_directory
from domogik.admin.application import render_template
from domogik.admin.views.clients import get_client_detail, get_client_devices
from jinja2 import TemplateNotFound
import ow
import traceback
import sys

### package specific imports
import subprocess

### package specific functions

def get_errorlog(log):
    print("Log file = %s" % log)
    errorlog = subprocess.Popen(['/bin/egrep', 'ERROR|WARNING', log], stdout=subprocess.PIPE)
    output = errorlog.communicate()[0]
    if not output:
        output = "No ERROR or WARNING"
    if isinstance(output, str):
        output = unicode(output, 'utf-8')
    return output


### common tasks
package = "plugin_template"
template_dir = "{0}/{1}/admin/templates".format(get_packages_directory(), package)
static_dir = "{0}/{1}/admin/static".format(get_packages_directory(), package)
logfile = "/var/log/domogik/{0}.log".format(package)

plugin_template_adm = Blueprint(package, __name__,
                        template_folder = template_dir,
                        static_folder = static_dir)


@plugin_template_adm.route('/<client_id>')
def index(client_id):
    detail = get_client_detail(client_id)       # template plugin configuration 
    #devices = get_client_devices(client_id)    # template plugin devices list
    #print("Plugin devices\n %s" % format(devices))
    try:
        return render_template('plugin_template.html',
            clientid = client_id,
            client_detail = detail,
            mactive ="clients",
            active = 'advanced',
            logfile = logfile,
            errorlog = get_errorlog(logfile))

    except TemplateNotFound:
        abort(404)

@plugin_template_adm.route('/<client_id>/log')
def log(client_id):
    clientid = client_id
    detail = get_client_detail(client_id)
    with open(logfile, 'r') as contentLogFile:
        content_log = contentLogFile.read()
        if not content_log:
            content_log = "Empty log file"
        if isinstance(content_log, str):
            content_log = unicode(content_log, 'utf-8')
    try:
        return render_template('plugin_template_log.html',
            clientid = client_id,
            client_detail = detail,
            mactive="clients",
            active = 'advanced',
            logfile = logfile,
            contentLog = content_log)

    except TemplateNotFound:
        abort(404)
