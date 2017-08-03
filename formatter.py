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
        print('feed recieved code:', self.code)

        tokens = tokenize.tokenize(self.linebytes().__next__)
        first = next(tokens)
        # we don't want to stuff `utf-8` at the start of every eval string
        if first.type != tokenize.ENCODING:
            raise ValueError('First token was not encoding!')
        first = next(tokens)
        # we want to make sure we're actually looking at a format string
        if first.type != tokenize.OP or first.string != '{':
            raise ValueError('First character was not an opening brace!')
        self.out_toks.append(first)

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
                        self.out_toks.append(tok)
                        ret = tokenize.untokenize(
                            self.tokens().__iter__()
                            )[1:-1]
                        ofs = self.inx + tok.end[1]
                        # subtract 2 from index because { and } are falsely
                        # counted as characters (see above string slice)
                        return ret, ofs - 2
            elif tok.type == tokenize.STRING:
                if tok.string.find('{') != -1 or tok.string.find('}') != -1:
                    # FOUND A FORMAT STRING
                    # WE NEED TO GO DEEEPER
                    depthformatter = ExtendedFormatter()
                    tok = tok._replace(string=
                        depthformatter.format(tok.string))
            elif tok.type == tokenize.INDENT:
                print('AN INDENT???')
                print(tok)
            self.out_toks.append(tok)

        raise SyntaxError('Missing end brace in format string')

class ExtendedFormatter():
    def __init__(self, depth=0, **kwargs):
        # generic parts
        self.env       = kwargs
        self.saved_env = kwargs
        self.cache     = {}
        self.depth = depth

    def save_env(self):
        self.saved_env = self.env.copy()

    def restore_env(self):
        self.env = self.saved_env

    def extend_env(self, vars={}, **kwargs):
        self.env.update(vars)
        self.env.update(kwargs)

    def reset_env(self):
        self.env = {}
        self.extend_env(extendedformat=self.format)

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

        return str(field_txt)

    def format_and_detect(self, orig_txt):
        """like format() but also returns a true/false value noting whether any
        replacements were detected / made

        useful for recursion, don't call it directly

        this recurses!"""
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
                    print('parsed as:', parsed[0])
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

        ret = self.format_and_detect(orig_txt)

        self.restore_env()

        return ret

formatter = ExtendedFormatter()
