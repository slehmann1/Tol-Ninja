import math
import numpy as np
from collections import namedtuple
import distributions
import stack_visualizer
import stackup_step

"""
Author: Samuel Lehmann
Network with him at: https://www.linkedin.com/in/samuellehmann/
"""


class StackManager:
    """
        The stackmanager manages and performs analysis on stackups.

        :param name: The name of the stackup
        :param description: A description of the stackup
        :param revision: The revision of the stackup
        :param oal_lsl: The overall lower specification limit
        :param oal_usl: The overall upper specification limit
        :param num_samples: The number of samples to create
        :param one_d_stack: If true, the stack is a 1d stack. If false, it is a radial stack.
        """
    Summary_Data = namedtuple("summary",
                              "target_limits percent_below_lsl percent_above_usl percent_ok "
                              "percent_nok percent_below_cust_lsl percent_above_cust_usl "
                              "percent_cust_ok percent_cust_nok mean median min max samples std cpk")

    def __init__(self, name: str = 'Tolerance Stackup Report', description: str = None, revision: str = "01",
                 oal_lsl: float = None, oal_usl: float = None, one_d_stack=True,
                 num_samples: int = distributions.DEFAULT_SAMPLES):

        self.stackup_steps = []
        self.one_d_stack = one_d_stack
        self.oal_lsl = oal_lsl
        self.oal_usl = oal_usl
        self.name = name
        self.description = description
        self.revision = revision
        self.num_samples = num_samples
        self.summary_data = None
        self.further_image_paths = None
        self.images = None
        self.lengths = None

    def add_part(self, stackup_step: stackup_step.StackupStep):
        """
        Adds a part to the stack path.

        :param stackup_step: An instance of ``Part``
        :return: None
        """
        stackup_step.set_num_samples(self.num_samples)

        self.stackup_steps.append(stackup_step)

    def calculate_stack(self, radial_stack=False):
        """
        Calculates all distributions within the stack
        :param radial_stack: If true, the stack should be calculated as a radial stack
        :return:
        """
        for stackup_step in self.stackup_steps:
            stackup_step.calculate(force_radial_stack=radial_stack)
            if stackup_step.lengths is None:
                raise AttributeError(f"{stackup_step.name} failed to calculate length")

    def create_arrow_diagram(self, axes):
        """
        Creates an arrow diagram
        :param axes: The axes to create the arrow diagram for
        :return: The updated axes
        """
        axes = stack_visualizer.arrow_diagram(axes, self.stackup_steps, self.oal_lsl, self.oal_usl)
        return axes

    def create_oal_diagram(self, axes, lengths=None, radial_stack = False):
        """
        Creates an overall histogram diagram
        :param axes: The axes to create the arrow diagram for
        :return: The updated axes
        """
        if lengths is None:
            lengths = self.lengths
            if lengths is None:
                lengths = self.calc_oal_dist()

        if self:
            if radial_stack or (len(lengths) == 2 and self.stackup_steps[0].distribution.num_samples != 2):
                # This is a radial stack
                axes = stack_visualizer.radial_diagram(axs=axes, lengths=lengths, length_bounds=self.oal_usl)
            else:
                axes = stack_visualizer.histogram(axes, lengths, [self.oal_lsl, self.oal_usl],
                                                  self.get_abs_limits())
        else:
            if radial_stack or (len(lengths) == 2 and self.stackup_steps[0].distribution.num_samples != 2):
                # This is a radial stack
                axes = stack_visualizer.radial_diagram(axs=axes, lengths=lengths)
            else:
                axes = stack_visualizer.histogram(axes, lengths)

        return axes

    def create_magnitude_diagram(self, axes, lengths=None):
        """
        Creates an overall histogram diagram
        :param lengths: The stackup lengths
        :param axes: The axes to create the magnitude diagram for
        :return: The updated axes
        """
        if lengths is None:
            lengths = self.lengths
            if lengths is None:
                lengths = self.calc_oal_dist()

        # Convert lengths to magnitudes
        magnitudes = np.array([np.sqrt(lengths[0] ** 2 + lengths[1] ** 2)])[0]

        if self:
            axes = stack_visualizer.histogram(axes, magnitudes, [0.0, self.oal_usl],
                                              self.get_abs_limits(), title_prefix="Histogram Of Eccentricities")
        else:
            axes = stack_visualizer.histogram(axs=axes, lengths=magnitudes, title_prefix="Histogram Of Eccentricities")

        # Set x axis to start from 0
        _, x1 = axes.get_xlim()
        axes.set_xlim([0.0, x1])
        axes.set_xlabel("Eccentricity")

        return axes

    def calc_oal_dist(self):
        """
        Computes the overall distribution, summing each step in the stackup
        :return: A numpy array of length values
        """
        num_of_steps = len(self.stackup_steps)

        if self.one_d_stack:
            final_lengths = np.zeros(len(self.stackup_steps[0].lengths))
            for i in range(num_of_steps):
                final_lengths += self.stackup_steps[i].lengths
        else:
            final_lengths = [np.zeros(len(self.stackup_steps[0].lengths[0])),
                             np.zeros(len(self.stackup_steps[0].lengths[1]))]
            for i in range(num_of_steps):
                final_lengths[0] += self.stackup_steps[i].lengths[0]
                final_lengths[1] += self.stackup_steps[i].lengths[1]

        self.lengths = final_lengths
        return final_lengths

    def get_abs_limits(self):
        """
        Calculate the absolute limits of the stackup. Returns None if limits cannot be calculated
        :return: None or a tuple of the [Absolute minimum limit, Absolute maximum limit]
        """
        abs_max = 0.0
        abs_min = 0.0
        all_abs_calculated = True

        for stackup_step in self.stackup_steps:
            if not stackup_step.abs_max or not stackup_step.abs_min:
                all_abs_calculated = False
            else:
                abs_max += stackup_step.abs_max
                abs_min += stackup_step.abs_min

        if all_abs_calculated:
            return [abs_min, abs_max]
        else:
            return None

    def add_report_image_paths(self, further_image_paths):
        """
        Adds image paths to the report
        :param further_image_paths: Strings of paths to the locations of the images
        :return: 
        """
        if not self.further_image_paths or len(self.further_image_paths == 0):
            self.further_image_paths = list(further_image_paths)
        else:
            self.further_image_paths.append(further_image_paths)

    def get_summary_data(self, lengths, cust_limits=None):
        """
        Calculated statistics summarizing the tolerance stack
        :param cust_limits: The imposed limits for which percentages above/below should be calculated. Optional
        :param lengths: The calculated tolerance stack to summarize data for
        :return: A Summary_Data named tuple
        """
        specification_limits = [self.oal_lsl, self.oal_usl]

        percent_below_lsl, percent_above_usl, percent_ok, percent_nok, cpk = (None for _ in range(5))

        if not self.one_d_stack:
            # Set LSL to 0
            specification_limits[0] = 0.0

        if specification_limits and specification_limits[0] is not None and specification_limits[1] is not None:
            percent_below_lsl, percent_above_usl, percent_ok, percent_nok = \
                self.determine_summary_percentages(lengths, specification_limits)

        mean = lengths.mean()
        std = np.std(lengths)

        if specification_limits and specification_limits[0] is not None and specification_limits[1] is not None:
            if not self.one_d_stack:
                cpk = get_cpk(specification_limits[0], specification_limits[1], mean, std)
            else:
                cpk = get_cpk(0.0, specification_limits[1], mean, std)

        percent_below_cust_lsl, percent_above_cust_usl, percent_cust_ok, percent_cust_nok = (None for _ in range(4))

        if cust_limits and cust_limits[0] is not None and cust_limits[1] is not None:
            percent_below_cust_lsl, percent_above_cust_usl, percent_cust_ok, percent_cust_nok = \
                self.determine_summary_percentages(lengths, cust_limits)

        self.summary_data = self.Summary_Data(percent_below_lsl=percent_below_lsl,
                                              percent_above_usl=percent_above_usl,
                                              percent_ok=percent_ok,
                                              percent_nok=percent_nok,
                                              percent_below_cust_lsl=percent_below_cust_lsl,
                                              percent_above_cust_usl=percent_above_cust_usl,
                                              percent_cust_ok=percent_cust_ok,
                                              percent_cust_nok=percent_cust_nok, mean=mean, median=np.median(lengths),
                                              min=min(lengths), max=max(lengths), target_limits=specification_limits,
                                              samples=len(lengths),
                                              std=std, cpk=cpk)

        return self.summary_data

    def determine_summary_percentages(self, lengths, limits):
        """
        Calculates percentages within and outside of limits for the get_summary data function
        :param lengths:
        :param limits:
        :return:
        """

        if len(lengths) == 2 and self.stackup_steps[0].num_samples != 2:
            # This is a radial stack, base off of magnitudes
            lengths = [np.sqrt(lengths[0] ** 2 + lengths[1] ** 2)][0]
            percent_below_min = 0.0
        else:
            percent_below_min = [i for i in lengths if i < limits[0]]
            percent_below_min = 100.0 * len(percent_below_min) / len(lengths)

        percent_above_max = [i for i in lengths if i > limits[1]]
        percent_above_max = 100.0 * len(percent_above_max) / len(lengths)

        percent_nok = percent_below_min + percent_above_max
        percent_ok = 100 - percent_above_max - percent_below_min

        return [percent_below_min, percent_above_max, percent_nok, percent_ok]


def get_cpk(lsl, usl, mean, std):
    """
    Returns the CPK for a given process
    :param lsl: Lower specification limit
    :param usl: Upper specification limit
    :param mean:
    :param std: Standard deviation
    :return:
    """
    return min((usl - mean) / 3 / std, (mean - lsl) / 3 / std)


def lengths_to_magnitudes(lengths):
    """
    Converts a 2d Array of lengths into an array of equivalent magnitudes
    :param lengths: Length values where lengths[0] is x and lengths[1] is y
    :return: The magnitudes of the length values
    """
    return np.array([np.sqrt(lengths[0] ** 2 + lengths[1] ** 2)])[0]


def range_for_percentage(percentage, type, lengths):
    """
    Gives the range of values required for a percentage of distribution coverage
    :param percentage: The percentage to be covered
    :param type: "Left", "Right", or Bi-Lateral"
    :param lengths: Precalculated length values
    :return:The range of values. Will be a tuple for a bi-lateral case
    """

    if type == "Left":
        lengths = np.sort(lengths)
        target_count = math.ceil(percentage * len(lengths) / 100)
        return lengths[target_count]

    elif type == "Right":
        lengths = np.sort(lengths)
        target_count = math.ceil(percentage * len(lengths) / 100)
        return lengths[-target_count]

    elif type == "Bi-Lateral":
        lengths = abs(lengths)
        lengths = np.sort(lengths)
        target_count = math.ceil(percentage * len(lengths) / 100)
        return [-lengths[target_count], lengths[target_count]]
