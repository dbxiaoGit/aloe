"""
A Gherkin parser written using pyparsing
"""

from pyparsing import (CharsNotIn,
                       Group,
                       Keyword,
                       lineStart,
                       lineEnd,
                       OneOrMore,
                       Optional,
                       printables,
                       restOfLine,
                       stringEnd,
                       Suppress,
                       White,
                       Word,
                       ZeroOrMore)


class Tag(object):
    """
    A tag

    @tag
    """
    def __init__(self, tokens):
        self.tag = tokens[0]

    def __repr__(self):
        return '{klass}<{tag}>'.format(klass=self.__class__.__name__,
                                       tag=self.tag)


class Statement(object):
    """
    A statement
    """

    def __init__(self, tokens):

        # statements are made up of a statement sentence + optional data
        # the optional data can either be a table or a multiline string
        try:
            keyword, remainder, data = tokens
        except ValueError:
            keyword, remainder = tokens
            data = None

        self.statement = keyword + remainder

        if hasattr(data, 'table'):
            self.table = data

    def __repr__(self):
        return 'Statement<%s>' % self.statement


class Block(object):
    """
    A generic block, e.g. Feature:, Scenario:

    Blocks contain a number of statements
    """

    def __init__(self, tokens):
        self.statements = []

    def __repr__(self):
        return '{klass}<{n} statements>'.format(klass=self.__class__.__name__,
                                                n=len(self.statements))

    @classmethod
    def add_statements(cls, tokens):
        """
        Consume the statements to add to this block
        """

        self = tokens.pop(0)

        assert isinstance(self, cls)
        assert all(isinstance(token, Statement) for token in tokens)

        self.statements = tokens

        return self


class TaggedBlock(Block):
    """
    Tagged blocks contain type-specific child content as well as tags
    """
    def __init__(self, tokens):
        super(TaggedBlock, self).__init__(tokens)

        self.tags = tokens[:-1]
        self.name = tokens[-1]

        assert all(isinstance(tag, Tag) for tag in self.tags)

    def __repr__(self):
        return '{klass}<{tag}>'.format(
            klass=self.__class__.__name__,
            tag=','.join([self.name] +
                         [' @%s' % tag.tag for tag in self.tags]))


class Background(Block):
    pass


class Feature(TaggedBlock):
    pass


"""
End of Line
"""
EOL = Suppress(lineEnd)

"""
@tag
"""
TAG = Suppress('@') + Word(printables) + EOL
TAG.setParseAction(Tag)

"""
A table
"""
TABLE_ROW = Suppress('|') + OneOrMore(CharsNotIn('|\n') + Suppress('|')) + EOL
TABLE_ROW.setParseAction(lambda tokens: [v.strip() for v in tokens])
TABLE = Group(OneOrMore(Group(TABLE_ROW)))('table')

"""
Statement
"""
STATEMENT = \
    (Keyword('Given') | Keyword('When') | Keyword('Then') | Keyword('And')) + \
    restOfLine + \
    Optional(TABLE)
STATEMENT.setParseAction(Statement)

"""
Background:
"""
BACKGROUND_DEFN = \
    Suppress(Keyword('Background') + ':' + EOL)
BACKGROUND_DEFN.setParseAction(Background)

BACKGROUND = \
    BACKGROUND_DEFN + \
    ZeroOrMore(STATEMENT)
BACKGROUND.setParseAction(Background.add_statements)

"""
Feature: description
"""
FEATURE_DEFN = \
    ZeroOrMore(TAG) + \
    Suppress(Keyword('Feature') + ':' + White()) + \
    restOfLine
FEATURE_DEFN.setParseAction(Feature)

DESCRIPTION = restOfLine

"""
Complete feature file definition
"""
FEATURE = \
    FEATURE_DEFN + \
    Optional(BACKGROUND) + \
    stringEnd


if __name__ == '__main__':
    from pyparsing import ParseException
    try:
        print FEATURE.parseString('''
Feature: an example feature

    A short definition
    That is really not very interesting

    Background:
        Given something
''')
    except ParseException as e:
        print e

    tokens = FEATURE.parseString('''
@badger
@stoat
Feature: an example feature

    Background:
        Given I have badgers in the database
        And I am a penguin
        And this step has a table
            | badger           | stoat |
            | smells like teen | stoat |
''')
    print
    for token in tokens:
        print token
        print token.statements