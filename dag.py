class BaseEntity:
    def __init__(self):
        self.next_entities = []
        self.previous_entities = []
        self.features = {}
        self.part_of = []

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{self.features}>'

    def add_next(self, entity: 'BaseEntity') -> None:
        if entity in self.next_entities:
            raise ValueError(f'Second adding of {entity} after {self}')
        self.next_entities.append(entity)
        if self in entity.previous_entities:
            raise ValueError(f'Second adding of {self} before {entity}')
        entity.previous_entities.append(self)

    def like(self, other: 'BaseEntity'):
        if isinstance(self, other.__class__) or isinstance(other, self.__class__):
            return self.features == other.features
        return False


class ConnectingEntity(BaseEntity):
    def __str__(self):
        return f'•'


class TextEntity(BaseEntity):
    def __init__(self, text_content: str, **kwargs):
        super().__init__(**kwargs)
        self.features['text_content'] = text_content
    
    @property
    def text_content(self):
        return self.features['text_content']

    def __str__(self):
        return f'{self.text_content.__repr__()[1:-1]}'


def get_taken_places(line):
    return [i for i, ch in enumerate(line) if ch != ' ']

def squeese_lines(lines):
    for i in range(len(lines)-1, 1, -1):
        places_current = get_taken_places(lines[i])
        places_previous = get_taken_places(lines[i-1])
        if all(idx not in places_previous for idx in places_current):
            for idx in places_current:
                lines[i-1] = lines[i-1][:idx] + lines[i][idx] + lines[i-1][idx+1:]
            lines.pop(i)


class EntitiesDAG:
    def __init__(self, tokens: list[str]):
        self.head = ConnectingEntity()
        self.core_entities = []
        last_entity = self.head
        for t in tokens:
            next_raw = TextEntity(t)
            self.core_entities.append(next_raw)
            last_entity.add_next(next_raw)
            last_entity = ConnectingEntity()
            next_raw.add_next(last_entity)
        self.tail = last_entity
    
    def __repr__(self):
        text = ''.join(i.text_content for i in self.core_entities)
        if len(text) > 80:
            text = text[:60] + '...' + text[-17:]
        return f'{self.__class__.__name__}<{text}>'
    
    def pprint(self, max_width=80):
        lines = ['']
        pos = {}
        for i in self:
            if len(i.previous_entities) == 0:
                lines[0] += str(i)
                pos[i] = (0, len(lines[0]))
                continue
            # print(i.__repr__(), pos)
            prev_line, prev_x = pos[i.previous_entities[0]]
            if len(lines[prev_line]) == prev_x:
                lines[prev_line] += str(i)
                pos[i] = (prev_line, len(lines[prev_line]))
            else:
                for ln in range(prev_line+1, len(lines)+1):
                    if ln == len(lines):
                        lines.append('')
                    if len(lines[ln]) > prev_x:
                        continue
                    lines[ln] += ' '*(prev_x - len(lines[ln]))
                    lines[ln] += str(i)
                    pos[i] = (ln, len(lines[ln]))
                    break
        
        squeese_lines(lines) #  Move closer up entities when possible
        
        while len(lines) > 0:
            for i, L in enumerate(lines):
                print(L[:max_width])
                if len(lines[i]) > max_width:
                    lines[i] = L[max_width:]
                else:
                    lines[i] = ''
            while len(lines) > 0 and len(lines[-1]) == 0:
                lines = lines[:-1]
            if len(lines) > 0:
                print('-'*max_width)
    
    def __iter__(self):
        return self.iterate_depth()
    
    def iterate(self, entity=None, returned=None):
        # TODO: remove method
        if entity is None:
            yield from self.iterate(entity=self.head, returned=[])
            return
        if entity in returned:
            return
        yield entity
        returned.append(entity)
        for i in entity.next_entities:
            yield from self.iterate(entity=i, returned=returned)

    def iterate_width(self):
        to_process = [self.head]
        processed = {self.head}
        while len(to_process) > 0:
            i = to_process.pop(0)
            for j in i.next_entities:
                if j not in processed:
                    processed.add(j)
                    to_process.append(j)
            # print(f'Iter. yield {i}, {to_process=}')
            yield i
    
    def iterate_depth(self):
        to_process = [self.head]
        processed = {self.head}
        while len(to_process) > 0:
            i = to_process.pop()
            for j in i.next_entities[::-1]:
                if j not in processed:
                    processed.add(j)
                    to_process.append(j)
            # print(f'Iter. yield {i}, {to_process=}')
            yield i
