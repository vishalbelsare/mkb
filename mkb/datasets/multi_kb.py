import copy
import random

import numpy as np

from .dataset import Dataset

__all__ = ["MultiKb"]


class MultiKb(Dataset):
    """Split input dataset into multiples parts and control fraction of aligned entities.

    Parameters:
        dataset (mkb.datasets): Dataset to split into multiple kg.
        id_set (int): Selected part of the splitted dataset.
        n_part (int): Number of splits of the input dataset.
        aligned_entities (float): Fraction of aligned entities between datasets.

    Example:

        >>> from mkb import datasets

        >>> dataset = datasets.MultiKb(
        ...     dataset = datasets.Umls(batch_size = 1, shuffle = False, seed = 42),
        ...     id_set = [0, 1, 2, 3, 4],
        ...     n_part = 10,
        ...     aligned_entities = 0.8,
        ... )

        >>> dataset
        Umls_[0, 1, 2, 3, 4]_10_80 dataset
            Batch size         1
            Entities           135
            Relations          46
            Shuffle            False
            Train triples      2610
            Validation triples 652
            Test triples       661
            Umls cutted in     10
            Umls set           [0, 1, 2, 3, 4]
            Aligned entities   80.0%

        >>> assert len(dataset.classification_valid['X']) == len(dataset.classification_valid['y'])
        >>> assert len(dataset.classification_test['X']) == len(dataset.classification_test['y'])

        >>> assert len(dataset.classification_valid['X']) == len(dataset.valid) * 2
        >>> assert len(dataset.classification_test['X']) == len(dataset.test) * 2

        All train triples are used to filter existing triples when initializing negative
        sampling with MultiKb.
        >>> len(dataset.train_triples)
        5216

        All true triples are used to filter existing triples when evaluating filtered metrics
        with MultiKb.
        >>> len(dataset.true_triples)
        6529

    """

    def __init__(self, dataset, id_set, n_part, aligned_entities=1.0):
        if not isinstance(id_set, list):
            id_set = [id_set]
        self.id_set = id_set
        self.n_part = n_part
        self.aligned_entities = aligned_entities
        self.filename = dataset.filename
        self.dataset_name = dataset.name

        train, self.excluded_triples = self.split_train(
            train=dataset.train, n_part=n_part, id_set=id_set, seed=dataset.seed
        )

        super().__init__(
            train=train,
            valid=dataset.valid,
            test=dataset.test,
            entities=self.corrupt_entities(entities=dataset.entities, seed=dataset.seed),
            relations=dataset.relations,
            batch_size=dataset.batch_size,
            shuffle=dataset.shuffle,
            num_workers=dataset.num_workers,
            seed=dataset.seed,
            classification=dataset.classification,
            classification_valid=dataset.classification_valid,
            classification_test=dataset.classification_test,
        )

    @property
    def true_triples(self):
        """Set of triples used dedicated to filtering to evualuate models."""
        return self.train + self.excluded_triples + self.test + self.valid

    @property
    def train_triples(self):
        """Filter all train triples in negative sampling even those that are excluded from the train
        set.
        """
        return self.train + self.excluded_triples

    @property
    def name(self):
        return (
            f"{self.dataset_name}_{self.id_set}_{self.n_part}_{round(self.aligned_entities * 100)}"
        )

    @property
    def _repr_title(self):
        return f"{self.name} dataset"

    @property
    def _repr_content(self):
        """The items that are displayed in the __repr__ method.
        This property can be overriden in order to modify the output of the __repr__ method.
        """
        return {
            "Batch size": f"{self.batch_size}",
            "Entities": f"{self.n_entity}",
            "Relations": f"{self.n_relation}",
            "Shuffle": f"{self.shuffle}",
            "Train triples": f"{len(self.train) if self.train else 0}",
            "Validation triples": f"{len(self.valid) if self.valid else 0}",
            "Test triples": f"{len(self.test) if self.test else 0}",
            f"{self.dataset_name} cutted in": f"{self.n_part}",
            f"{self.dataset_name} set": f"{self.id_set}",
            "Aligned entities": f"{self.aligned_entities * 100}%",
        }

    @classmethod
    def split_train(cls, train, n_part, id_set, seed=42):
        """
        Split train into n_part. Returns selected part and excluded triples.
        """
        splitted_train = []

        train = copy.deepcopy(train)

        random.Random(seed).shuffle(train)

        excluded_triples = []

        for i, frame in enumerate(np.array_split(train, n_part)):

            if i in id_set:
                splitted_train += cls.format_triples(frame)
            else:
                excluded_triples += cls.format_triples(frame)

        return splitted_train, excluded_triples

    @staticmethod
    def format_triples(x):
        return [(h, r, t) for h, r, t in x]

    def corrupt_entities(self, entities, seed):
        n_entities = len(entities)
        n_entities_to_corrupt = round(n_entities * (1 - self.aligned_entities))
        rng = np.random.RandomState(seed)
        entities_id_corrupt = rng.choice(range(n_entities), n_entities_to_corrupt, replace=False)

        e_prime = {value: key for key, value in entities.items()}
        for id_e in entities_id_corrupt:
            e = e_prime[id_e]
            entities.pop(e)
            entities[f"{e}_{self.id_set}_{self.n_part}"] = id_e
        entities = {k: v for k, v in sorted(entities.items(), key=lambda item: item[1])}
        return entities
