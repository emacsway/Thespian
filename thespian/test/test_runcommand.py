import sys
import datetime
from thespian.test import *
from thespian.actors import *
import thespian.runcommand

ask_timeout = datetime.timedelta(seconds=7)



class TestRunCommand(object):
    def testCreateActorSystem(self, asys):
        pass

    def testSimpleCommand(self, asys):
        cmd = asys.createActor(thespian.runcommand.RunCommand)
        res = asys.ask(cmd, thespian.runcommand.Command(sys.executable, ['-c', 'print("hello")']),
                       ask_timeout)
        print(res)
        assert res
        assert res.stdout == 'hello\n'


    def testSimpleTaggedCommand(self, asys):
        cmd = asys.createActor(thespian.runcommand.RunCommand)
        res = asys.ask(cmd, thespian.runcommand.Command(sys.executable, ['-c', 'print("hello")'],
                                                        logtag='hi'),
                       ask_timeout)
        print(res)
        assert res
        assert res.stdout == 'hello\n'


    def testNonExistentCommand(self, asys):
        cmd = asys.createActor(thespian.runcommand.RunCommand)
        res = asys.ask(cmd, thespian.runcommand.Command(sys.executable[3:-3], ['-c', 'print("hello")'],
                                                        logtag='hi'),
                       ask_timeout)
        print(res)
        assert not res
        assert res.stderr
        assert 'FAILED' in str(res)


    def testSlowCommandOutputOnly(self, asys):
        cmd = asys.createActor(thespian.runcommand.RunCommand)
        program = '\n'.join(['import time',
                             'print("hello")',
                             'time.sleep(0.5)',
                             'print("world")',
                             'time.sleep(0.5)',
        ])
        res = asys.ask(cmd, thespian.runcommand.Command(sys.executable, ['-u', '-c', program],
                                                        logtag='hi'),
                       ask_timeout)
        print(res)
        assert res
        assert res.stdout == 'hello\nworld\n'

    def testSlowCommandTimeout(self, asys):
        #actor_system_unsupported(asys, 'simpleSystemBase') #, 'multiprocQueueBase')
        cmd = asys.createActor(thespian.runcommand.RunCommand)
        program = '\n'.join(['import time',
                             'print("hello")',
                             'time.sleep(2.5)',
                             'print("world")',
                             'time.sleep(0.5)',
        ])
        res = asys.ask(cmd, thespian.runcommand.Command(sys.executable, ['-u', '-c', program],
                                                        logtag='hi',
                                                        timeout=2),
                       ask_timeout)
        print(res)
        assert not res

    def testSlowCommandTimeDelta(self, asys):
        #actor_system_unsupported(asys, 'simpleSystemBase') #, 'multiprocQueueBase')
        cmd = asys.createActor(thespian.runcommand.RunCommand)
        program = '\n'.join(['import time',
                             'print("hello")',
                             'time.sleep(2.5)',
                             'print("world")',
                             'time.sleep(0.5)',
        ])
        res = asys.ask(cmd, thespian.runcommand.Command(sys.executable, ['-u', '-c', program],
                                                        logtag='hi',
                                                        timeout=datetime.timedelta(seconds=2)),
                       ask_timeout)
        print(res)
        assert not res

    def testSlowCommandWantingInputNoneAvailable(self, asys):
        cmd = asys.createActor(thespian.runcommand.RunCommand)
        program = '\n'.join(['import time',
                             'print("hello")',
                             'time.sleep(0.5)',
                             'import sys',
                             'print("Who are you? "),',
                             'r = sys.stdin.read()',
                             'print("\\nhello %s" % r)',
                             'time.sleep(0.5)',
        ])
        res = asys.ask(cmd, thespian.runcommand.Command(sys.executable, ['-c', program],
                                                        logtag='hi'),
                       ask_timeout)
        print(res)
        assert res
        assert res.stdout == 'hello\nWho are you?  \nhello \n'

    def testSlowCommandWantingInputAvailable(self, asys):
        cmd = asys.createActor(thespian.runcommand.RunCommand)
        program = '\n'.join(['import time',
                             'print("hello")',
                             'time.sleep(0.5)',
                             'import sys',
                             'print("Who are you? "),',
                             'sys.stdout.flush()',
                             'r = sys.stdin.read()',
                             'print("\\nhello %s" % r)',
                             'time.sleep(0.5)',
        ])
        res = asys.ask(cmd, thespian.runcommand.Command(sys.executable, ['-c', program],
                                                        logtag='hi',
                                                        input_src='Harry\n'
        ),
                       ask_timeout)
        print(res)
        assert res
        assert res.stdout == 'hello\nWho are you?  \nhello Harry\n\n'

    def testSlowShellCommandWantingInputAvailable(self, asys):
        cmd = asys.createActor(thespian.runcommand.RunCommand)
        program = ';'.join(['echo howdy',
                            'sleep 1',
                            'echo -n Who are you?',
                            'read r',
                            'echo',
                            'echo hello $r',
                            'sleep 1',
        ])
        res = asys.ask(cmd, thespian.runcommand.Command('bash', ['-c', program],
                                                        logtag='yo',
                                                        input_src='Harry\n'
        ),
                       ask_timeout)
        print(res)
        assert res
        assert res.stdout == 'howdy\nWho are you?\nhello Harry\n'

    def testWatchedSlowCommandWantingInputAvailable(self, asys):
        cmd = asys.createActor(thespian.runcommand.RunCommand)
        program = '\n'.join(['import time',
                             'print("hello")',
                             'time.sleep(0.5)',
                             'import sys',
                             'print("Who are you? "),',
                             'sys.stdout.flush()',
                             'r = sys.stdin.read()',
                             'print("\\nhello %s" % r)',
                             'sys.stderr.write("All done\\n")',
                             'time.sleep(0.5)',
        ])
        watcher = asys.createActor(Watcher)
        res = asys.ask(cmd, thespian.runcommand.Command(sys.executable, ['-c', program],
                                                        logtag='hi',
                                                        input_src='Harry\n',
                                                        output_updates=watcher
        ),
                       ask_timeout)
        print(res)
        assert res
        assert res.stdout == 'hello\nWho are you?  \nhello Harry\n\n'
        assert res.stderr == 'All done\n'
        watched = asys.ask(watcher, 1, ask_timeout)
        print(res.stdout)
        print('--')
        print(''.join(watched[0]))
        print('==')
        print(res.stderr)
        print('--')
        print(''.join(watched[1]))
        assert (res.stdout, res.stderr) == (''.join(watched[0]), ''.join(watched[1]))

    def testWatchedSlowShellCommandWantingInputAvailable(self, asys):
        cmd = asys.createActor(thespian.runcommand.RunCommand)
        program = ';'.join(['echo howdy',
                            'sleep 1',
                            'echo -n Who are you?',
                            'read r',
                            'echo',
                            'echo hello $r',
                            'echo all done >&2',
                            'sleep 1',
        ])
        watcher = asys.createActor(Watcher)
        res = asys.ask(cmd, thespian.runcommand.Command('bash', ['-c', program],
                                                        logtag='yo',
                                                        input_src='Harry\n',
                                                        output_updates=watcher
        ),
                       ask_timeout)
        print(res)
        assert res
        assert res.stdout == 'howdy\nWho are you?\nhello Harry\n'
        assert res.stderr == 'all done\n'
        watched = asys.ask(watcher, 1, ask_timeout)
        print(res.stdout)
        print('--')
        print(''.join(watched[0]))
        print('==')
        print(res.stderr)
        print('--')
        print(''.join(watched[1]))
        assert (res.stdout, res.stderr) == (''.join(watched[0]), ''.join(watched[1]))


class Watcher(ActorTypeDispatcher):
    def __init__(self, *args, **kw):
        super(Watcher, self).__init__(*args, **kw)
        self.output = []
        self.errors = []
    def receiveMsg_CommandOutput(self, outmsg, sender):
        self.output.append(outmsg.output)
    def receiveMsg_CommandError(self, errmsg, sender):
        self.errors.append(errmsg.error_output)
    def receiveMsg_int(self, intmsg, sender):
        self.send(sender, (self.output, self.errors))