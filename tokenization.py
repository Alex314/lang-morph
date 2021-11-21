import re


def text_to_tokens(text: str) -> list[str]:
    #  TODO: rewrite to simple loop, no need for regexp
    regex = r'''
    (
        (?<=[a-zA-Zа-яА-ЯїґєіХЇҐЄІёЁ])(?=[a-zA-Zа-яА-ЯїґєіХЇҐЄІёЁ])  # Words
        |(?<=[0-9])(?=[0-9])  # Numbers
    )
    '''
    no_split_pos = [i.start() for i in re.finditer(regex, text, flags=re.VERBOSE | re.MULTILINE)]
    split_pos = [i for i in range(len(text)+1) if i not in no_split_pos]
    tokens = [text[start:end] for start, end in zip(split_pos[:-1], split_pos[1:])]
    return tokens