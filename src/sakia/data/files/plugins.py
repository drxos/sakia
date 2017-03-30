import attr
import os
import sys
import logging
import importlib
from ..entities import Plugin


@attr.s(frozen=True)
class PluginsDirectory:
    """
    The repository for UserParameters
    """
    _path = attr.ib()
    plugins = attr.ib(default=[])
    _logger = attr.ib(default=attr.Factory(lambda: logging.getLogger('sakia')))

    @classmethod
    def in_config_path(cls, config_path, profile_name):
        plugins_path = os.path.join(config_path, profile_name, "plugins")
        if not os.path.exists(plugins_path):
            os.makedirs(plugins_path)
        return cls(plugins_path)

    def load_or_init(self):
        """
        Init plugins
        """
        try:
            for file in os.listdir(self._path):
                if file.endswith(".zip"):
                    sys.path.append(os.path.join(self._path, file))
                    module_name = os.path.splitext(os.path.basename(file))[0]
                    try:
                        plugin_module = importlib.import_module(module_name)
                        self.plugins.append(Plugin(plugin_module.PLUGIN_NAME,
                                                   plugin_module.PLUGIN_DESCRIPTION,
                                                   plugin_module.PLUGIN_VERSION,
                                                   True,
                                                   plugin_module))
                    except ImportError as e:
                        self.plugins.append(Plugin(module_name, "", "",
                                                   False, None))
                        self._logger.debug(str(e) + " with sys.path " + str(sys.path))
        except OSError as e:
            self._logger.debug(str(e))
        return self