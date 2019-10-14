from __future__ import absolute_import
import codecs
from math import isinf, isnan

import six

from dlgo.gosgf import sgf_grammar
from six.moves import range

if six.PY2:
    _bytestring_ord = ord
else:
    def identity(x):
        return x


    _bytestring_ord = identity


def normalise_charset_name(s):
    if not isinstance(s, six.text_type):
        s = s.decode('ascii')
    return (codecs.lookup(s).name.replace("_", "-").upper()
            .replace("ISO8859", "ISO-8859"))


def interpret_go_point(s, size):
    if s == b"" or (s == b"tt" and size <= 19):
        return None

    col_s, row_s = s
    col = _bytestring_ord(col_s) - 97
    row = size - _bytestring_ord(row_s) + 96
    if not ((0 <= col < size) and (0 <= row < size)):
        raise ValueError
    return row, col


def serialise_go_point(move, size):
    if not 1 <= size <= 26:
        raise ValueError
    if move is None:

        if size <= 19:
            return b"tt"
        else:
            return b""
    row, col = move
    if not ((0 <= col < size) and (0 <= row < size)):
        raise ValueError
    col_s = "abcdefghijklmnopqrstuvwxy"[col].encode('ascii')
    row_s = "abcdefghijklmnopqrstuvwxy"[size - row - 1].encode('ascii')
    return col_s + row_s


class _Context:
    def __init__(self, size, encoding):
        self.size = size
        self.encoding = encoding


def interpret_none(s, context=None):
    return True


def serialise_none(b, context=None):
    return b""


def interpret_number(s, context=None):
    return int(s, 10)


def serialise_number(i, context=None):
    return ("%d" % i).encode('ascii')


def interpret_real(s, context=None):
    result = float(s)
    if isinf(result):
        raise ValueError("infinite")
    if isnan(result):
        raise ValueError("not a number")
    return result


def serialise_real(f, context=None):
    f = float(f)
    try:
        i = int(f)
    except OverflowError:
        raise ValueError
    if f == i:
        return str(i).encode('ascii')
    s = repr(f)
    if 'e-' in s:
        return "0".encode('ascii')
    return s.encode('ascii')


def interpret_double(s, context=None):
    if s.strip() == b"2":
        return 2
    else:
        return 1


def serialise_double(i, context=None):
    if i == 2:
        return "2"
    return "1"


def interpret_colour(s, context=None):
    colour = s.decode('ascii').lower()
    if colour not in ('b', 'w'):
        raise ValueError
    return colour


def serialise_colour(colour, context=None):
    if colour not in ('b', 'w'):
        raise ValueError
    return colour.upper().encode('ascii')


def _transcode(s, encoding):
    u = s.decode(encoding)
    if encoding == "UTF-8":
        return s
    else:
        return u.encode("utf-8")


def interpret_simpletext(s, context):
    return _transcode(sgf_grammar.simpletext_value(s), context.encoding)


def serialise_simpletext(s, context):
    if context.encoding != "UTF-8":
        s = s.decode("utf-8").encode(context.encoding)
    return sgf_grammar.escape_text(s)


def interpret_text(s, context):
    return _transcode(sgf_grammar.text_value(s), context.encoding)


def serialise_text(s, context):
    if context.encoding != "UTF-8":
        s = s.decode("utf-8").encode(context.encoding)
    return sgf_grammar.escape_text(s)


def interpret_point(s, context):
    result = interpret_go_point(s, context.size)
    if result is None:
        raise ValueError
    return result


def serialise_point(point, context):
    if point is None:
        raise ValueError
    return serialise_go_point(point, context.size)


def interpret_move(s, context):
    return interpret_go_point(s, context.size)


def serialise_move(move, context):
    return serialise_go_point(move, context.size)


def interpret_point_list(values, context):
    result = set()
    for s in values:

        p1, is_rectangle, p2 = s.partition(b":")
        if is_rectangle:
            top, left = interpret_point(p1, context)
            bottom, right = interpret_point(p2, context)
            if not (bottom <= top and left <= right):
                raise ValueError
            for row in range(bottom, top + 1):
                for col in range(left, right + 1):
                    result.add((row, col))
        else:
            pt = interpret_point(p1, context)
            result.add(pt)
    return result


def serialise_point_list(points, context):
    result = [serialise_point(point, context) for point in points]
    result.sort()
    return result


def interpret_AP(s, context):
    application, version = sgf_grammar.parse_compose(s)
    if version is None:
        version = b""
    return (interpret_simpletext(application, context),
            interpret_simpletext(version, context))


def serialise_AP(value, context):
    application, version = value
    return sgf_grammar.compose(serialise_simpletext(application, context),
                               serialise_simpletext(version, context))


def interpret_ARLN_list(values, context):
    result = []
    for s in values:
        p1, p2 = sgf_grammar.parse_compose(s)
        result.append((interpret_point(p1, context),
                       interpret_point(p2, context)))
    return result


def serialise_ARLN_list(values, context):
    return [b":".join((serialise_point(p1, context), serialise_point(p2, context)))
            for p1, p2 in values]


def interpret_FG(s, context):
    if s == b"":
        return None
    flags, name = sgf_grammar.parse_compose(s)
    return int(flags), interpret_simpletext(name, context)


def serialise_FG(value, context):
    if value is None:
        return b""
    flags, name = value
    return str(flags).encode('ascii') + b":" + serialise_simpletext(name, context)


def interpret_LB_list(values, context):
    result = []
    for s in values:
        point, label = sgf_grammar.parse_compose(s)
        result.append((interpret_point(point, context),
                       interpret_simpletext(label, context)))
    return result


def serialise_LB_list(values, context):
    return [b":".join((serialise_point(point, context), serialise_simpletext(text, context)))
            for point, text in values]


class Property_type:

    def __init__(self, interpreter, serialiser, uses_list,
                 allows_empty_list=False):
        self.interpreter = interpreter
        self.serialiser = serialiser
        self.uses_list = bool(uses_list)
        self.allows_empty_list = bool(allows_empty_list)


def _make_property_type(type_name, allows_empty_list=False):
    return Property_type(
        globals()["interpret_" + type_name],
        globals()["serialise_" + type_name],
        uses_list=(type_name.endswith("_list")),
        allows_empty_list=allows_empty_list)


_property_types_by_name = {
    'none': _make_property_type('none'),
    'number': _make_property_type('number'),
    'real': _make_property_type('real'),
    'double': _make_property_type('double'),
    'colour': _make_property_type('colour'),
    'simpletext': _make_property_type('simpletext'),
    'text': _make_property_type('text'),
    'point': _make_property_type('point'),
    'move': _make_property_type('move'),
    'point_list': _make_property_type('point_list'),
    'point_elist': _make_property_type('point_list', allows_empty_list=True),
    'stone_list': _make_property_type('point_list'),
    'AP': _make_property_type('AP'),
    'ARLN_list': _make_property_type('ARLN_list'),
    'FG': _make_property_type('FG'),
    'LB_list': _make_property_type('LB_list'),
}

P = _property_types_by_name

_property_types_by_ident = {
    b'AB': P['stone_list'],
    b'AE': P['point_list'],
    b'AN': P['simpletext'],
    b'AP': P['AP'],
    b'AR': P['ARLN_list'],
    b'AW': P['stone_list'],
    b'B': P['move'],
    b'BL': P['real'],
    b'BM': P['double'],
    b'BR': P['simpletext'],
    b'BT': P['simpletext'],
    b'C': P['text'],
    b'CA': P['simpletext'],
    b'CP': P['simpletext'],
    b'CR': P['point_list'],
    b'DD': P['point_elist'],
    b'DM': P['double'],
    b'DO': P['none'],
    b'DT': P['simpletext'],
    b'EV': P['simpletext'],
    b'FF': P['number'],
    b'FG': P['FG'],
    b'GB': P['double'],
    b'GC': P['text'],
    b'GM': P['number'],
    b'GN': P['simpletext'],
    b'GW': P['double'],
    b'HA': P['number'],
    b'HO': P['double'],
    b'IT': P['none'],
    b'KM': P['real'],
    b'KO': P['none'],
    b'LB': P['LB_list'],
    b'LN': P['ARLN_list'],
    b'MA': P['point_list'],
    b'MN': P['number'],
    b'N': P['simpletext'],
    b'OB': P['number'],
    b'ON': P['simpletext'],
    b'OT': P['simpletext'],
    b'OW': P['number'],
    b'PB': P['simpletext'],
    b'PC': P['simpletext'],
    b'PL': P['colour'],
    b'PM': P['number'],
    b'PW': P['simpletext'],
    b'RE': P['simpletext'],
    b'RO': P['simpletext'],
    b'RU': P['simpletext'],
    b'SL': P['point_list'],
    b'SO': P['simpletext'],
    b'SQ': P['point_list'],
    b'ST': P['number'],
    b'SZ': P['number'],
    b'TB': P['point_elist'],
    b'TE': P['double'],
    b'TM': P['real'],
    b'TR': P['point_list'],
    b'TW': P['point_elist'],
    b'UC': P['double'],
    b'US': P['simpletext'],
    b'V': P['real'],
    b'VW': P['point_elist'],
    b'W': P['move'],
    b'WL': P['real'],
    b'WR': P['simpletext'],
    b'WT': P['simpletext'],
}
_text_property_type = P['text']

del P


class Presenter(_Context):

    def __init__(self, size, encoding):
        try:
            encoding = normalise_charset_name(encoding)
        except LookupError:
            raise ValueError("unknown encoding: %s" % encoding)
        _Context.__init__(self, size, encoding)
        self.property_types_by_ident = _property_types_by_ident.copy()
        self.default_property_type = _text_property_type

    def get_property_type(self, identifier):

        return self.property_types_by_ident[identifier]

    def register_property(self, identifier, property_type):

        self.property_types_by_ident[identifier] = property_type

    def deregister_property(self, identifier):

        del self.property_types_by_ident[identifier]

    def set_private_property_type(self, property_type):

        self.default_property_type = property_type

    def _get_effective_property_type(self, identifier):
        try:
            return self.property_types_by_ident[identifier]
        except KeyError:
            result = self.default_property_type
            if result is None:
                raise ValueError("unknown property")
            return result

    def interpret_as_type(self, property_type, raw_values):
        if not raw_values:
            raise ValueError("no raw values")
        if property_type.uses_list:
            if raw_values == [b""]:
                raw = []
            else:
                raw = raw_values
        else:
            if len(raw_values) > 1:
                raise ValueError("multiple values")
            raw = raw_values[0]
        return property_type.interpreter(raw, self)

    def interpret(self, identifier, raw_values):

        return self.interpret_as_type(
            self._get_effective_property_type(identifier), raw_values)

    def serialise_as_type(self, property_type, value):

        serialised = property_type.serialiser(value, self)
        if property_type.uses_list:
            if serialised == []:
                if property_type.allows_empty_list:
                    return [b""]
                else:
                    raise ValueError("empty list")
            return serialised
        else:
            return [serialised]

    def serialise(self, identifier, value):

        return self.serialise_as_type(
            self._get_effective_property_type(identifier), value)
