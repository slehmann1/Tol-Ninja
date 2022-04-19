import numpy as np
from matplotlib import pyplot as plt
import stack_manager

"""
Author: Samuel Lehmann
Network with him at: https://www.linkedin.com/in/samuellehmann/
"""

HISTOGRAM_BINS = 50
LIMIT_TEXT_SPACING = 0.1


def arrow_diagram(axs, stackup_steps, min_target_length=None, max_target_length=None, display_absolute_range=True):
    """
    Creates an arrow diagram for the given stackup steps
    :param axs: The axes the arrow diagram should be created on
    :param stackup_steps: The list of stackup steps to create the arrow diagram for
    :param min_target_length: Used to create the "target zone"
    :param max_target_length: Used to create the "target zone"
    :param display_absolute_range: Whether the absolute range zone should be displayed
    :return:
    """

    axs.axvline(0, label='Datum', alpha=0.6)
    if min_target_length is not None and max_target_length is not None:
        axs.axvspan(min_target_length, max_target_length, color='green', zorder=-1, label='Target', alpha=0.3)

    abs_max = 0.0
    abs_min = 0.0
    all_abs_calculated = True

    head_width = len(stackup_steps)/25

    # draw arrows
    last_step_x = 0
    labels = []

    for stackup_step in enumerate(stackup_steps):

        if stackup_step[1].mid_length > 0:
            colour_string = "Green"
        else:
            colour_string = "Red"

        if not stackup_step[1].abs_max or not stackup_step[1].abs_min:
            all_abs_calculated = False
        else:
            abs_max += stackup_step[1].abs_max
            abs_min += stackup_step[1].abs_min

        axs.arrow(y=stackup_step[0], dy=0, x=last_step_x, dx=stackup_step[1].mid_length,
                  width=head_width / 3,
                  length_includes_head=True, head_width=head_width, color=colour_string)

        last_step_x = last_step_x + stackup_step[1].mid_length

        label = stackup_step[1].part_name
        if stackup_step[1].description:
            label += ", " + stackup_step[1].description
        labels.append(label)

    if display_absolute_range and all_abs_calculated:
        axs.axvspan(abs_min, abs_max, color='grey', zorder=-1, label='Specification Limits', alpha=0.3)

    axs.set_yticks(range(len(stackup_steps)))
    axs.set_yticklabels(labels, fontsize=8)
    axs.invert_yaxis()
    axs.set_title('Stackup Arrow Diagram')
    a, _ = axs.get_legend_handles_labels()

    # Only create a legend if there are valid entries
    if a:
        axs.legend(bbox_to_anchor=(0.8, 1), loc="upper left")
    return axs


def histogram(axs, lengths, length_bounds=None, abs_bounds=None, title_prefix="Histogram Of Overall Distribution"):
    """
    Generates a histogram for the given lengths values
    :param axs: The axes the arrow diagram should be created on
    :param lengths: A numpy array of lengths, for which the histogram should be made
    :param length_bounds: The minimum and maximum acceptable length in a tuple. Can be left as None.
    Used to show boundaries.
    :param abs_bounds: Used to create the "target zone". Minimum and maximum in a tuple. Can be left as None.
    :param title_prefix: Graph is given the name f'{title_prefix}, {len(lengths)} Samples'
    :return:
    """

    # Convert the axis from polar coordinates
    fig = axs.get_figure()
    axs.remove()
    axs = fig.add_subplot(1, 1, 1)

    axs.cla()
    axs.hist(lengths, histtype='step', bins=HISTOGRAM_BINS, zorder=3, color='white')
    axs.set_title(f'{title_prefix}, {len(lengths)} Samples')

    if abs_bounds is not None and abs_bounds[0] is not None and abs_bounds[1] is not None:
        axs.axvspan(abs_bounds[0], abs_bounds[1], color='grey', zorder=1, label='Absolute Range', alpha=0.3)
        axs.axvline(abs_bounds[0], color='grey', zorder=2, linestyle='--')
        axs.axvline(abs_bounds[1], color='grey', zorder=2, linestyle='--')

    if length_bounds is not None and length_bounds[0] is not None and length_bounds[1] is not None:
        axs.axvspan(length_bounds[0], length_bounds[1], color='green',
                    zorder=-1, label="Within Specification Limits", alpha=0.3)

    x0, x1 = axs.get_xlim()
    y0, y1 = axs.get_ylim()

    if length_bounds is not None and length_bounds[1] is not None:
        out_range = [i for i in lengths if i > length_bounds[1]]

        if len(out_range) > 0:
            out_range_percent = 100.0 * len(out_range) / len(lengths)
            axs.axvspan(length_bounds[1], x1, color='red', zorder=1, alpha=0.1)
            axs.axvline(length_bounds[1], color='red', zorder=2, linestyle='--')
            axs.text(x=length_bounds[1] + LIMIT_TEXT_SPACING, y=((y1 - y0) * 0.85),
                     s=f'{out_range_percent:.001f}% Above\nMaximum',
                     color='red', horizontalalignment='left')

    if length_bounds is not None and length_bounds[0] is not None:
        out_range = [i for i in lengths if i < length_bounds[0]]
        if len(out_range) > 0:
            out_range_percent = 100.0 * len(out_range) / len(lengths)
            axs.axvspan(x0, length_bounds[0], color='red', zorder=1, alpha=0.1, label="Outside Specification Limits", )
            axs.axvline(length_bounds[0], color='red', zorder=2, linestyle='--')
            axs.text(x=length_bounds[0] - LIMIT_TEXT_SPACING, y=((y1 - y0) * 0.85),
                     s=f'{out_range_percent:.001f}% Below\nMinimum',
                     color='red', horizontalalignment='right')

    # Set the x limits back to what they were before the "fail range" reset them
    axs.set_xlim([x0, x1])
    axs.set_xlim([x0, x1])

    axs.set_xlabel("Dimension")
    axs.set_ylabel("Frequency")

    # Only create a legend if there are valid entries
    a, _ = axs.get_legend_handles_labels()
    if a:
        axs.legend(bbox_to_anchor=(0, 1), loc="upper left")
    return axs


def radial_diagram(axs, lengths, length_bounds=None):
    """
    Generates a radial diagram for the given lengths values
    :param axs: The axes the arrow diagram should be created on
    :param lengths: A numpy array of lengths, for which the histogram should be made
    :param length_bounds: The minimum and maximum acceptable length in a tuple. Can be left as None.
    Used to show boundaries.
    :return:
    """

    # Base the alpha off of the number of points that are used
    alpha = 5000 / len(lengths[0])
    alpha = alpha if alpha < 1.0 else 1.0
    alpha = alpha if alpha > 0.1 else 0.1

    magnitudes = stack_manager.lengths_to_magnitudes(lengths)
    np.random.shuffle(magnitudes)
    thetas = [np.arctan(lengths[1], lengths[0])]

    thetas = [theta * 360.0 / 2.0 / np.pi for theta in thetas]

    # Convert the axis to polar coordinates
    fig = axs.get_figure()
    axs.remove()
    axs = fig.add_subplot(1, 1, 1, projection="polar")
    axs.scatter(thetas, magnitudes, label='Samples', color="grey", alpha=alpha)

    x0, x1 = axs.get_xlim()
    y0, y1 = axs.get_ylim()

    if length_bounds is not None and length_bounds is not None:
        # Create the outer red boundaries
        theta = np.linspace(0., 2. * np.pi, 80, endpoint=True)
        axs.fill_between(theta, length_bounds, max(x0, x1, y0, y1), color="red", alpha=0.1, zorder=1,
                         label="Outside Specification Limits")

        axs.add_patch(
            plt.Circle((0, 0), length_bounds, color="green", alpha=0.1, zorder=1, label="Within Specification Limits",
                       transform=axs.transData._b, ))

    # Set the x limits back to what they were before the "fail range" reset them
    axs.set_xlim([x0, x1])
    axs.set_ylim([0.0, y1])

    # Only create a legend if there are valid entries
    a, _ = axs.get_legend_handles_labels()
    if a:
        axs.legend(bbox_to_anchor=(-0.4, 1.1), loc="upper left")
    return axs
