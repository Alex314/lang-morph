from collections.abc import Sequence, Iterable
import json

from dag import BaseEntity, ConnectingEntity, TextEntity
from analyser import BaseAnalyser


class WordEntity(BaseEntity):
    def __init__(self, text_content: str, features, **kwargs):
        super().__init__(**kwargs)
        self.features |= features
        self.features['text_content'] = text_content
    
    @property
    def text_content(self):
        return self.features['text_content']

    def __str__(self):
        main_form = self.features.get('main_form')
        main_form = f'|{main_form}' if main_form else ''
        return f'Word<{self.text_content}{main_form}>'


class WordAnalyser(BaseAnalyser):
    def __init__(self,
                 wordform_to_features,
                 start_to_continuations,
                 allow_intermediate_types: Iterable[BaseEntity] = (ConnectingEntity,)
                ):
        super().__init__(trigger_on_instances=[TextEntity])
        self.wordform_to_features = wordform_to_features
        self.start_to_continuations = start_to_continuations
        self.allow_intermediate_types = tuple(allow_intermediate_types)

    def trigger(self, dag_entity: TextEntity):
        continuations = self.start_to_continuations.get(dag_entity.text_content.lower(), [[]])
        
        for next_tokens in continuations:
            if len(next_tokens) == 0:  # Last entity of sequence matched
                self.embed_result(matched_dag_entities=[dag_entity])
                continue
            self.match_sequence(dag_entity, next_tokens)
    
    def match_sequence(self, dag_entity: BaseEntity, next_tokens: Sequence[str], matched=None):
        if matched is None:
            matched = [dag_entity]
        for i in dag_entity.next_entities:
            if isinstance(i, TextEntity) and i.text_content.lower() == next_tokens[0]:
                matched.append(i)
                if len(next_tokens) == 1:
                    self.embed_result(matched)
                    continue
                self.match_sequence(dag_entity=i, next_tokens=next_tokens[1:], matched=matched)
            elif isinstance(i, self.allow_intermediate_types):  # Pass allowed entity
                matched.append(i)
                self.match_sequence(dag_entity=i, next_tokens=next_tokens, matched=matched)
                
    
    def embed_result(self, matched_dag_entities: Sequence[BaseEntity]):
        text = ''.join(i.text_content for i in matched_dag_entities if isinstance(i, TextEntity))
        possible_features = self.wordform_to_features.get(text.lower(), [])
        for features in possible_features:
            new_entity = WordEntity(text_content=text, features=features)
            for i in matched_dag_entities[0].previous_entities:
                i.add_next(new_entity)
            for i in matched_dag_entities[-1].next_entities:
                new_entity.add_next(i)
            for i in matched_dag_entities:
                i.part_of.append(new_entity)
    
    def to_json(self, filepath: str, **json_kwargs):
        data = {
            'wordform_to_features': self.wordform_to_features,
            'start_to_continuations': self.start_to_continuations,
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, **json_kwargs)
    
    @classmethod
    def from_json(cls, filepath: str,
                  allow_intermediate_types: Iterable[BaseEntity] = (ConnectingEntity,)):
        with open(filepath) as f:
            data = json.load(f)
        return cls(**data, allow_intermediate_types=allow_intermediate_types)
