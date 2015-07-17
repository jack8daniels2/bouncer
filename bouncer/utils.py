import importlib
import inspect
from pkgutil import walk_packages
import logging

log = logging.getLogger(__name__)

def discover_class(module_name, interface):
    '''
    Discover class_object from a module by its interface type
    '''
    log.debug('Discovering {}'.format(module_name))
    #dynamic class load
    try:
        module = __import__(module_name, fromlist=[module_name,])
        for _, classobject in inspect.getmembers(module, inspect.isclass):
            if issubclass(classobject, interface) and \
                    classobject != interface:
                return classobject
    except:
        log.exception('Error loading module_name {}'.format(module_name))
        raise Exception('Error loading module_name {}'.format(module_name))

def load_class(module_name, interface):
    '''
    Fetch class_object from a module by name and verify that is has the correct
    interface
    '''
    log.debug('Loading {}'.format(module_name))
    mod_name, class_name = module_name.rsplit('.', 1)
    try:
        module = __import__(mod_name, fromlist=[mod_name,])
        classobject = getattr(module, class_name)
        if issubclass(classobject, interface) and \
                classobject != interface:
            return classobject
        else:
            raise Exception('{} has the wrong interface {}',
                            classobject, interface)
    except:
        log.exception('Error loading mod_name {}'.format(mod_name))
        raise Exception('Error loading mod_name {}'.format(mod_name))

def parse_url(url):
    #TODO Verify the URL parsing logic. It must be more complex than this
    url_tuple = url.split('/', 1)
    if len(url_tuple) < 2:
        return url_tuple[0], None, None

    dn, pp = url_tuple
    return (dn,) + parse_path_parameters(pp)

def parse_path_parameters(pp):
    pp_tuple = pp.split('?', 1)
    if len(pp_tuple) < 2:
        return pp_tuple[0], None

    return (pp_tuple[0], pp_tuple[1].split('&'))
