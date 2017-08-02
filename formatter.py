import textwrap
import string
import tokenize
import ast

class ExtendedFormatParser():
    """
    parses extended format-literals from, uh, non-literal strings

    tl;dr: arbitrary nesting is in, format and conversion specs (ending a
    replacement field with `!x:yyy`) is out (direct function calls to str(),
    repr(), hex(), or format() are better)

    [1]: https://docs.python.org/3/library/string.html#string.Formatter.parse
    """
    def __init__(self):
        self.code = ''
        self.inx = 0

    def linebytes(self):
        for line in self.code.splitlines():
            line += '\n'
            yield line.encode('utf-8')
            self.inx += len(line)

    def feed(self, code):
        self.code = code
        self.inx = 0

        tokens = tokenize.tokenize(self.linebytes().__next__)
        first = next(tokens)
        if first.type != tokenize.ENCODING:
            raise ValueError('First token was not encoding!')
        first = next(tokens)
        if first.type != tokenize.OP or first.string != '{':
            raise ValueError('Second token was not an opening brace!')

        bracedepth = 0
        out = []
        line_offset = 0
        for tok in tokens:
            if tok.type == tokenize.OP:
                if tok.string == '{':
                    bracedepth += 1
                elif tok.string == '}':
                    bracedepth -= 1
                    if bracedepth < 1:
                        ofs = self.inx + tok.end[1]
                        # subtract 2 from index because { and } are falsely
                        # counted as characters
                        return self.code[1:ofs - 1], ofs - 2
            # print(tok)

        raise ValueError('Missing end brace?')

class ExtendedFormatter():
    def __init__(self, **kwargs):
        # generic parts
        self.env       = kwargs
        self.saved_env = kwargs
        self.cache     = {}

    def save_env(self):
        self.saved_env = self.env.copy()

    def restore_env(self):
        self.env = self.saved_env

    def extend_env(self, vars={}, **kwargs):
        self.env.update(vars)
        self.env.update(kwargs)

    def reset_env(self):
        self.env = {}

    def invalidate_cache(self):
        self.cache = {}

    def convert_field(self, field, spec):
        # look, the builtin modes
        # [r]epr
        # [s]tr
        # and [a]scii
        # are very uninteresting, so im cutting them out
        conversion_mapping = {
            'c': misc.center,
            'r': misc.right,
            'f': misc.fill,
            'l': lambda x: x.lower(),
            'u': lambda x: x.upper(),
            't': string.capwords, # for [t]itlecase
        }

        for c in conversion_mapping:
            if c in spec:
                field = conversion_mapping[c](field)

        return field

    def multiline_eval(self, expr, context):
        """
        Evaluate several lines of input, returning the result of the last line
        from https://stackoverflow.com/a/41472638/5719760
        """
        if expr.find('\n') == -1:
            # no newline
            return eval(expr, {}, context)
        tree = ast.parse(expr)
        # execute all lines except for the last
        exec_part = compile(ast.Module(tree.body[:-1]), 'file', 'exec')
        # eval the last line and return it
        eval_part = compile(ast.Expression(tree.body[-1].value), 'file', 'eval')
        exec(exec_part, {}, context)
        return eval(eval_part, {}, context)

    def parse_field(self, field):
        field_txt = ''

        if field is not None:
            try:
                # print('evaluating ', field)
                field_txt = self.multiline_eval(field,
                    self.env # locals
                )
            except NameError as e:
                raise NameError(' '.join(e.args) + '\nEnvironment: \n' +
                    repr(self.env.keys())) from None
            # except SyntaxError:
                # raise SyntaxError('Invalid format string: ' + field) from None

        return field_txt


    def format(self, txt, **kwargs):
        """no you cant pass `txt` as a kwarg stop asking"""
        # narrator: nobody ever asked

        self.save_env()
        self.extend_env(kwargs)

        orig_txt = '\n'.join(txt) if isinstance(txt, list) else txt
        ret = [] # list of characters / tokens

        parser = ExtendedFormatParser()

        txtiter = enumerate(orig_txt)
        for i, c in txtiter:
            if c == '{':
                i, nexttok = next(txtiter)
                if nexttok == '{':
                    # literal brace
                    ret.append('{')
                else:
                    # format string, start parsing as code
                    parsed = parser.feed(orig_txt[i - 1:])
                    ret.append(self.parse_field(parsed[0]))
                    [next(txtiter) for x in range(parsed[1])]
            else:
                ret.append(c)

        # parser.feed(orig_txt)

        self.restore_env()

        return ''.join(ret)

formatter = ExtendedFormatter()
