import pathlib

from ..utils import read_csv, read_csv_classification, read_json
from .dataset import Dataset

__all__ = ["Nell995"]


class Nell995(Dataset):
    """Nell995 dataset.

    Nell995 aim to iterate over the associated dataset. It provide positive samples, corresponding
    weights and the mode (head batch / tail batch)

    Parameters:
        batch_size (int): Size of the batch.
        classification (bool): Must be set to True when using ConvE model to optimize BCELoss.
        shuffle (bool): Whether to shuffle the dataset or not.
        pre_compute (bool): Pre-compute parameters such as weights when using translationnal model
            (TransE, DistMult, RotatE, pRotatE, ComplEx). When using ConvE, pre-compute target
            matrix. When pre_compute is set to True, the model training is faster but it needs more
            memory.
        num_workers (int): Number of workers dedicated to iterate on the dataset.
        seed (int): Random state.

    Attributes:
        train (list): Training set.
        valid (list): Validation set.
        test (list): Testing set.
        entities (dict): Index of entities.
        relations (dict): Index of relations.
        n_entity (int): Number of entities.
        n_relation (int): Number of relations.

    Example:

        >>> from mkb import datasets

        >>> dataset = datasets.Nell995(batch_size=1, shuffle=False, pre_compute=False, seed=42)

        >>> dataset
        Nell995 dataset
            Batch size         1
            Entities           75492
            Relations          200
            Shuffle            False
            Train triples      149678
            Validation triples 543
            Test triples       3992

        >>> assert len(dataset.classification_valid['X']) == len(dataset.classification_valid['y'])
        >>> assert len(dataset.classification_test['X']) == len(dataset.classification_test['y'])

        >>> assert len(dataset.classification_valid['X']) == len(dataset.valid) * 2
        >>> assert len(dataset.classification_test['X']) == len(dataset.test) * 2

    References:
        1. [An Open-source Framework for Knowledge Embedding implemented with PyTorch.](https://github.com/thunlp/OpenKE)

    """

    def __init__(
        self,
        batch_size,
        classification=False,
        shuffle=True,
        pre_compute=True,
        num_workers=1,
        seed=None,
    ):

        self.filename = "nell995"

        path = pathlib.Path(__file__).parent.joinpath(self.filename)

        super().__init__(
            train=read_csv(file_path=f"{path}/train.csv"),
            valid=read_csv(file_path=f"{path}/valid.csv"),
            test=read_csv(file_path=f"{path}/test.csv"),
            entities=read_json(f"{path}/entities.json"),
            relations=read_json(f"{path}/relations.json"),
            batch_size=batch_size,
            shuffle=shuffle,
            classification=classification,
            pre_compute=pre_compute,
            num_workers=num_workers,
            seed=seed,
            classification_valid=read_csv_classification(f"{path}/classification_valid.csv"),
            classification_test=read_csv_classification(f"{path}/classification_test.csv"),
        )
