# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See LICENSE for more details.
#
# Copyright (c) 2020 ScyllaDB

import copy
import uuid
import cherrypy
from core.configuration import Configuration
import core.faults


class Root(object):

    @staticmethod
    def create_object_from_json_extract_classname(json):
        cls = json.get('classname', None)
        if cls is None:
            print(f'did not foud classname field in json')
            return None
        clsptr = core.faults.attrs(cls)
        json.pop(cls)
        if clsptr is None:
            print(f'did not found class {cls}')
            return None
        fault = None
        try:
            fault = clsptr._deserialize()
        except BaseException as ex:
            print(f"exception {ex} when trying to deserialize {json} cls={cls}")
        return fault

    def add_fault(uuid, json):
        faultobj = Root.create_object_from_json_extract_classname(json)
        if faultobj is None:
            print(f"fail creating obj from uuid={uuid} json={json}")
            return 0
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
        json = None if method == 'DELETE' else cherrypy.request.json
        print(f'fault_id={fault_id}')
        print(f'method={method}')
        print(f'params={params}')
        print(f'json={json}')
        if method == 'GET':
            if fault_id is None:
                ids = {'faults ids': Configuration.get_all_faults_ids()}
                return ids
            else:
                return self.faults[fault_id]
        if method == 'POST' or method == 'CREATE' or method == 'PUT':
            fault_id = str(uuid.uuid4())
            faultobj = Root.create_object_from_json_extract_classname(json)
            if faultobj:
                Configuration.set_fault(fault_id, faultobj)
            else:
                fault_id = "0"
            return {'fault_id': fault_id}
        if method == 'DELETE':
            removed_uuid = Configuration.remove_fault(fault_id)
            if removed_uuid:
                cherrypy.response.status = 200
            else:
                cherrypy.response.status = 404
            return {'fault_id': fault_id}


def rest_start(port=8080):
    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': port,
    })
    cherrypy.quickstart(Root())


if __name__ == '__main__':
    rest_start(port=8080)
