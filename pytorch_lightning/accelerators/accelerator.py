# Copyright The PyTorch Lightning team.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from abc import abstractmethod
from typing import Any, Dict, Optional, Union

import torch
from torch.nn import Module

import pytorch_lightning as pl
from pytorch_lightning.plugins.precision import PrecisionPlugin
from pytorch_lightning.plugins.training_type import TrainingTypePlugin


class Accelerator:
    """The Accelerator Base Class. An Accelerator is meant to deal with one type of Hardware.

    Currently there are accelerators for:

    - CPU
    - GPU
    - TPU
    - IPU

    Each Accelerator gets two plugins upon initialization:
    One to handle differences from the training routine and one to handle different precisions.
    """

    def __init__(self, precision_plugin: Optional[PrecisionPlugin], training_type_plugin: TrainingTypePlugin) -> None:
        """
        Args:
            precision_plugin: the plugin to handle precision-specific parts

                .. deprecated::
                    The ``precision_plugin`` parameter has been deprecated and will be removed soon.
                    Pass the precision plugin as a parameter to the ``TrainingTypePlugin`` instead.

            training_type_plugin: the plugin to handle different training routines
        """

        self.training_type_plugin = training_type_plugin

        if precision_plugin is not None:
            self.training_type_plugin._precision_plugin = precision_plugin

    def setup_environment(self) -> None:
        """Setup any processes or distributed connections.

        This is called before the LightningModule/DataModule setup hook which allows the user to access the accelerator
        environment before setup is complete.
        """
        self.training_type_plugin.setup_environment()

    def setup(self, trainer: "pl.Trainer") -> None:
        """Setup plugins for the trainer fit and creates optimizers.

        Args:
            trainer: the trainer instance
        """
        self.training_type_plugin.setup(trainer)

    @property
    def model(self) -> Module:
        """Returns the model.

        This can also be a wrapped LightningModule. For retrieving the pure LightningModule use
        :attr:`Accelerator.lightning_module`
        """
        return self.training_type_plugin.model

    @model.setter
    def model(self, new_model: Module) -> None:
        self.training_type_plugin.model = new_model

    @property
    def lightning_module(self) -> "pl.LightningModule":
        """Returns the pure LightningModule.

        To get the potentially wrapped model use :attr:`Accelerator.model`
        """
        return self.training_type_plugin.lightning_module

    @property
    def root_device(self) -> torch.device:
        """Returns the root device."""
        return self.training_type_plugin.root_device

    def teardown(self) -> None:
        """This method is called to teardown the training process.

        It is the right place to release memory and free other resources.
        """
        self.training_type_plugin.teardown()

    def get_device_stats(self, device: Union[str, torch.device]) -> Dict[str, Any]:
        """Gets stats for a given device.

        Args:
            device: device for which to get stats

        Returns:
            Dictionary of device stats
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def auto_device_count() -> int:
        """Get the devices when set to auto."""
