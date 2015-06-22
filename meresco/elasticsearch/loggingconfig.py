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

from os.path import join

class LoggingConfig(object):
    def writeConfig(self, configDir):
        # logging = JsonDict({
        #     "configuration": {
        #         "loggers":{
        #             "root": {
        #                 "level": "info",
        #                 "AppenderRef": { "ref": "STDOUT" }
        #             },
        #             "logger": [
        #                 {
        #                     "name": "action",
        #                     "level": "debug",
        #                     "AppenderRef": { "ref": "Console" },
        #                 },
        #                 {
        #                     "name": "org.apache.http",
        #                     "level": "info",
        #                     "AppenderRef": { "ref": "Console" },
        #                 },
        #             ]
        #         },
        #         "appenders": {
        #             "Console": {
        #                 "name": "STDOUT",
        #                 "PatternLayout": "[%d{ISO8601}][%-5p][%-25c] %m%n",
        #             }
        #         }
        #     }
        # })

        with open(join(configDir, 'logging.yml'), 'w') as f:
            # logging.dump(f, indent=4, sort_keys=True)
            f.write("""#config log
es.logger.level: INFO
rootLogger: ${es.logger.level}, console
logger:
  # log action execution errors for easier debugging
  action: DEBUG
  # reduce the logging for aws, too much is logged under the default INFO
  com.amazonaws: WARN
  org.apache.http: INFO

appender:
  console:
    type: console
    layout:
      type: consolePattern
      conversionPattern: "[%d{ISO8601}][%-5p][%-25c] %m%n"
""")