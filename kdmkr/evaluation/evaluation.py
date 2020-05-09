import torch

from creme       import stats
from torch.utils import data

from ..stream import base


__all__ = ['Evaluation']


class Evaluation:
    """Evaluate model on selected dataset.

    Example:

        :
            >>> from kdmkr import stream
            >>> from kdmkr import evaluation
            >>> from kdmkr import model
            >>> from kdmkr import loss

            >>> import torch

            >>> _ = torch.manual_seed(42)

            >>> train = [
            ...     (0, 0, 1),
            ...     (0, 1, 1),
            ...     (2, 0, 3),
            ...     (2, 1, 3),
            ... ]

            >>> valid = [
            ...     (0, 0, 1),
            ...     (2, 1, 3),
            ... ]

            >>> test = [
            ...     (0, 0, 1),
            ...     (2, 1, 3),
            ... ]

            >>> entities = {
            ... 'e0': 0,
            ... 'e1': 1,
            ... 'e2': 2,
            ... 'e3': 3,
            ... }

            >>> relations = {
            ... 'r0': 0,
            ... 'r1': 1,
            ... }

            >>> dataset = stream.FetchDataset(train=train, test=test, entities=entities,
            ...    relations=relations, negative_sample_size=2, batch_size=1, seed=42)

            >>> rotate = model.RotatE(hidden_dim=3, n_entity=dataset.n_entity,
            ...    n_relation=dataset.n_relation, gamma=1)

            >>> optimizer = torch.optim.Adam(
            ...    filter(lambda p: p.requires_grad, rotate.parameters()),
            ...    lr = 0.5,
            ... )

            >>> loss = loss.Adversarial()

            >>> for _ in range(10):
            ...     positive_sample, negative_sample, weight, mode=next(dataset)
            ...     positive_score = rotate(positive_sample)
            ...     negative_score = rotate((positive_sample, negative_sample), mode=mode)
            ...     loss(positive_score, negative_score, weight, alpha=0.5).backward()
            ...     _ = optimizer.step()

            >>> rotate = rotate.eval()

            >>> validation = evaluation.Evaluation(train=train, valid=valid, test=test,
            ...     entities=entities, relations=relations, batch_size=1)

            >>> scores = validation.eval(model=rotate)

            >>> print(scores)
            HITS@10: 1.000000, HITS@1: 0.250000, HITS@3: 1.000000, MR: 2.000000, MRR: 0.583333

    """
    def __init__(self, train, valid, test, entities, relations, batch_size, device='cpu',
        num_workers=1):
        self.train = train
        self.valid = valid
        self.test  = test
        self.entities = entities
        self.relations = relations
        self.batch_size = batch_size
        self.device = device
        self.num_workers = num_workers

    def _get_test_loader(self, triples, batch_size, mode):
        test_dataset = base.TestDataset(triples=triples,
            all_true_triples=self.train + self.test + self.valid, entities=self.entities,
            relations=self.relations, mode=mode)
        return data.DataLoader(dataset=test_dataset, batch_size=batch_size,
            num_workers=self.num_workers, collate_fn=base.TestDataset.collate_fn)

    def get_test_stream(self):
        head_loader = self._get_test_loader(triples=self.test, batch_size=self.batch_size,
            mode='head-batch')
        tail_loader = self._get_test_loader(triples=self.test, batch_size=self.batch_size,
            mode='tail-batch')
        return [head_loader, tail_loader]

    def eval(self, model):
        """Evaluate selected model with the metrics: MRR, MR, HITS@1, HITS@3, HITS@10"""
        metrics = {metric: stats.Mean() for metric in ['MRR', 'MR', 'HITS@1', 'HITS@3', 'HITS@10']}
        with torch.no_grad():

            for test_set in self.get_test_stream():

                for step, (positive_sample, negative_sample, filter_bias, mode) in enumerate(test_set):

                    positive_sample = positive_sample.to(self.device)

                    negative_sample = negative_sample.to(self.device)

                    filter_bias = filter_bias.to(self.device)

                    score = model(sample=(positive_sample, negative_sample), mode=mode)

                    score += filter_bias

                    argsort = torch.argsort(score, dim = 1, descending=True)

                    if mode == 'head-batch':
                        positive_arg = positive_sample[:, 0]

                    elif mode == 'tail-batch':
                        positive_arg = positive_sample[:, 2]

                    batch_size = positive_sample.size(0)

                    for i in range(batch_size):
                        #Notice that argsort is not ranking
                        ranking = (argsort[i, :] == positive_arg[i]).nonzero()
                        assert ranking.size(0) == 1

                        #ranking + 1 is the true ranking used in evaluation metrics
                        ranking = 1 + ranking.item()

                        metrics['MRR'].update(1.0/ranking)
                        metrics['MR'].update(ranking)
                        metrics['HITS@1'].update(1.0 if ranking <= 1 else 0.0)
                        metrics['HITS@3'].update(1.0 if ranking <= 3 else 0.0)
                        metrics['HITS@10'].update(1.0 if ranking <= 10 else 0.0)

        score = {f'{name}: {metric.get():4f}' for name, metric in metrics.items()}

        return ', '.join(sorted(score))
