from utils import models, plugins
from utils.install import update_settings

PLUGIN_NAME = 'eprints'
DESCRIPTION = 'Imports Eprints articles.'
AUTHOR = 'Andy Byers'
VERSION = '1.1'
SHORT_NAME = 'eprints'
MANAGER_URL = 'eprints_index'
JANEWAY_VERSION = "1.3.10"


class EprintsPlugin(plugins.Plugin):
    plugin_name = PLUGIN_NAME
    display_name = PLUGIN_NAME
    description = DESCRIPTION
    author = AUTHOR
    short_name = SHORT_NAME

    manager_url = MANAGER_URL

    version = VERSION
    janeway_version = "1.4.0"

    is_workflow_plugin = False


def install():
    EprintsPlugin.install()
    update_settings(
        file_path='plugins/eprints/install/settings.json',
    )


def hook_registry():
    # TODO: fill this in! you will need to declare a name for the hook, the module where to find the hook defined,
    # and  the function in the module. The function name will have to match the function in hooks.py
    # ex: return {'article_footer_block': {'module': 'plugins.disqus.hooks', 'function': 'inject_disqus'}}
    pass
