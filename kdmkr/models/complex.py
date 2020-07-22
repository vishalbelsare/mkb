# Reference: https://github.com/DeepGraphLearning/KnowledgeGraphEmbedding
import torch

from . import base

__all__ = ['ComplEx']


class ComplEx(base.BaseModel):
    """ComplEx


    Example:

        >>> from kdmkr import models

        >>> model = models.ComplEx(hidden_dim = 10, n_entity = 2, n_relation = 2, gamma = 1)

        >>> model
        ComplEx({'entity_dim': 20, 'relation_dim': 20, 'gamma': 1.0})

    """

    def __init__(self, hidden_dim, n_entity, n_relation, gamma):
        super().__init__(hidden_dim=hidden_dim, relation_dim=hidden_dim*2, entity_dim=hidden_dim*2,
                         n_entity=n_entity, n_relation=n_relation, gamma=gamma)

    def forward(self, sample, mode='default'):
        head, relation, tail = self.head_relation_tail(
            sample=sample, mode=mode)
        re_head, im_head = torch.chunk(head, 2, dim=2)
        re_relation, im_relation = torch.chunk(relation, 2, dim=2)
        re_tail, im_tail = torch.chunk(tail, 2, dim=2)

        if mode == 'head-batch':
            re_score = re_relation * re_tail + im_relation * im_tail
            im_score = re_relation * im_tail - im_relation * re_tail
            score = re_head * re_score + im_head * im_score
        else:
            re_score = re_head * re_relation - im_head * im_relation
            im_score = re_head * im_relation + im_head * re_relation
            score = re_score * re_tail + im_score * im_tail
        return score.sum(dim=2)

    def distill(self, sample):
        head, relation, tail = self.distillation_batch(sample)
        re_head, im_head = torch.chunk(head, 2, dim=-1)
        re_relation, im_relation = torch.chunk(relation, 2, dim=-1)
        re_tail, im_tail = torch.chunk(tail, 2, dim=-1)

        re_score = re_relation * re_tail + im_relation * im_tail
        im_score = re_relation * im_tail - im_relation * re_tail
        score = re_head * re_score + im_head * im_score
        return score.sum(dim=-1)
