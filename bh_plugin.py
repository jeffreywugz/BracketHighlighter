import sublime
import sublime_plugin
import os
from os.path import normpath, join, exists
import imp
from collections import namedtuple
import sys
import traceback


class Payload(object):
    status = False
    plugin = None
    args = None

    @classmethod
    def clear(cls):
        cls.status = False
        cls.plugin = None
        cls.args = None


class BracketRegion (namedtuple('BracketRegion', ['begin', 'end'], verbose=False)):
    """
    Bracket Regions for plugins
    """

    def move(self, begin, end):
        """
        Move bracket region to different points
        """

        return self._replace(begin=begin, end=end)

    def size(self):
        """
        Get the size of the region
        """

        return abs(self.begin - self.end)

    def toregion(self):
        """
        Convert to sublime region
        """

        return sublime.Region(self.begin, self.end)


def is_bracket_region(obj):
    """
    Check if object is a BracketRegion
    """

    return isinstance(obj, BracketRegion)


class ImportModule(object):
    @classmethod
    def import_module(cls, module_name, loaded=None):
        # Pull in built-in and custom plugin directory
        BH_MODULES = join(sublime.packages_path(), 'BracketHighlighter')
        # if BH_MODULES not in sys.path:
        #     sys.path.append(BH_MODULES)
        if module_name.startswith("bh_modules."):
            path_name = join(BH_MODULES, normpath(module_name.replace('.', '/')))
            module_name = module_name.replace("bh_modules.", "")
        else:
            path_name = join(sublime.packages_path(), normpath(module_name.replace('.', '/')))
        path_name += ".py"
        if not exists(path_name):
            raise AssertionError(path_name)
        if loaded is not None and module_name in loaded:
            module = sys.modules[module_name]
        else:
            module = imp.load_source(module_name, path_name)
        return module

    @classmethod
    def import_from(cls, module_name, attribute):
        return getattr(cls.import_module(module_name), attribute)


class BracketPluginRunCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        try:
            Payload.args["edit"] = edit
            Payload.plugin.run(**Payload.args)
            Payload.status = True
        except Exception:
            print("BracketHighlighter: Plugin Run Error:\n%s" % str(traceback.format_exc()))



class BracketPlugin(object):
    """
    Class for preparing and running plugins
    """

    def __init__(self, plugin, loaded):
        """
        Load plugin module
        """

        self.enabled = False
        self.args = plugin['args'] if ("args" in plugin) else {}
        self.plugin = None
        if 'command' in plugin:
            plib = plugin['command']
            try:
                module = ImportModule.import_module(plib, loaded)
                self.plugin = getattr(module, 'plugin')()
                loaded.add(plib)
                self.enabled = True
            except Exception:
                print('BracketHighlighter: Load Plugin Error: %s\n%s' % (plugin['command'], traceback.format_exc()))

    def is_enabled(self):
        """
        Check if plugin is enabled
        """

        return self.enabled

    def run_command(self, view, name, left, right, selection):
        """
        Load arguments into plugin and run
        """

        Payload.status = False
        Payload.plugin = self.plugin()
        setattr(Payload.plugin, "left", left)
        setattr(Payload.plugin, "right", right)
        setattr(Payload.plugin, "view", view)
        setattr(Payload.plugin, "selection", selection)
        self.args["edit"] = None
        self.args["name"] = name
        Payload.args = self.args

        # Call a TextCommand to run the plugin so it can feed in the Edit object
        view.run_command("bracket_plugin_run")

        if Payload.status:
            left, right, selection = Payload.plugin.left, Payload.plugin.right, Payload.plugin.selection
        Payload.clear()

        return left, right, selection


class BracketPluginCommand(object):
    """
    Bracket Plugin base class
    """

    def run(self, bracket, content, selection):
        """
        Runs the plugin class
        """

        pass
