import torch

from .base import BaseModel

__all__ = ["ComplEx"]


class ComplEx(BaseModel):
    """ComplEx model.

    Parameters:
        hiddem_dim (int): Embedding size of relations and entities.
        n_entity (int): Number of entities to consider.
        n_relation (int): Number of relations to consider.
        gamma (float): A higher gamma parameter increases the upper and lower bounds of the latent
            space and vice-versa.

    Example:

        >>> from mkb import models
        >>> from mkb import datasets

        >>> import torch
        >>> _ = torch.manual_seed(42)

        >>> dataset = datasets.CountriesS1(batch_size = 2)

        >>> model = models.ComplEx(
        ...    hidden_dim = 3,
        ...    entities = dataset.entities,
        ...    relations = dataset.relations,
        ...    gamma = 1
        ... )

        >>> model
        ComplEx model
            Entities embeddings dim  6
            Relations embeddings dim  6
            Gamma  1.0
            Number of entities  271
            Number of relations  2

        >>> model.embeddings['entities']['oceania']
        tensor([ 0.8911, -0.7287, -0.1702, -0.1209,  0.9779, -0.2161])

        >>> model.embeddings['relations']['locatedin']
        tensor([ 0.4710, -0.9410,  0.3869,  0.4595,  0.6451, -0.5734])

    References:
        1. [Trouillon, Théo, et al. "Complex embeddings for simple link prediction." International Conference on Machine Learning (ICML), 2016.](http://proceedings.mlr.press/v48/trouillon16.pdf)
        2. [Knowledge Graph Embedding](https://github.com/DeepGraphLearning/KnowledgeGraphEmbedding)

    """

    def __init__(self, hidden_dim, entities, relations, gamma):
        super().__init__(
            hidden_dim=hidden_dim,
            relation_dim=hidden_dim * 2,
            entity_dim=hidden_dim * 2,
            entities=entities,
            relations=relations,
            gamma=gamma,
        )

    def forward(self, sample, negative_sample=None, mode=None):
        head, relation, tail, shape = self.batch(
            sample=sample, negative_sample=negative_sample, mode=mode
        )

        re_head, im_head = torch.chunk(head, 2, dim=2)
        re_relation, im_relation = torch.chunk(relation, 2, dim=2)
        re_tail, im_tail = torch.chunk(tail, 2, dim=2)

        if mode == "head-batch":
            re_score = re_relation * re_tail + im_relation * im_tail
            im_score = re_relation * im_tail - im_relation * re_tail
            score = re_head * re_score + im_head * im_score

        else:
            re_score = re_head * re_relation - im_head * im_relation
            im_score = re_head * im_relation + im_head * re_relation
            score = re_score * re_tail + im_score * im_tail

        score = score.sum(dim=2)
        return score.view(shape)
