PLUGIN_NAME = 'eprints'
DESCRIPTION = 'Imports Eprints articles.'
AUTHOR = 'Andy Byers'
VERSION = '0.1'
SHORT_NAME = 'eprints'
MANAGER_URL = 'eprints_index'

from utils import models


def install():
    new_plugin, created = models.Plugin.objects.get_or_create(name=SHORT_NAME, version=VERSION, enabled=True)

    if created:
        print('Plugin {0} installed.'.format(PLUGIN_NAME))
    else:
        print('Plugin {0} is already installed.'.format(PLUGIN_NAME))
        
    models.PluginSetting.objects.get_or_create(name='eprints_enabled', plugin=new_plugin, types='boolean',
                                               pretty_name='Enable eprints', description='Enable eprints',
                                               is_translatable=False)


def hook_registry():
    # TODO: fill this in! you will need to declare a name for the hook, the module where to find the hook defined,
    # and  the function in the module. The function name will have to match the function in hooks.py
    # ex: return {'article_footer_block': {'module': 'plugins.disqus.hooks', 'function': 'inject_disqus'}}
    pass
