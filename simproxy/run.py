import readline, os, rlcompleter, atexit, code, sys, time

class SimProxyConsole(code.InteractiveConsole):
    def __init__(self, clt=None, locals=None, filename="<console>",
                 histfile=os.path.expanduser("~/.simtool-history")):
        code.InteractiveConsole.__init__(self, locals, filename)
        self.init_history(histfile)

    def init_history(self, histfile):
        readline.parse_and_bind("tab: complete")
        if hasattr(readline, "read_history_file"):
            try:
                readline.read_history_file(histfile)
            except IOError:
                pass
            atexit.register(self.save_history, histfile)

    def save_history(self, histfile):
        readline.write_history_file(histfile)

    # def send_cmd(self, line):
    #     self.client.send(line+'\r\n')

    # def cmd_result(self): 
    #     st = time.time()
    #     while True:
    #         self.buf += self.client.recv(1024)
    #         bf = self.buf.split('\r\n')
    #         if len(bf) > 1:
    #             self.buf = bf[1]
    #             return bf[0]
    #         if time.time() - st > 10:
    #             return 'Timeout'

    def mon_show(self):
        while True:
            sys.stdout.write(self.client.recv(1024))
            time.sleep(0.5)

    def push(self, line):
        # you can filter input here by doing something like
        # line = filter(line)
        if line == 'quit':
            code.InteractiveConsole.push(self, 'co.close()')
            code.InteractiveConsole.push(self, 'quit()')
            return
        code.InteractiveConsole.push(self, line)
        # if line[0] != '#':
        #     a = code.InteractiveConsole.push(self, line)
        #     return
        # self.send_cmd(line[1:])
        # if line == '#mon':
        #     self.mon_show()
        # else:
        #     print self.cmd_result()
        #     code.InteractiveConsole(self,line)
        # self.return_output()
        # output = self.cache.flush()
        # you can filter the output here by doing something like
        # output = filter(output)
        # return

    def interact(self):
        code.InteractiveConsole.push(self, 'from simproxy.net import *')
        code.InteractiveConsole.push(self, 'sp=SimProxySck()')
        code.InteractiveConsole.interact(self, 'Use "sp" var to comunicate with server.')

def main():
    hc = SimProxyConsole()
    hc.interact()

if __name__ == "__main__":
    main()
