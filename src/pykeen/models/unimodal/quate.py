# -*- coding: utf-8 -*-

"""Implementation of the QuatE model."""

from typing import Any, ClassVar, Mapping, Type

import torch
from torch.nn import functional

from ..nbase import ERModel
from ...constants import DEFAULT_EMBEDDING_HPO_EMBEDDING_DIM_RANGE
from ...losses import BCEWithLogitsLoss, Loss
from ...nn.emb import EmbeddingSpecification
from ...nn.init import init_quaternions
from ...nn.modules import QuatEInteraction
from ...regularizers import LpRegularizer, Regularizer
from ...typing import Constrainer, Hint, Initializer

__all__ = [
    'QuatE',
]


def quaternion_normalizer(x: torch.FloatTensor) -> torch.FloatTensor:
    r"""
    Normalize the length of relation vectors, if the forward constraint has not been applied yet.

    Absolute value of a quaternion

    .. math::

        |a + bi + cj + dk| = \sqrt{a^2 + b^2 + c^2 + d^2}

    L2 norm of quaternion vector:

    .. math::
        \|x\|^2 = \sum_{i=1}^d |x_i|^2
                 = \sum_{i=1}^d (x_i.re^2 + x_i.im_1^2 + x_i.im_2^2 + x_i.im_3^2)
    :param x:
        The vector.

    :return:
        The normalized vector.
    """
    # Normalize relation embeddings
    shape = x.shape
    x = x.view(*shape[:-1], -1, 4)
    x = functional.normalize(x, p=2, dim=-1)
    return x.view(*shape)


class QuatE(ERModel):
    r"""An implementation of QuatE from [zhang2019]_.

    QuatE uses hypercomplex valued representations for the
    entities and relations. Entities and relations are represented as vectors
    $\textbf{e}_i, \textbf{r}_i \in \mathbb{H}^d$, and the plausibility score is computed using the
    quaternion inner product.

    .. seealso ::

        Official implementation: https://github.com/cheungdaven/QuatE/blob/master/models/QuatE.py
    ---
    citation:
        author: Zhang
        year: 2019
        link: https://arxiv.org/abs/1904.10281
        github: cheungdaven/quate
    """

    #: The default strategy for optimizing the model's hyper-parameters
    hpo_default: ClassVar[Mapping[str, Any]] = dict(
        embedding_dim=DEFAULT_EMBEDDING_HPO_EMBEDDING_DIM_RANGE,
    )
    #: The default loss function class
    loss_default: ClassVar[Type[Loss]] = BCEWithLogitsLoss
    #: The default parameters for the default loss function class
    loss_default_kwargs: ClassVar[Mapping[str, Any]] = dict(reduction='mean')
    #: The regularizer used by [zhang2019]_ for QuatE.
    regularizer_default: ClassVar[Type[Regularizer]] = LpRegularizer
    #: The LP settings used by [zhang2019]_ for QuatE.
    regularizer_default_kwargs: ClassVar[Mapping[str, Any]] = dict(
        weight=0.0025,
        p=3.0,
        normalize=True,
    )

    def __init__(
        self,
        *,
        embedding_dim: int = 100,
        entity_initializer: Hint[Initializer] = init_quaternions,
        relation_initializer: Hint[Initializer] = init_quaternions,
        relation_constrainer: Hint[Constrainer] = quaternion_normalizer,
        **kwargs,
    ) -> None:
        """Initialize QuatE.

        :param embedding_dim:
            The embedding dimensionality of the entity embeddings.

            .. note ::
                The number of parameter per entity is `4 * embedding_dim`, since quaternion are used.

        :param entity_initializer:
            The initializer to use for the entity embeddings.
        :param relation_initializer:
            The initializer to use for the relation embeddings.
        :param relation_constrainer:
            The constrainer to use for the relation embeddings.
        :param kwargs:
            Additional keyword based arguments passed to :class:`pykeen.models.ERModel`. Must not contain
            "interaction", "entity_representations", or "relation_representations".
        """
        super().__init__(
            interaction=QuatEInteraction,
            entity_representations=EmbeddingSpecification(
                embedding_dim=4 * embedding_dim,
                initializer=entity_initializer,
                dtype=torch.float,
            ),
            relation_representations=EmbeddingSpecification(
                embedding_dim=4 * embedding_dim,
                initializer=relation_initializer,
                constrainer=relation_constrainer,
                dtype=torch.float,
            ),
            **kwargs,
        )
