from django.utils import timezone
import datetime
from textwrap import wrap

class Transaction():
    "a transacation"
    
    def __init__(self, dt, amount, descr=""):
        self.dt = dt
        self.description = descr
        self.amount = amount

    def __add__(self, a):
        if isinstance(a, Transaction):
            return self.amount + a.amount
        else:
            return self.amount + a

    def __radd__(self, a):
        return self + a

    def __str__(self, wrap_description=True):
        if wrap_description:
            descr_lines = wrap(self.description, width=24)
        else:
            descr_lines = self.description

        outstr = timezone.localtime(self.dt).ctime() + '   {:<24s}'.format(descr_lines[0]) + '   ${:>8.2f}'.format(self.amount) 
        if hasattr(self, 'balance'):
            outstr += '   ${:>8.2f}'.format(self.balance)

        for line in descr_lines[2:]: outstr += '\n                           {:<24s}'.format(line)

        return outstr

    
