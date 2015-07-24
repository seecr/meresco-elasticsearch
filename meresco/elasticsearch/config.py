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

from os import makedirs, execv, chmod, getuid, walk, chown
from pwd import getpwnam
from os.path import join, abspath, isdir, dirname
from meresco.components import ParseArguments
from meresco.components.json import JsonDict
from .loggingconfig import LoggingConfig
from itertools import chain

mypath = dirname(abspath(__file__))
usrSharePath = '/usr/share/meresco-elasticsearch'
usrSharePath = join(dirname(mypath), 'usr-share')  #DO_NOT_DISTRIBUTE


class Config(object):
    def __init__(self, **kwargs):
        # defaults
        self.development = False
        self.user = None
        # self.service = False
        for (k, v) in kwargs.items():
            if not k.startswith('_'):
                setattr(self, k, v)

    def configure(self):
        self.stateDir = ensureDir(self.stateDir)
        self.configDir = ensureDir(self.stateDir, 'config')
        self.configFile = join(self.configDir, 'elasticsearch.json')
        self._configure()
        LoggingConfig().writeConfig(configDir=self.configDir)
        self._createBin()
        self._ownUser()
        self._service()
        if self.development:
            self._start()
            return
        print '''
Elasticsearch configured in directory "{stateDir}"
All configuration is in the file "{configurationFile}"

To start:
    $ {runfile}'''.format(
            stateDir=self.stateDir,
            configurationFile=self.configFile,
            runfile=self.runfile
        )
        if self.user:
            print '''
To run as a service:
    $ cd /etc/service; sudo ln -s {stateDir}/service elasticsearch-service'''.format(
            stateDir=self.stateDir,
        )


    @classmethod
    def parse(cls):
        parser = ParseArguments()
        parser._parser.set_description("""Configures elasticsearch to start from given stateDir""")
        keys = ['default']
        keys.append('admin' if getuid() == 0 else 'user')
        for option in (o for k in keys for o in cls.options[k]):
            parser.addOption(option.shortOpt, option.longOpt, **option.kwargs)
        options, arguments = parser.parse()
        return cls(**vars(options))

    def _start(self):
        execv(
            self.runfile,
            [self.runfile],
        )

    def _configure(self):
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
        with open(self.configFile, 'w') as f:
            configuration.dump(f, indent=4, sort_keys=True)

    def _configureIndex(self, configuration):
        index = configuration.setdefault('index', {})
        if self.development:
            index['number_of_shards'] = 1
            index['number_of_replicas'] = 0
        else:
            index['number_of_shards'] = self.shards
            index['number_of_replicas'] = self.replicas

    def _createBin(self):
        binDir = ensureDir(self.stateDir, 'bin')
        self.runfile = join(binDir, 'run')
        self.pluginfile = join(binDir, 'plugin')
        with open(self.runfile, 'w') as b:
            b.write("""#!/bin/bash
# Generated
{0} --config={1}
""".format(self.executable, self.configFile))
        chmod(self.runfile, 0755)
        with open(self.pluginfile, 'w') as b:
            b.write("""#!/bin/bash
# Generated
export CONF_DIR={0}
{1} "$@"
""".format(self.configDir, join(dirname(self.executable), 'plugin')))
        chmod(self.pluginfile, 0755)

    def _ownUser(self):
        if not self.user:
            return
        userInfo = getpwnam(self.user)
        for path, dirs, files in walk(self.stateDir):
            for f in chain(dirs, files):
                chown(join(path, f), userInfo.pw_uid, userInfo.pw_gid)

    def _service(self):
        if not self.user:
            return
        serviceDir = ensureDir(self.stateDir, 'service')
        ensureDir(serviceDir, 'log', 'main')
        runfile = join(serviceDir, 'run')
        logrunfile = join(serviceDir, 'log', 'run')
        with open(logrunfile, 'w') as f:
            f.write("""#!/bin/bash
exec /usr/bin/setuidgid {0} /usr/bin/multilog t n20 s9999999 ./main 2>&1""".format(self.user))
        chmod(logrunfile, 0755)
        with open(runfile, 'w') as f:
            f.write("""#!/bin/bash
export LANG=en_US.UTF-8
exec 2>&1
cd {0}
exec /usr/bin/setuidgid {1} ./run""".format(join(self.stateDir, 'bin'), self.user))
        chmod(runfile, 0755)

    class Option(object):
        def __init__(self, shortOpt, longOpt, **kwargs):
            self.shortOpt = shortOpt
            self.longOpt = longOpt
            self.kwargs = kwargs
    options = {
        'default': [
            Option('', '--stateDir', help='State dir for data and config files for elasticsearch are written.', mandatory=True),
            Option('-p', '--port', type='int', help='Portnumber for HTTP access', default=9200),
            Option('-t', '--transportPort', type='int', help='Portnumber for internal transport', default=9300),
            Option('-n', '--name', help='Application name (unique for elasticsearch cluster)', mandatory=True),
            Option('', '--identifier', help='Identifier, if None an identifier will be generated for this node.'),
            Option('', '--shards', type='int', help='Set the number of shards, defaults to ElasticSearch default of {default}.', default=5),
            Option('', '--replicas', type='int', help='Set the number of replicas, defaults to ElasticSearch default of {default}.', default=1),
            Option('', '--elasticsearchExecutable', default='/usr/share/elasticsearch/bin/elasticsearch', help='Elasticsearch executable', dest='executable'),
        ],
        "user": [
            Option('', '--development', help='Will start as a development node with 1 shard and 0 replicas, overrides settings of shards or replicas and will start.', default=False, action="store_true"),
        ],
        "admin": [
            Option('', '--user', help='User to be running the elasticseach-service', mandatory=True),
            # Option('', '--service', help='Prepare daemontools service', default=False, action='store_true')
        ]
    }

def ensureDir(*parts):
    p = abspath(join(*parts))
    isdir(p) or makedirs(p)
    return p

