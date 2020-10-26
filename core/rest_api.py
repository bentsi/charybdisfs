# Copyright 2020 ScyllaDB
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import copy
import json
import uuid
import cherrypy
from core.configuration import Configuration
import core.faults


DEFAULT_PORT = 8080


class Root(object):

    @staticmethod
    def create_object_from_json_extract_classname(jsonobj):
        jsonloaded : dict = json.loads(jsonobj)
        cls = jsonloaded.get('classname', None)
        if cls is None:
            print(f'did not found classname field in json')
            return NameError('classname') ,None
        print(cls)
        clsptr = getattr(core.faults, cls)
        jsonloaded.pop('classname')
        if clsptr is None:
            print(f'did not found class {cls}')
            return NameError('cls') ,None
        fault = None
        try:
            fault = clsptr._deserialize(json.dumps(jsonloaded))
        except BaseException as ex:
            print(f"exception {ex} when trying to deserialize {jsonloaded} cls={cls}")
            return ex, None
        return None, fault

    @staticmethod
    def add_fault(uuid, faultobj):
        if faultobj is None:
            print(f"fail creating obj from uuid={uuid} obj={faultobj})")
            return "0"
        Configuration.set_fault(uuid, faultobj)
        return uuid

    def remove_fault(uuid):
        uuid_removed = Configuration.remove_fault(uuid)
        return uuid_removed

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def faults(self, fault_id=None):
        method = cherrypy.request.method
        params = cherrypy.request.params
        jsonobj = None if method == 'DELETE' or method == 'GET' else cherrypy.request.json
        print(f'fault_id={fault_id}')
        print(f'method={method}')
        print(f'params={params}')
        print(f'json={jsonobj}')
        if method == 'GET':
            if fault_id is None:
                ids = {'faults ids': Configuration.get_all_faults_ids()}
                return ids
            else:
                return {'fault_id': 'fault_id', 'fault':Configuration.get_fault(fault_id)._serialize()}
        if method == 'POST' or method == 'CREATE' or method == 'PUT':
            fault_id = str(uuid.uuid4())
            ex, faultobj = Root.create_object_from_json_extract_classname(jsonobj)
            fault_id= Root.add_fault(fault_id, faultobj)
            if ex is not None:
                cherrypy.response.status = 500
                return {'fault_id': fault_id, 'exception': str(ex)}
            return {'fault_id': fault_id}

        if method == 'DELETE':
            removed_uuid = Configuration.remove_fault(fault_id)
            if removed_uuid:
                cherrypy.response.status = 200
            else:
                cherrypy.response.status = 404
            return {'fault_id': fault_id}


def rest_start(port=DEFAULT_PORT):
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': port
    })
    cherrypy.quickstart(Root())

def rest_stop():
    cherrypy.engine.exit()

if __name__ == '__main__':
    rest_start(port=DEFAULT_PORT)
