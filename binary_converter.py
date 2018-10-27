import math

i754_std = {
    16:dict(bias = (2**4)-1, exp = 5, sig = 10),
    32:dict(bias = (2**7)-1, exp = 8, sig = 23),
    64:dict(bias = (2**10)-1, exp = 11, sig = 52),
    128:dict(bias = (2**14)-1, exp = 15, sig = 112),
    256:dict(bias = (2**18)-1, exp = 19, sig = 236),
}

encode_std = {d:i for i,d in enumerate("0123456789abcdef")}

def pad_binary(val, digits=32, side='>', pad=0):
    """Pad val at left or right with character."""
    frmt = "{:" + str(pad) + side + str(digits) + "}"
    
    if val[0] == '-':
        return '-' + frmt.format(val[1:])
    else:
        return frmt.format(val)

def base_integer(val, base=2):
    """Convert base n val as integer to integer."""
    assert isinstance(val, str), 'val must be str'

    return int(val, base)

def base_fractional(val, base=2):
    """Convert base n val as fractional to fractional."""
    assert isinstance(val, str), 'val must be str'
    
    encode = encode_std
    e = 1
    agg = 0
    for d in str(val):
        agg += encode[str(d)] * base**-e
        e+=1
    return agg

def base_float(val, base=2):
    """Convert base n val as float to float."""
    assert isinstance(val, str), 'val must be str'
    
    if val[0] == '-':
        val = val[1:]
        neg = True
    else:
        neg = False

    if '.' in str(val):
        integer, fractional = val.split('.')
    else:
        integer = val
        fractional = 0

    integer = base_integer(integer, base)
    fractional = base_fractional(fractional, base)
    
    flt = integer + fractional
    
    if neg:
        flt = flt * -1
        
    return flt

def integer_base(val, digits=32, base=2):
    """Convert integer to base n val with max digits."""
    assert isinstance(val, int), 'val must be int'
    assert val >= 0, 'val must be positive'
    assert base > 1 and base < 17, 'base must be in [2,16]'
    
    encode = ''.join(encode_std.keys())
    remainder = val
    chars = []
    while(remainder > 0 and len(chars) < digits):
        char = remainder % base
        remainder = remainder // base    
        chars.insert(0, encode[char])
    return ''.join(str(c) for c in chars)

def fractional_base(val, digits=32, base=2):
    """Convert fractional to base n val with max digits."""
    assert isinstance(val, float), 'val must be float'
    assert val >= 0, 'val must be positive'
    assert val < 1, 'val must be less than 1'
    assert base > 1 and base < 17, 'base must be in [2,16]'

    encode = ''.join(encode_std.keys())
    chars = []
    fractional = abs(val)
    while(fractional > 0 and len(chars) < digits):
        product = fractional * base
        fractional, integer = math.modf(product)
        chars.append(encode[int(integer)])
    return ''.join(str(c) for c in chars)

def float_base(val, digits=32, base=2):
    """Convert float to base n val with max digits."""
    sign = '-' if val < 0 else ''
    fractional, integer = math.modf(abs(val))
    
    integer = integer_base(int(integer), digits, base)
    fractional = fractional_base(fractional, digits - len(integer), base)
    
    if not integer:
        integer = '0'
    if fractional:
        return sign + integer + '.' + fractional
    else:
        return sign + integer


def float_i754(val, precision=32):
    """Convert float to IEEE 754 of precision, no rounding support."""
    std = i754_std[precision]
    
    sign = '1' if val < 0 else '0'
    val = abs(val)
    
    exponent = math.floor(math.log2(val))
    characteristic = exponent + std['bias']
    mantissa = math.modf(val / 2**exponent)[0]

    e = std['exp']
    char = pad_binary(integer_base(characteristic, e), e, '>')
    
    s = std['sig']
    mant = pad_binary(fractional_base(mantissa, s), s, '<')
    return sign + char + mant

def i754_float(val, precision=32):
    """Convert IEEE 754 of precision to float."""
    std = i754_std[precision]
    
    sign = val[0]
    char = val[1:(std['exp']+1)]
    mant = val[(std['exp']+1):precision]
    
    exponent = base_integer(char) - std['bias']
    mantissa = base_fractional(mant)
    rep = (1 + mantissa) * 2**exponent
    if sign == 1: rep = rep * -1
    return rep

def integer_comp1(val, digits=32):
    """Convert integer to one's complement with max digits."""
    assert isinstance(val, int), 'val must be int'

    bits = integer_base(abs(val), digits)
    if val < 0:
        bits = [int(not int(b)) for b in bits]
        bits = ''.join(str(b) for b in bits)
        bits = pad_binary(bits, digits, pad=1)
    else:
        bits = pad_binary(bits, digits)
    return bits

def integer_comp2(val, digits=32):
    """Convert integer to two's complement with max digits."""
    assert isinstance(val, int), 'val must be int'
        
    bits = integer_comp1(val, digits)
    if bits[0] == '1':
        integer = base_integer(bits)
        integer += 1
        bits = integer_base(integer)
    return bits

def comp1_integer(val):
    """Convert one's complement to integer."""
    assert all([v in ['0','1'] for v in val]), 'val may contain [0,1]'
    
    if val[0] == '1':
        bits = [int(not int(v)) for v in val]
        bits = ''.join(str(b) for b in bits)
        integer = base_integer(bits) * -1
    else:
        integer = base_integer(val)
        
    return integer

def comp2_integer(val):
    """Convert two's complement to integer."""
    assert all([v in ['0','1'] for v in val]), 'val may contain [0,1]'
    
    integer = comp1_integer(val)
    if val[0] == '1':
        integer -= 1
        
    return integer

def convert(val, form='decimal', digits=32):
    """Convert val of form using max digts of precision.
    
    Args:
        val: int, float, str. Input value type dependent on form.
        form: str. Specifies form of input val. Supports:
            form    | desc             | type       | permitted
            --------|------------------|------------|-----------
            binary  | Binary           | str        | 0,1,.,-
            decimal | Decimal          | int, float | 0-9,.,-
            hex     | Hexadecimal      | str        | 0-f,.,-
            s754    | IEEE 754 Single  | str        | 0,1
            d754    | IEEE 754 Double  | str        | 0,1
            comp1   | One's Complement | str        | 0,1
            comp2   | Two's Complement | str        | 0,1
    
    Return:
        dict: val converted to all applicable forms.
    """
    forms = ['binary', 'decimal', 'hex', 's754', 'd754', 'comp1', 'comp2']
    assert form in forms, 'form must be one of: {}'.format(forms)
    
    if form == 'decimal':
        assert isinstance(val, (float, int)), 'decimal must be int or float'
    elif form == 'binary':
        valid = all([v in ['0','1', '.', '-'] for v in val])
        assert valid, 'binary must contain [0,1,.,-]'
    elif form == 'hex':
        valid = all([d in list(encode_std.keys()) + ['.', '-'] for d in val])
        assert valid, 'hex must contain [0-f,.,-]'
    elif form in ['s754', 'd754', 'comp1', 'comp2']:
        valid = all([v in ['0','1'] for v in val])
        assert valid, '{} must contain [0,1]'.format(form)
        assert isinstance(val, str), 'non-decimal must be str'
    
    if form == 'binary':
        decimal = base_float(val, 2)    
    elif form == 'decimal':
        decimal = val
    elif form == 'hex':
        decimal = base_float(val, 16)        
    elif form == 's754':
        decimal = i754_float(val, 32)
    elif form == 'd754':
        decimal = i754_float(val, 64)
    elif form == 'comp1':
        decimal = comp1_integer(val)
    elif form == 'comp2':
        decimal = comp2_integer(val)
   
    c = dict()
    c['val'] = val
    c['decimal'] = decimal
    c['hex'] = float_base(decimal, digits, 16)
    c['binary'] = float_base(decimal, digits)
    c['binaryP'] = pad_binary(c['binary'], digits)
    c['s754'] = float_i754(decimal, 32)
    c['d754'] = float_i754(decimal, 64)
    
    fractional, integer = math.modf(decimal)
    
    if fractional:
        c['comp1'] = None
        c['comp2'] = None
    else:
        c['comp1'] = integer_comp1(int(decimal), digits)
        c['comp2'] = integer_comp2(int(decimal), digits)
    
    return c
