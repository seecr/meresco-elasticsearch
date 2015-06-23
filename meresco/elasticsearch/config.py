## begin license ##
#
# Copyright (C) 2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2015 Stichting Kennisnet http://www.kennisnet.nl
#
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
#
## end license ##

from os import makedirs, execv
from os.path import join, abspath, isdir, dirname
from meresco.components.json import JsonDict
from .loggingconfig import LoggingConfig

mypath = dirname(abspath(__file__))
usrSharePath = '/usr/share/meresco-elasticsearch'
usrSharePath = join(dirname(mypath), 'usr-share')  #DO_NOT_DISTRIBUTE


class Config(object):
    def __init__(self, stateDir, **kwargs):
        self.stateDir = ensureDir(stateDir)
        self.configDir = ensureDir(stateDir, 'config')
        for (k, v) in kwargs.items():
            if not k.startswith('_'):
                setattr(self, k, v)

    def _configure(self):
        self._configuration = [
            '--config={0}/elasticsearch.json'.format(self.configDir),
        ]
        configuration = JsonDict({
            "path": {
                "data": ensureDir(self.stateDir, 'data'),
                "logs": ensureDir(self.stateDir, 'logs'),
                "work": ensureDir(self.stateDir, 'work'), # temporary files
                "conf": self.configDir,
                "plugins": ensureDir(self.stateDir, 'plugins'),
            },
            "cluster":{
                "name": self.name,
            },
            "http":{
                "port": self.port,
            },
            "transport": {
                "tcp": {
                    "port": self.transportPort
                }
            }
        })
        self._configureIndex(configuration)
        if self.identifier:
            configuration.setdefault("node", dict())['name'] = self.identifier
        with open(join(self.configDir, 'elasticsearch.json'), 'w') as f:
            configuration.dump(f, indent=4, sort_keys=True)
        LoggingConfig().writeConfig(configDir=self.configDir)

    def _configureIndex(self, configuration):
        index = configuration.setdefault('index', {})
        if self.development:
            index['number_of_shards'] = 1
            index['number_of_replicas'] = 0
        else:
            index['number_of_shards'] = self.shards
            index['number_of_replicas'] = self.replicas

    def start(self):
        self._configure()
        execv(
            self.executable,
            [self.executable] + self._configuration,
        )

    class Option(object):
        def __init__(self, shortOpt, longOpt, **kwargs):
            self.shortOpt = shortOpt
            self.longOpt = longOpt
            self.kwargs = kwargs
    options = [
        Option('', '--stateDir', help='State dir for data and config files for elasticsearch are written.', mandatory=True),
        Option('-p', '--port', type='int', help='Portnumber for HTTP access', default=9200),
        Option('-t', '--transportPort', type='int', help='Portnumber for internal transport', default=9300),
        Option('-n', '--name', help='Application name (unique for elasticsearch cluster)', mandatory=True),
        Option('', '--identifier', help='Identifier, if None an identifier will be generated for this node.'),
        Option('', '--shards', type='int', help='Set the number of shards, defaults to ElasticSearch default of {default}.', default=5),
        Option('', '--replicas', type='int', help='Set the number of replicas, defaults to ElasticSearch default of {default}.', default=1),
        Option('', '--development', help='Will start as a development node with 1 shard and 0 replicas, overrides settings of shards or replicas.', default=False, action="store_true"),
        Option('', '--elasticsearchExecutable', default='/usr/share/elasticsearch/bin/elasticsearch', help='Elasticsearch executable', dest='executable'),
    ]

def ensureDir(*parts):
    p = abspath(join(*parts))
    isdir(p) or makedirs(p)
    return p

