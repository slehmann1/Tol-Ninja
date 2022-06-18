
# Tol Ninja: Tolerance Stackup Analysis Software
Statistical tolerance stackup analysis software based on the Monte Carlo methodology, capable of analyzing complicated 1D and coaxial tolerance chains. 

### Feature Overview
Generate stackup results for both:
#### 1 Dimensional Tolerance Chains
![1D Chain Image](https://raw.githubusercontent.com/slehmann1/Tol-Ninja/main/SupportingInfo/GitHubImages/1D_Stack.png)
#### Radial Tolerance Chains
![Radial Stack Chain](https://raw.githubusercontent.com/slehmann1/Tol-Ninja/main/SupportingInfo/GitHubImages/RadialStack.png)
#### Power
Support for normal, skewed normal, and uniform distributions in a complete or truncated state, with an intuitive interface to setup complicated, multi-part stacks:
![Interface Overview](https://raw.githubusercontent.com/slehmann1/Tol-Ninja/main/SupportingInfo/GitHubImages/Interface.png)
#### Reporting
Generate professional looking reports like [this (1D Stack)](https://github.com/slehmann1/Tol-Ninja/blob/main/SupportingInfo/SampleReports/1D_SampleReport.pdf) or [this (Radial Stack)](https://github.com/slehmann1/Tol-Ninja/blob/main/SupportingInfo/SampleReports/Radial_SampleReport.pdf).

![Reporting Overview](https://raw.githubusercontent.com/slehmann1/Tol-Ninja/main/SupportingInfo/GitHubImages/Report_Overview.PNG)
#### Dependencies
Written in python with the following dependencies:  Numpy, Scipy, Tkinter, QBstyles, MatPlotLib, and ReportLab.


#### Usage Example
Two sample cases are provided. To open them, start the program and press the "load stack" (1) button and navigate to the /SupportingInfo/SampleReports folder. Open one of the two provided pickle files in this folder and the stackup setup section of the user interface will populate with the loaded sample case (2). Pressing the calculate button (3) will complete the monte carlo simulation for the stackup.

![UsageImage](https://raw.githubusercontent.com/slehmann1/Tol-Ninja/main/SupportingInfo/GitHubImages/UsageExample.png)