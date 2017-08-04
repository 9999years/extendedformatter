from extendedformatter import formatter, extformat

def format_assert(fstr, val, *vars, **kwargs):
    formatter.reset_env()
    formatter.extend_env(*vars, **kwargs)
    def success():
        print('SUCCESS')
    def failure():
        print('FAILURE')
        print('FORMAT STRING IS:  ', fstr)
        print('EXPECTED OUTPUT IS:', val)
        print('OUTPUT IS:         ', a)


    # try:
    a = extformat(fstr)
    # except:
        # a = ''
        # failure()

    if a == val:
        success()
    else:
        failure()

# possible astral codepoint counting bugs
format_assert('fire {" 🔥"} fire', 'fire  🔥 fire')
# possible astral codepoint counting bugs
format_assert('fire 🔥 fire', 'fire 🔥 fire')
# variable substitution
format_assert('{foo}def', 'abcdef', foo='abc')
# string substitution
format_assert('start{"mid"}end', 'startmidend')
# checking string parsing
# remember to escape braces!
format_assert('start{"false brace ending}"}end',
    'startfalse brace ending}end')
# multiline format fields
format_assert(r'''start{
# multiline expressions can contain constants or arbitrary code
# (as well as comments!)
for x in range(10):
    pass
"why not?".rjust(10)
}end''', 'start  why not?end')
format_assert('''sum of numbers 1 through 100: {
sum = 0
for x in range(101):
    sum += x
sum}''', 'sum of numbers 1 through 100: 5050')
# you can do anything if it's escaped
# no reason to escape the ' as \x27 other than being extra extra
format_assert('{\'don\\\x27t actually do this ever\'}',
    'don\'t actually do this ever')
# literal braces
format_assert('{{ }}', '{ }')
# nesting, and a practical (?) application
# note that you do have to pass format variables in as keyword arguments
# (or locals()) if you prefer
format_assert('''factorials of n=1 through n=5:
{
ret = ''
for top in range(1, 6):
    # regular f-string within extended format string
    ret += extformat('{top}! = ', top=top)
    fact = 1
    for n in range(top, 0, -1):
        fact *= n
    ret += str(fact) + '\\n'
ret
}''', '''factorials of n=1 through n=5:
1! = 1
2! = 2
3! = 6
4! = 24
5! = 120
''')
# triple nesting
# this is 5 factorial
# dont do this
format_assert(
"""{ 5 * int(extformat('{4 * 3 * int(extformat("{int(6 / 3)}"))}'))} = 120""", 
'120 = 120')
