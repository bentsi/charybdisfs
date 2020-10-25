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

import cherrypy
import copy
class Root(object):
    faults_dict = {'1':{'name':'first'},'2':{'name':'second'},'80':{'name':'eighty'}}
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
                ids = {'faults ids': list(self.faults_dict.keys())}
                return ids
            else:
                return self.faults[fault_id]
        if method == 'POST' or method == 'CREATE' or method == 'PUT':
                self.faults_dict[fault_id] = copy.deepcopy(json)
                return {fault_id:self.faults_dict[fault_id]}
        if method == 'DELETE':
            if fault_id in self.faults_dict:
                self.faults_dict.pop(fault_id)
                cherrypy.response.status = 200
            else:
                cherrypy.response.status = 404
            return {'fault_id': fault_id}
if __name__ == '__main__':
    cherrypy.quickstart(Root())
