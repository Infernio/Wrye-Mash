import os
import subprocess
import threading

import conf

import Queue as queue

class tes3cmd(threading.Thread):
    """ A class that manages a tes3cmd process in another thread """

    def __init__(self, callback=None):
        """
        The callback should be a function that sends the done event to your
        application. It should be constructed with care as it is called in this
        thread not the main one.
        """
        threading.Thread.__init__(self)
        self.msg = queue.Queue()
        self.callback = callback
        self.err = self.out = ''

    def stop(self):
        """
        Stops the execution of the thread. You must join the thread after
        calling this as it isn't instant. This is safe to call from another thread
        """
        self.msg.put('STOP')

    def fixit(self, hideBackups=True, backupDir=None):
        args = ['tes3cmd.exe', 'fixit']

        if hideBackups:
            args += ['--hide-backups']

        if backupDir:
            args += ['--backup-dir', backupDir]

        self.args = args
        self.start()

    def clean(self, files, replace=False, hideBackups=True, backupDir=None):
        self.files = files
        args = ['tes3cmd.exe', 'clean']

        if replace:
            args += ['--replace']

        if hideBackups:
            args += ['--hide-backups']

        if backupDir:
            args += ['--backup-dir', backupDir]

        args += files
        self.args = args

        self.start()

    def run(self):
        """
        This shouldn't be called directly, use a function like clean
        that correctly sets the state
        """
        startupinfo = None

        #hides the command promp on NT systems
        if os.name == 'nt':
            info = subprocess.STARTUPINFO()
            #WIN32 constant: STARTUPINFO.STARTF_USESHOWWINDOW
            info.dwFlags |= 0x00000001

        p = subprocess.Popen(self.args,
                             executable=getLocation(),
                             cwd=getDataDir(),
                             startupinfo=info,
                             stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE) 

        while p.poll() is None:
            if not self.msg.empty():
                msg = self.msg.get()
                if msg == 'STOP':
                    p.terminate()
                    return

            out = p.stdout.readline().strip()
            err = p.stderr.readline().strip()

            if out:
                self.out += out

            if err:
                self.err += err

        if self.callback:
            self.callback()


def getDataDir():
    cwd = os.getcwd()
    mwdir = os.path.dirname(cwd)
    return os.path.join(mwdir, 'Data Files')

def getLocation():
    location = None
    cwd = os.getcwd()
    locs = [cwd,
            os.path.join(cwd, 'tes3cmd'),
            conf.settings['mwDir'],
            os.path.join(conf.settings['mwDir'], 'Data Files')]
    for loc in locs:
        path = os.path.join(loc, 'tes3cmd.exe')
        if os.path.exists(path):
            return path
    return None
