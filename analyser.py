from collections.abc import Iterable, Collection, Sequence

from dag import EntitiesDAG, BaseEntity, ConnectingEntity, TextEntity


class BaseAnalyser:
    def __init__(self, trigger_on_instances: Iterable[type]):
        self.trigger_on_instances = tuple(trigger_on_instances)

    def analyse(self, dag: EntitiesDAG):
        for i in dag:
            if isinstance(i, self.trigger_on_instances):
                self.trigger(i)
    
    def trigger(self, entity: BaseEntity):
        raise NotImplementedError('`trigger` function is not implemented for this analyser')


class NumberEntity(BaseEntity):
    def __init__(self, text_content: str, numerical_content, **kwargs):
        super().__init__(**kwargs)
        self.features['text_content'] = text_content
        self.features['numerical_content'] = numerical_content
    
    @property
    def text_content(self):
        return self.features['text_content']
    
    @property
    def numerical_content(self):
        return self.features['numerical_content']

    def __str__(self):
        return f'N<{self.text_content}>'


class IntegerAnalyser(BaseAnalyser):
    def __init__(self):
        super().__init__(trigger_on_instances=[TextEntity])

    def trigger(self, dag_entity: TextEntity):
        if all(i in '0123456789' for i in dag_entity.text_content):
            self.embed_result(matched_dag_entities=[dag_entity])
    
    def embed_result(self, matched_dag_entities: Sequence[BaseEntity]):
        assert len(matched_dag_entities) == 1
        text = matched_dag_entities[0].text_content
        n = int(text)
        new_entity = NumberEntity(text_content=text, numerical_content=n)
        
        
        for i in matched_dag_entities[0].previous_entities:
            i.add_next(new_entity)
        for i in matched_dag_entities[-1].next_entities:
            new_entity.add_next(i)
        for i in matched_dag_entities:
            i.part_of.append(new_entity)


integer_analyser = IntegerAnalyser()


class MatchAnalyser(BaseAnalyser):
    def __init__(self, valid_entity_sequences: Iterable[Collection[BaseEntity]],
                 match_entity_factory,
                 allow_intermediate_types: Iterable[BaseEntity] = (ConnectingEntity,),
                 **kwargs):
        super().__init__(**kwargs)
        self.match_entity_factory = match_entity_factory
        self.valid_entity_sequences = list(valid_entity_sequences)
        self.allow_intermediate_types = tuple(allow_intermediate_types)

    def trigger(self, dag_entity: BaseEntity):
        # print(f'{self.valid_entity_sequences=}')
        continuations = []
        for head, *tail in self.valid_entity_sequences:
            if head.like(dag_entity):
                continuations.append(tail)
        for next_entities in continuations:
            if len(next_entities) == 0:  # Last entity of sequence matched
                self.embed_result(matched_dag_entities=[dag_entity])
                continue
            self.match_sequence(dag_entity, next_entities)
    
    def match_sequence(self, dag_entity: BaseEntity, next_entities: Sequence[BaseEntity], matched=None):
        if matched is None:
            matched = [dag_entity]
        # raise NotImplementedError('entities sequence matching not supported yet')
        for i in dag_entity.next_entities:
            if i.like(next_entities[0]):
                matched.append(i)
                if len(next_entities) == 1:
                    self.embed_result(matched)
                    continue
                self.match_sequence(dag_entity=i, next_entities=next_entities[1:], matched=matched)
            elif isinstance(i, self.allow_intermediate_types):  # Pass allowed entity
                matched.append(i)
                self.match_sequence(dag_entity=i, next_entities=next_entities, matched=matched)
                
    
    def embed_result(self, matched_dag_entities: Sequence[BaseEntity]):
        new_entity = self.match_entity_factory(matched_dag_entities)
        for i in matched_dag_entities[0].previous_entities:
            i.add_next(new_entity)
        for i in matched_dag_entities[-1].next_entities:
            new_entity.add_next(i)
        for i in matched_dag_entities:
            i.part_of.append(new_entity)


class SpacingEntity(BaseEntity):
    def __init__(self, text_content: str, **kwargs):
        super().__init__(**kwargs)
        self.features['text_content'] = text_content
    
    @property
    def text_content(self):
        return self.features['text_content']

    def __str__(self):
        return '␣' #  *len(self.text_content)


def spacing_entity_factory(matched_entities: list[BaseEntity]):
    text = ''.join(i.text_content for i in matched_entities)
    return SpacingEntity(text_content=text)

valid_spacing_sequences = [
    [TextEntity(' ')],
    [TextEntity('\t')],
    [TextEntity('\n')],
]

spacing_analyser = MatchAnalyser(valid_entity_sequences=valid_spacing_sequences,
                                 match_entity_factory=spacing_entity_factory,
                                 trigger_on_instances=[TextEntity])


class PunctuationEntity(BaseEntity):
    def __init__(self, text_content: str, **kwargs):
        super().__init__(**kwargs)
        self.features['text_content'] = text_content
    
    @property
    def text_content(self):
        return self.features['text_content']

    def __str__(self):
        return f'Punct<{self.text_content}>' #  *len(self.text_content)


def punctuation_entity_factory(matched_entities: list[BaseEntity]):
    text = ''.join(i.features.get('text_content', '') for i in matched_entities)
    return PunctuationEntity(text_content=text)

valid_punctuation_sequences = [
    *([TextEntity(i)] for i in '.,!?–-—:…;'),
    [TextEntity('.'), TextEntity('.'), TextEntity('.')],
]

punctuation_analyser = MatchAnalyser(valid_entity_sequences=valid_punctuation_sequences,
                                     match_entity_factory=punctuation_entity_factory,
                                     trigger_on_instances=[TextEntity])
