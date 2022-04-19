import numpy as np
from distributions import Distribution

"""
Author: Samuel Lehmann
Network with him at: https://www.linkedin.com/in/samuellehmann/
"""

# The number of standard deviations that are present within the tolerance range
_DEFAULT_NUM_STDS = 3


class StackupStep:
    """
    Represents a step in the stackup, complete with tolerances as defined by the distributions.

    :param part_name: The part name
    :param description: A string describing the stackup step
    :param distribution: The distribution of the dimension
    :param one_d_stack: If True, the stack is treated as a one dimensional stack. If False, the stack is treated as a
    radial stack
    """

    def __init__(self, distribution: Distribution, part_name: str, description: str = None, one_d_stack=True,
                 is_interface=False):
        self.part_name = part_name
        self.description = description
        self.distribution = distribution
        self.one_d_stack = one_d_stack
        self.lengths = None
        self.is_interface = is_interface
        self.abs_min = distribution.abs_min()
        self.abs_max = distribution.abs_max()
        self.mid_length = distribution.mid_length()
        self.calculate()

    @staticmethod
    def retrieve_distributions():
        return ['norm', 'skew-norm', 'uniform']

    def set_num_samples(self, num_samples):
        self.distribution.num_samples = num_samples

    def to_dict(self):
        return {
            'name': self.part_name,
            'distribution': self.distribution
        }

    def calculate(self, num_samples: int = None, force_radial_stack=False):
        """
        Calculates the distribution.
        :param force_radial_stack: Whether to overwrite the current setting and calculate the stackup as a radial stack
        :param num_samples: The number of samples, optional
        :return: None
        """

        if force_radial_stack:
            self.one_d_stack = False

        if num_samples is not None:
            self.distribution.num_samples = num_samples

        if not self.one_d_stack:
            # Ensure that no negative values are generated
            if self.distribution.lower_lim:
                self.distribution.lower_lim = max(0.0, self.distribution.lower_lim)
            else:
                self.distribution.lower_lim = 0.0

            magnitudes = self.distribution.calculate()
            # in rad
            angles = np.random.random(self.distribution.num_samples) * 2 * np.pi

            self.lengths = [magnitudes * np.cos(angles), magnitudes * np.sin(angles)]

        else:
            self.lengths = self.distribution.calculate()
