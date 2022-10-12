import sublime, sublime_plugin
import threading
import time
from subprocess import Popen, PIPE



class PiperThread(threading.Thread):
    def __init__(self, text, command):
        self.text = text
        self.command = command
        self.success = False
        threading.Thread.__init__(self)

    def run(self):
        args = self.command.split(" ")
        try:
            pop = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            out, err = pop.communicate(self.text.encode("UTF-8"))
            self.out = out.decode("UTF-8")
            self.err = err.decode("UTF-8")
            self.success = True
        except Exception as ex:
            self.out = ex.__str__()
            self.ex = ex
        finally:
            pass


class BasePiper(sublime_plugin.TextCommand):
    """
    class with the basic piper methods. the child classes are only responsible
    for getting pipe-command-name, and this one does the piping.

    command is a simple string which will be split up in the thread helper
    class.

    use_temp_file is not yet implemented.
    """

    def __init__(self, *args, **kwargs):
        super(BasePiper, self).__init__(*args, **kwargs)
        s = self.view.sel()
        if len(s):
            self.position = self.view.rowcol(s[0].a)
        else:
            self.position = None

    def pipe_text_through(self, command, sel=None):   # use_temp_file=False):
        # get all text in the buffer
        if not sel:
            sel = sublime.Region(0, self.view.size())
        regions = self.view.split_by_newlines(sel)
        regions = [ self.view.substr(s) for s in regions ]
        buffer_text = "\n".join(regions)
        thread = PiperThread(buffer_text, command)
        thread.start()
        data = { 'sel': sel }
        self.wait_for_result(thread, data)

    def wait_for_result(self, thread, data):
        if thread.is_alive():
            symbol = "*" if (time.time() % 1) < 0.5 else "-"
            self.view.set_status("pipe", "%s"%(symbol))
            sublime.set_timeout(lambda: self.wait_for_result(thread, data), 200)
        elif thread.success:
            # we're done! hooray!
            self.on_thread_done(thread.out, data)
        else:
            # we had an error
            sublime.error_message("Piper Error: Waiting for thread: " + thread.ex.__str__())

    def on_thread_done(self, new_text, data):
        try:
            sel = data['sel']
            sublime.active_window().run_command(
                "piper_update_selection",
                {
                    "sel": [sel.begin(), sel.end()],
                    "new_text": new_text,
                }
            )

        except Exception as ex:
            sublime.error_message("Piper Error: Initiating command: "+ex.__str__())


class PipeThroughPredefinedCommand(BasePiper):
    """
    opens a selection menu to choose a predefined command to pipe through
    """

    def run(self, edit, *args, **kwargs):
        self.edit = edit
        s = sublime.load_settings("Piper.settings")
        if s.has("predefined_commands"):  pre_commands = s.get('predefined_commands')
        else: pre_commands = [ "Nothing in here yet!" ]
        self.view.window().show_quick_panel(
            pre_commands,
            self.on_select,
            0)

    def on_select(self, index):
        s = sublime.load_settings("Piper.settings")
        if s.has("predefined_commands") and index > -1:
            pre_commands = s.get('predefined_commands')
            self.pipe_text_through(pre_commands[index])


class PiperDeleteEntry(sublime_plugin.WindowCommand):

    def run(self, *args, **kwargs):
        s = sublime.load_settings("Piper.settings")
        if s.has("predefined_commands"):  pre_commands = s.get('predefined_commands')
        else: pre_commands = [ "Nothing in here yet!" ]
        self.window.show_quick_panel(
            pre_commands,
            self.on_select,
            0)

    def on_select(self, index):
        s = sublime.load_settings("Piper.settings")
        if s.has("predefined_commands") and index > -1:
            pre_commands = s.get('predefined_commands')
            if len(pre_commands) > index:
                pre_commands.pop(index)
                if len(pre_commands): s.set('predefined_commands', pre_commands)
                else: s.erase('predefined_commands')
                sublime.save_settings("Piper.settings")


class PiperAddEntry(sublime_plugin.WindowCommand):

    def run(self, *args, **kwargs):
        last_command = ""
        s = sublime.load_settings("Piper.settings")
        if s.has("last_command"):  last_command = s.get('last_command')
        self.window.show_input_panel(
         "command to add",
            last_command,
            self.on_done,
            self.on_change,
            self.on_cancel)

    def on_done(self, user_input):
        s = sublime.load_settings("Piper.settings")
        if s.has("predefined_commands"):  pre_commands = s.get('predefined_commands')
        else: pre_commands = []
        pre_commands.append(user_input)
        s.set('predefined_commands', pre_commands)
        sublime.save_settings("Piper.settings")

    def on_cancel(self):
        pass

    def on_change(self, input):
        pass


class PipeThroughExternalCommand(BasePiper):
    """
    sends of the current file through an external application and
    replaces the actual contens with the output. useful as generic reformatter.
    """

    def run(self, edit, *args, **kwargs):
        self.edit = edit
        last_command = ""
        s = sublime.load_settings("Piper.settings")
        if s.has("last_command"):  last_command = s.get('last_command')
        self.view.window().show_input_panel(
         "pipe buffer to",
            last_command,
            self.on_done,
            self.on_change,
            self.on_cancel)

    def on_done(self, user_input):
        # simply give control to the base class.
        s = sublime.load_settings("Piper.settings")
        s.set('last_command', user_input)
        sublime.save_settings("Piper.settings")
        if not user_input == "":
            self.pipe_text_through(user_input)

    def on_cancel(self):
        pass

    def on_change(self, input):
        pass


class PipeCommandAddNew(sublime_plugin.WindowCommand):

    def run(self, *args, **kwargs):
        pass



class PiperUpdateSelection(sublime_plugin.TextCommand):
    def run(self, edit, sel, new_text=''):
        use_sel = sublime.Region(sel[0], sel[1])

        self.view.replace(edit, use_sel, new_text)
