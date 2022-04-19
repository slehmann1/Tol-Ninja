import datetime
import numpy as np
import reportlab
import stack_manager
from stack_manager import StackManager
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Image, Frame, Spacer, BaseDocTemplate, PageTemplate, NextPageTemplate, PageBreak, \
    Paragraph, Table, TableStyle

"""
Author: Samuel Lehmann
Network with him at: https://www.linkedin.com/in/samuellehmann/
"""

_DECIMAL_PLACES = 2

# Styles for fonts
# Normal text style
_STYLE_N = getSampleStyleSheet()['Normal']
_STYLE_N.fontName = "Helvetica"
_STYLE_N.alignment = 1  # Center the text

# Main header style
_STYLE_H = getSampleStyleSheet()['Heading1']
_STYLE_H.fontName = "Helvetica"

# Subheading style
_STYLE_H2 = getSampleStyleSheet()['Heading1']
_STYLE_H2.fontName = "Helvetica-bold"
_STYLE_H2.fontSize = 12

# Table Header style
_STYLE_TABLE_H = getSampleStyleSheet()["Normal"]
_STYLE_TABLE_H.alignment = 1  # Center the text
_STYLE_TABLE_H.textColor = colors.white
_STYLE_TABLE_H.fontName = "Helvetica-bold"

_HORIZONTAL_MARGIN = 25.4 * mm
_VERTICAL_MARGIN = 25.4 * mm
WIDTH = 215.9 * mm - 2 * _HORIZONTAL_MARGIN
HEIGHT = 279.4 * mm - 2 * _VERTICAL_MARGIN


class ReportGenerator(object):

    def __init__(self, stack_manager: StackManager, title: str, author: str, revision: str):
        self.stack_manager = stack_manager
        self.title = title
        self.author = author
        self.revision = revision

    def create_report(self, file_path: str, summary_image_list):
        """
        Generate a report which can be saved as a pdf
        :param file_path: The path and name of the file
        :param summary_image_list: Images that should be included in the report as a summary of the stack
        :return: A document template
        """

        doc = BaseDocTemplate(file_path, pagesize=reportlab.lib.pagesizes.letter)

        # Create the page templates
        first_page_table_frame = Frame(_HORIZONTAL_MARGIN, _VERTICAL_MARGIN, WIDTH, HEIGHT - 10 * mm, id='small_table')
        later_pages_table_frame = Frame(_HORIZONTAL_MARGIN, _VERTICAL_MARGIN, WIDTH, HEIGHT, id='large_table')
        first_page = PageTemplate(id='FirstPage', frames=[first_page_table_frame], onPage=self._on_first_page)
        later_pages = PageTemplate(id='LaterPages', frames=[later_pages_table_frame], onPage=self._add_default_info)

        doc.addPageTemplates([first_page, later_pages])

        story = [NextPageTemplate(['*', 'LaterPages']), Paragraph("Overall Parameters", _STYLE_H2)]

        # The parameters table
        param_table = Table(self._generate_oal_params(), colWidths=[55.03333 * mm] * 3)
        param_table.setStyle(TableStyle([('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                                         ('BOX', (0, 0), (-1, -1), 1, colors.black),
                                         ('FONT', (0, 0), (-1, -1), 'Helvetica', 12),
                                         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                         ('BACKGROUND', (0, 0), (-1, 0), colors.black),
                                         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                         ('TEXTCOLOR', (0, 0), (-1, 0), colors.white)
                                         ]))
        story.append(param_table)
        story.append(Spacer(10, 10))

        # The results table
        results_table = Table(self._generate_results_params(), colWidths=(50 * mm, 32.55 * mm, 50 * mm, 32.55 * mm))
        results_table.setStyle(TableStyle([
            ('SPAN', (0, 0), (3, 0)),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 12),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ]))
        story.append(results_table)
        story.append(Spacer(10, 10))

        # The stackup inputs table
        stackup_table = Table(self._generate_stackup_inputs_params(),
                              colWidths=(27.7 * mm, 27.7 * mm, 27.7 * mm, 15 * mm, 22 * mm, 15 * mm, 15 * mm, 15 * mm))
        stackup_table.setStyle(TableStyle([
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ]))
        story.append(stackup_table)
        story.append(Spacer(10, 10))

        story.append(PageBreak())

        # Figures
        story.append(Paragraph("Overall Figures", _STYLE_H2))
        if self.stack_manager.further_image_paths:
            for image_path in self.stack_manager.further_image_paths:
                image = Image(image_path)

                height = image.drawHeight / (image.drawWidth / WIDTH)
                image_flowable = Image(image_path, width=WIDTH, height=height)
                story.append(image_flowable)
                story.append(Spacer(10, 10))

        # Add summary images
        for image in summary_image_list:
            height = Image(image).drawHeight / (Image(image).drawWidth / WIDTH)
            image_flowable = Image(image, width=WIDTH, height=height)
            story.append(image_flowable)
            story.append(Spacer(10, 10))

        story.append(PageBreak())
        story.append(Paragraph("Detailed Stackup Step Information", _STYLE_H2))

        # Add images and tables for each stackup step
        for stackup_step in self.stack_manager.stackup_steps:
            stackup_table = Table(self._generate_stackup_step_params(stackup_step),
                                  colWidths=(50 * mm, 32.55 * mm, 50 * mm, 32.55 * mm))
            stackup_table.setStyle(TableStyle([
                ('SPAN', (0, 0), (3, 0)),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('FONT', (0, 0), (-1, -1), 'Helvetica', 12),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.black),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ]))
            story.append(stackup_table)
            story.append(Spacer(10, 10))

            height = Image(stackup_step.image).drawHeight / (Image(stackup_step.image).drawWidth / WIDTH)
            image_flowable = Image(stackup_step.image, width=WIDTH, height=height)
            story.append(image_flowable)

            story.append(Spacer(10, 10))

        doc.build(story)

        return doc

    def _on_first_page(self, canvas, doc):
        """
        Sets up information for the first page of the document
        :param canvas:
        :param doc:
        :return:
        """
        canvas.saveState()
        # Add default info
        self._add_default_info(canvas, doc)

        title = Paragraph("Tolerance Stack-up Report: " + self.title, _STYLE_H)
        title.wrap(WIDTH, HEIGHT)
        title.drawOn(canvas, _HORIZONTAL_MARGIN, HEIGHT + _VERTICAL_MARGIN)
        subtitle = Paragraph(
            f"Revision: {self.revision},  Author: {self.author},   Date: {datetime.date.today().strftime('%Y-%m-%d')}",
            _STYLE_H2)
        subtitle.wrap(WIDTH, HEIGHT)
        subtitle.drawOn(canvas, _HORIZONTAL_MARGIN, HEIGHT + _VERTICAL_MARGIN - 20)
        canvas.restoreState()

    def _add_default_info(self, canvas, doc):
        """
        Adds items to every page of the document
        :param canvas:
        :param doc:
        :return:
        """

        canvas.saveState()
        footer_style = _STYLE_N
        footer_style.alignment = 1
        footer_style.textColor = colors.darkgrey

        footer = Paragraph(
            f'Report created using Tol Ninja: An open source tolerance stackup software (ADD GITHUB LINK) <br />'

            f'<link href="' + 'https://www.linkedin.com/in/SamuelLehmann/' + '">' +
            "<u>Network with the developer</u>" + '</link><br />' +

            f'<link href="' + 'https://www.buymeacoffee.com/SamuelLehmann' + '">' +
            "<u>Or maybe even tip them a coffee</u>" + '</link>',

            footer_style)

        footer.wrap(WIDTH, HEIGHT)
        footer.drawOn(canvas, _HORIZONTAL_MARGIN, _VERTICAL_MARGIN / 3)

        canvas.restoreState()
        _STYLE_N.textColor = colors.black

    def _generate_oal_params(self):
        """
        Generates overall parameters for display in the overall parameters table
        :return: A list of strings
        """
        oal_params = ["", "", ""]
        if self.stack_manager.one_d_stack:
            oal_params[0] = "One Dimensional Stackup"
        else:
            oal_params[0] = "Radial Stackup"

        if self.stack_manager.oal_lsl:
            oal_params[1] = str(self.stack_manager.oal_lsl)
        else:
            oal_params[1] = "-"

        if self.stack_manager.oal_usl:
            oal_params[2] = str(self.stack_manager.oal_usl)
        else:
            oal_params[2] = "-"

        return [_str_to_paragraph(["Stackup Type", "Lower Specification Limit", "Upper Specification Limit"],
                                  _STYLE_TABLE_H), _str_to_paragraph(oal_params, _STYLE_N)]

    def _generate_stackup_step_params(self, stackup_step):
        """
        Creates parameters to be used in the table for each individual stackup step
        :param stackup_step:The stackup step to create parameters for
        :return:a list of parameters that can be provided to the table
        """
        stackup_step_params = [[f"Overview for {stackup_step.part_name}, {stackup_step.description}", "", "", ""]]
        stackup_step_params = _str_to_paragraph(stackup_step_params, _STYLE_TABLE_H)

        table_params = []
        if self.stack_manager.one_d_stack:

            table_params.append(
                ["Mean:", _strval(stackup_step.lengths.mean()), "Median:", _strval(np.median(stackup_step.lengths))])
            table_params.append(["Min:", _strval(min(stackup_step.lengths)), "Max:", _strval(max(stackup_step.lengths))])
        else:
            magnitudes = stack_manager.lengths_to_magnitudes(stackup_step.lengths)

            table_params.append(
                ["Mean:", _strval(magnitudes.mean()), "Median:", _strval(np.median(magnitudes))])
            table_params.append(["Min:", _strval(min(magnitudes)), "Max:", _strval(max(magnitudes))])

        for table_param in table_params:
            stackup_step_params.append(_str_to_paragraph(table_param, _STYLE_N))
        return stackup_step_params

    def _generate_results_params(self):
        """
        Creates parameters to be used in the table for overall results summarizing the stackup
        :return:a list of parameters that can be provided to the table
        """
        results_params = [["Overall Stackup Results", "", "", ""]]
        results_params = _str_to_paragraph(results_params, _STYLE_TABLE_H)

        summary = self.stack_manager.summary_data
        table_params = []
        table_params.append(["Mean:", _strval(summary.mean), "Median:", _strval(summary.median)])
        table_params.append(["Minimum:", _strval(summary.min), "Maximum:", _strval(summary.max)])
        table_params.append(["Standard Deviation:", _strval(summary.std), "CPK:", _strval(summary.cpk)])
        table_params.append(["Number of Samples:", _strval(summary.samples),
                             "Absolute Limits:", _strval(summary.target_limits)])
        table_params.append(["Percent Below Limit:", f"{_strval(summary.percent_below_lsl)}%",
                             "Percent Above Limit:", f"{_strval(summary.percent_above_usl)}%"])
        table_params.append(["Percent Within Limits:", f"{_strval(summary.percent_ok)}%",
                             "Percent Outside Limits:", f"{_strval(summary.percent_nok)}%"])

        for table_param in table_params:
            results_params.append(_str_to_paragraph(table_param, _STYLE_N))
        return results_params

    def _generate_stackup_inputs_params(self):
        """
        Creates parameters to be used in the table that identifies the inputs for each stackup step
        :return:a list of parameters that can be provided to the table
        """
        stackup_params = [["Part", "Description", "Distribution Type", "Mean", "Standard Deviation", "Skew",
                           "Lower Limit", "Upper Limit"]]
        stackup_params = _str_to_paragraph(stackup_params, _STYLE_TABLE_H)

        table_params = []
        for stackup_step in self.stack_manager.stackup_steps:
            table_params.append([stackup_step.part_name, stackup_step.description,
                                 stackup_step.distribution.name,
                                 _strval(stackup_step.distribution.mean),
                                 _strval(stackup_step.distribution.std),
                                 _strval(stackup_step.distribution.skew),
                                 _strval(stackup_step.distribution.lower_lim),
                                 _strval(stackup_step.distribution.upper_lim)])

        for table_param in table_params:
            stackup_params.append(_str_to_paragraph(table_param, _STYLE_N))

        return stackup_params


def _line_to_paragraph(str_list, style):
    """
    Converts a 1D list of strings to an equivalent list of paragraph entries with the given style
    :param str_list: The string list to create paragraphs from
    :param style: The style to be applied to each string
    :return: A list of paragraphs
    """
    paragraph_list = []
    for string in str_list:
        paragraph_list.append((Paragraph(string, style=style)))

    return paragraph_list


def _str_to_paragraph(str_list, style):
    """
    Converts a multi-dimensional list of strings to an equivalent list of paragraph entries with the given style
    :param str_list: The string list to create paragraphs from
    :param style: The style to be applied to each string
    :return: A list of paragraphs
    """
    if isinstance(str_list[0], str):
        return _line_to_paragraph(str_list, style)
    else:

        return_val = []
        for sub_list in str_list:
            return_val.append(_str_to_paragraph(sub_list, style))
        return return_val


def _strval(value):
    """
    Returns a string equivalent of the given float value rounded to the correct number of decimal places
    :param value: The value to get a string for
    :return: A string representation of the value. If the value is none, it returns "-"
    """
    if value is None:
        return "-"
    # This does not handle lists that aren't 1d
    if isinstance(value, list):
        string = "("
        for i in enumerate(value):
            if i[1] is None:
                return "-"
            string += str(round(i[1], _DECIMAL_PLACES))
            if i[0] < len(value):
                string += ", "
        string += ")"
        return string
    return str(round(value, _DECIMAL_PLACES))
