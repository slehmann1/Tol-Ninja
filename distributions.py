import numpy as np
from scipy.stats import skewnorm
from abc import ABC, abstractmethod

"""
Author: Samuel Lehmann
Network with him at: https://www.linkedin.com/in/samuellehmann/
"""

# The maximum number of iterations to be run for cutoff distributions
_MAX_ITERATIONS = 100
# The default number of samples if no other value is specified
DEFAULT_SAMPLES = 50000


class Distribution(ABC):
    """
    An abstract class that parents all distributions
    """

    def __init__(self, name: str, num_samples: int = DEFAULT_SAMPLES, mid_length=None, lower_lim=None, upper_lim=None):
        """
        An abstract class that parents all distributions
        :param num_samples: The number of samples. Defaults to DEFAULT SAMPLES
        :param mid_length: The mid_point value for all distributions
        :param lower_lim: A cutoff at a lower limit, no cutoff applied if no value passed
        :param upper_lim: A cutoff at an upper limit, no cutoff applied if no value passed
        :param name: A string representation of the distribution
        """
        self.num_samples = num_samples
        self.lower_lim = lower_lim
        self.upper_lim = upper_lim
        self.name = name
        self.nominal_value = mid_length
        self.mean = None
        self.std = None
        self.skew = None

    def mid_length(self):
        """
        :return: The distributions medium value
        """
        return self.nominal_value

    @abstractmethod
    def calculate(self):
        """
        Returns a random sampling from the distribution in the form of a numpy array.
        :return: A randomly ordered numpy array of values
        """
        pass

    def abs_max(self):
        """
        The absolute maximum value possible in the distrbibution. May be none if not defined.
        Eg. a normal distribution without a cutoff.
        :return:
        """
        return self.upper_lim

    def abs_min(self):
        """
        The absolute minimum value possible in the distrbibution. May be none if not defined.
        Eg. a normal distribution without a cutoff.
        :return:
        """
        return self.lower_lim


class Normal(Distribution):
    """
    A class for a normal distribution
    """

    def __init__(self, mean: float, std: float, num_samples: int = DEFAULT_SAMPLES, lower_lim=None, upper_lim=None):
        """

        :param mean: The mean value for the distribution
        :param std: The standard deviation for the distribution
        :param num_samples: Optional - the number of samples within the common lengths
        :param lower_lim: A cutoff at a lower limit, no cutoff applied if no value passed
        :param upper_lim: A cutoff at an upper limit, no cutoff applied if no value passed
        """
        super().__init__("Normal", num_samples, mean, lower_lim, upper_lim)
        self.mean = mean
        self.std = std
        self.lower_lim = lower_lim
        self.upper_lim = upper_lim

    def calculate(self):
        """
        Returns a random sampling from the distribution in the form of a numpy array.
        :return: A randomly ordered numpy array of values
        """
        values = np.random.normal(self.mean, self.std, self.num_samples)
        if self.lower_lim or self.upper_lim:
            # remove samples not in range
            if self.lower_lim:
                values = values[values >= self.lower_lim]
            if self.upper_lim:
                values = values[values <= self.upper_lim]

            count = 0
            while len(values) < self.num_samples:
                values = np.append(values, np.random.normal(self.mean, self.std, self.num_samples))
                if self.lower_lim:
                    values = values[values >= self.lower_lim]
                if self.upper_lim:
                    values = values[values <= self.upper_lim]
                count += 1
                if count > _MAX_ITERATIONS:
                    raise ValueError('Number of iterations exceeds the maximum set for cutoff distributions.')

            values = values[:self.num_samples]

        return values


class Uniform(Distribution):
    """
    A class for a uniform distribution
    """

    def __init__(self, nominal: float, tolerance: float, num_samples: int = DEFAULT_SAMPLES):
        """

        :param nominal: The nominal value
        :param tolerance: The bi-directional tolerance of common lengths
        :param num_samples: The number of samples within the common lengths
        """
        super().__init__("Uniform", num_samples, nominal, nominal - tolerance, nominal + tolerance)
        self.nominal = nominal
        self.tolerance = tolerance

    def calculate(self):
        """
        Returns a random sampling from the distribution in the form of a numpy array.
        :return: A randomly ordered numpy array of values
        """
        return np.random.uniform(self.nominal - self.tolerance, self.nominal + self.tolerance, self.num_samples)


class SkewedNormal(Distribution):
    """
    A class for a skewed normal distribution
    """

    def __init__(self, skew: float, mean: float, std: float, num_samples: int = DEFAULT_SAMPLES, lower_lim=None,
                 upper_lim=None):
        """

        :param skew: 0 gives the normal distribution. A negative value will create a left skew whilst a positive
        value will create a right skew.
        :param mean: The mean value of the unskewed normal distribution
        :param std: The standard deviation of the unskewed normal distribution
        :param num_samples: The number of samples within the common lengths
        :param lower_lim: A cutoff at a lower limit, no cutoff applied if no value passed
        :param upper_lim: A cutoff at an upper limit, no cutoff applied if no value passed
        """
        super().__init__("Skewed Normal", num_samples, mean, lower_lim, upper_lim)
        self.skew = skew
        self.mean = mean
        self.std = std
        self.lower_lim = lower_lim
        self.upper_lim = upper_lim

    def calculate(self):
        """
        Returns a random sampling from the distribution in the form of a numpy array.
        :return: A randomly ordered numpy array of values
        """
        values = skewnorm.rvs(self.skew, self.mean, self.std, self.num_samples).astype(np.float64)
        if self.lower_lim or self.upper_lim:
            # remove samples not in range
            if self.lower_lim:
                values = values[values >= self.lower_lim]
            if self.upper_lim:
                values = values[values <= self.upper_lim]

            count = 0
            while len(values) < self.num_samples:
                values = np.append(values,
                                   skewnorm.rvs(self.skew, self.mean, self.std, self.num_samples).astype(np.float64))
                if self.lower_lim:
                    values = values[values >= self.lower_lim]
                if self.upper_lim:
                    values = values[values <= self.upper_lim]
                count += 1
                if count > _MAX_ITERATIONS:
                    raise ValueError('Number of iterations exceeds the maximum set for cutoff distributions.')

            values = values[:self.num_samples]

        return values
