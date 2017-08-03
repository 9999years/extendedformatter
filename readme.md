In Python, despite *almost* sharing syntax, [`str.format()`][strformat] and
[`f`-string][fstring] literals have some unique (read: awful for me) differences:

    >>> f'{"ok".center(10)}'
    '    ok    '

    >>> '{"ok".center(10)}'.format()
    Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    KeyError: '"ok"'
    '"ok"'

    >>> format('{"ok".center(10)}')
    '{"ok".center(10)}'

There’s a simple reason for this: `f`-string literals can (with limitations!)
execute arbitrary code, and generally it’s bad to have a function as versatile
and widely-used as `str.format()` / `format()` be able to execute arbitrary code
in any untrusted string.

However! If you’re writing an application (like [The Daily Report][dailyreport])
where you trust arbitrary strings or don’t care if your users fuck up their own
computers, you might want to be able to use the `f`-string syntax in arbitrary
strings — a bridge between having an end-user write a whole Python file and
being able to expose a pretty and simple public API with the option to expand
into arbitrary Python code.

# Understand the risks

I won’t beat around the bush: This module **pivots** around evaluating and
executing **completely arbitrary** strings. If any user input is inserted into
those strings, the user can execute anything they want — remember that multiline
expressions are allowed, with the only requirement being that the last
expression is casted to a string. You were warned!

# Features

This module is an extension to and a reimplementation of Python’s `f`-strings.
It allows treating arbitrary expressions as `f`-strings as well as extending
their syntax, allowing comments, multiple expressions (using the last one,
casted to a string, as the result), and nesting.

Other languages have similar features to what I offer (sans, AFAIK, arbitrary
string evaluation): PowerShell has [`"$(expr)"`][powershellexpr], Ruby has
[`"#{expr}"`][rubyexpr], and Perl has [`"@{[expr]}"`][perlexpr], but Python is
left out, with only the limited offerings of `f`-strings!

As of the time of this writing, everything but nesting works! I think that’s
pretty fantastic for about 120 SLOC!

[strformat]: https://docs.python.org/3/library/stdtypes.html#str.format
[fstring]: https://docs.python.org/3/reference/lexical_analysis.html#f-strings
[powershellexpr]: https://ss64.com/ps/syntax-operators.html
[rubyexpr]: http://fullybaked.co.uk/articles/tip-ruby-string-interpolation-with-hashes
[perlexpr]: https://stackoverflow.com/a/3939925/5719760
[dailyreport]: https://github.com/9999years/daily-report