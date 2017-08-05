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
        self.reset()

    def reset(self):
        self.code = ''
        self.inx = 0
        self.out_toks = []

    def linebytes(self):
        for line in self.code.splitlines():
            line += '\n'
            yield line.encode('utf-8')
            self.inx += len(line)

    def tokens(self):
        for t in self.out_toks:
            yield [t.type, t.string]

    def feed(self, code):
        self.reset()
        self.code = code

        tokens = tokenize.tokenize(self.linebytes().__next__)
        first = next(tokens)
        # we don't want to stuff `utf-8` at the start of every eval string
        if first.type != tokenize.ENCODING:
            raise ValueError('First token was not encoding!')
        # first = next(tokens)
        # we want to make sure we're actually looking at a format string
        # if first.type != tokenize.OP or first.string != '{':
            # raise ValueError('First character was not an opening brace!')
        # self.out_toks.append(first)

        bracedepth = 1
        out = []
        line_offset = 0
        for tok in tokens:
            if tok.type == tokenize.OP:
                if tok.string == '{':
                    bracedepth += 1
                elif tok.string == '}':
                    bracedepth -= 1
                    if bracedepth < 1:
                        self.out_toks.append(tok)
                        ret = tokenize.untokenize(
                            self.tokens().__iter__()
                            )[:-1]
                        ofs = self.inx + tok.end[1]
                        # subtract 2 from index because { and } are falsely
                        # counted as characters (see above string slice)
                        return ret, ofs - 1
            # elif tok.type == tokenize.STRING:
                # if tok.string.find('{') != -1 or tok.string.find('}') != -1:
                    # # FOUND A FORMAT STRING
                    # # WE NEED TO GO DEEEPER
                    # depthformatter = ExtendedFormatter()
                    # tok = tok._replace(string=
                        # depthformatter.format(tok.string))
            self.out_toks.append(tok)

        raise SyntaxError('Missing end brace in format string')

class ExtendedFormatter():
    def __init__(self, depth=0, **kwargs):
        # generic parts
        self.env       = kwargs
        self.saved_env = kwargs
        self.cache     = {}
        self.width = 80
        self.conversions = {
            'c': lambda x: x.center(self.width),
            'r': lambda x: x.rjust(self.width),
            'l': lambda x: x.lower(),
            'u': lambda x: x.upper(),
            't': string.capwords, # for [t]itlecase
        }


    def save_env(self):
        self.saved_env = self.env.copy()

    def restore_env(self):
        self.env = self.saved_env

    def extend_env(self, vars={}, **kwargs):
        self.env.update(vars)
        self.env.update(kwargs)

    def reset_env(self):
        self.env = {}
        # wrapper
        self.extend_env(extformat=self.format)

    def invalidate_cache(self):
        self.cache = {}

    def convert_field(self, field, spec):
        for c in self.conversions:
            if c in spec:
                field = self.conversions[c](field)

        return field

    def get_specs(self, field):
        """
        takes a format string, returns stripped field, conversion spec, and
        format spec
        only a 2-tuple of field and conversion for now
        use format(...) for formatting
        """

        field = field.strip()

        # if the very last character is ! it's not a conversion spec
        if '!' in field and field[-1] != '!':
            # possible conversion spec
            for i, c in enumerate(reversed(field)):
                cp = ord(c)
                # must be within a-z or A-Z or 0-9
                if cp == 0x21: #!
                    # ! followed by valid alphanumer sequence
                    inx = len(field) - i - 1
                    # + 1 to cut out `!`
                    return field[:inx], field[inx + 1:]
                elif not (
                        (0x30 <= cp <= 0x39) or
                        (0x41 <= cp <= 0x5a) or
                        (0x61 <= cp <= 0x7a)
                    ):
                    # invalid
                    break
        return field, ''

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

        field, conversion = self.get_specs(field)

        try:
            field_txt = self.multiline_eval(
                field,
                self.env # locals
            )
        except NameError as e:
            raise NameError(' '.join(e.args) + '\nEnvironment: \n' +
                repr(self.env.keys()) + '\nFormat string:\n' + field)
        except SyntaxError:
            raise SyntaxError('Invalid format string: ' + field)

        field_txt = self.convert_field(field_txt, conversion)

        return str(field_txt)

    def mainformat(self, orig_txt):
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
                    parsed = parser.feed(orig_txt[i:])
                    ret.append(self.parse_field(parsed[0]))
                    [next(txtiter) for x in range(parsed[1])]
            elif c == '}':
                i, nexttok = next(txtiter)
                if nexttok == '}':
                    # literal brace
                    ret.append('}')
                else:
                    # bad news buddy
                    raise SyntaxError('Illegal unmatched closing brace. '
                        'Repeat the brace (`}}`) to insert a literal brace.')
            else:
                ret.append(c)
        return ''.join(ret)

    def format(self, txt, vars={}, **kwargs):
        """no you cant pass `txt` as a kwarg stop asking"""
        # narrator: nobody ever asked

        self.save_env()
        vars.update(kwargs)
        self.extend_env(vars)

        orig_txt = '\n'.join(txt) if isinstance(txt, list) else txt

        ret = self.mainformat(orig_txt)

        self.restore_env()

        return ret

formatter = ExtendedFormatter()
extformat = formatter.format
